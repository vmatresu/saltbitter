# ADR-008: Stripe for Payment Processing

## Status
Accepted

## Context
The SaltBitter platform offers three subscription tiers (Free, Premium $19.99/mo, Elite $49.99/mo) plus microtransactions (virtual gifts, event tickets). We need a payment processor that supports:
- Recurring subscriptions with automatic billing
- One-time payments (microtransactions)
- Multiple payment methods (cards, Apple Pay, Google Pay)
- PCI DSS compliance (don't store card numbers)
- Webhooks for payment events
- Strong fraud prevention
- Global expansion (EU, UK, CA, AU initially)

### Options Considered

**Option A: Stripe**
- Market leader in SaaS subscriptions
- Best developer experience
- Strong fraud prevention (Radar)
- Comprehensive API and webhooks
- Fee: 2.9% + $0.30 per transaction

**Option B: PayPal**
- High user trust and adoption
- Lower friction (users have existing accounts)
- Fee: 2.9% + $0.30, but higher for international
- Less developer-friendly API
- Limited subscription management features

**Option C: Braintree (PayPal subsidiary)**
- Combines Stripe's API with PayPal's network
- Good international support
- Fee: 2.9% + $0.30
- More complex integration

**Option D: Build own with payment gateway (Authorize.net, etc.)**
- More control over user experience
- Avoid revenue share
- Requires PCI DSS compliance ($50K+ annually)
- Higher development and maintenance cost

## Decision
We will use **Stripe** as our primary payment processor.

## Rationale

### Why Stripe
1. **Developer Experience**: Best-in-class API, extensive documentation, excellent SDKs
2. **Subscription Management**: Native support for trials, upgrades, downgrades, prorations
3. **PCI Compliance**: Stripe handles PCI DSS, we never touch card numbers
4. **Webhooks**: Real-time events for all payment states
5. **Fraud Prevention**: Stripe Radar with machine learning (free on standard fees)
6. **Global Ready**: Supports 135+ currencies, local payment methods
7. **Tax Automation**: Stripe Tax calculates sales tax/VAT automatically
8. **Proven Scale**: Used by Shopify, Lyft, DoorDash, Amazon

### Payment Methods Supported
- Credit/debit cards (Visa, Mastercard, Amex)
- Apple Pay (iOS in-app and web)
- Google Pay (Android in-app and web)
- Bank transfers (ACH in US, SEPA in EU) - lower fees
- Buy Now Pay Later (Klarna, Affirm) - for annual subscriptions

## Implementation Details

### Subscription Flow

```python
# Backend: Create subscription
@router.post("/api/subscriptions")
async def create_subscription(
    tier: Literal["premium", "elite"],
    payment_method_id: str,
    current_user: User = Depends(get_current_user)
):
    # Create Stripe customer if not exists
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": str(current_user.id)}
        )
        await db.update_user_stripe_id(current_user.id, customer.id)
    else:
        customer_id = current_user.stripe_customer_id

    # Attach payment method
    await stripe.PaymentMethod.attach(
        payment_method_id,
        customer=customer_id
    )

    # Set as default payment method
    await stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method_id}
    )

    # Create subscription
    subscription = await stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": TIER_PRICE_IDS[tier]}],  # Stripe price ID
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
        metadata={
            "user_id": str(current_user.id),
            "tier": tier
        }
    )

    # Save to database
    await db.create_subscription(
        user_id=current_user.id,
        tier=tier,
        stripe_subscription_id=subscription.id,
        status="incomplete"
    )

    # Return client secret for 3D Secure
    return {
        "subscription_id": subscription.id,
        "client_secret": subscription.latest_invoice.payment_intent.client_secret
    }
```

### Webhook Handling

```python
# Backend: Handle Stripe webhooks
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event types
    if event.type == "invoice.payment_succeeded":
        await handle_payment_succeeded(event.data.object)

    elif event.type == "invoice.payment_failed":
        await handle_payment_failed(event.data.object)

    elif event.type == "customer.subscription.updated":
        await handle_subscription_updated(event.data.object)

    elif event.type == "customer.subscription.deleted":
        await handle_subscription_canceled(event.data.object)

    return {"status": "success"}

async def handle_payment_succeeded(invoice):
    """Payment succeeded, upgrade user tier."""
    subscription_id = invoice.subscription
    subscription = await db.get_subscription_by_stripe_id(subscription_id)

    # Update subscription status
    await db.update_subscription_status(subscription.id, "active")

    # Upgrade user tier
    await db.update_user_tier(subscription.user_id, subscription.tier)

    # Log for compliance
    await db.create_payment_log(
        user_id=subscription.user_id,
        amount=invoice.amount_paid / 100,  # Convert cents to dollars
        type="subscription",
        stripe_invoice_id=invoice.id,
        status="succeeded"
    )

    # Send confirmation email
    await send_email(
        user_id=subscription.user_id,
        template="payment_success",
        context={"amount": invoice.amount_paid / 100}
    )

async def handle_payment_failed(invoice):
    """Payment failed, notify user and optionally downgrade."""
    subscription_id = invoice.subscription
    subscription = await db.get_subscription_by_stripe_id(subscription_id)

    # Mark subscription as past due
    await db.update_subscription_status(subscription.id, "past_due")

    # Send email notification
    await send_email(
        user_id=subscription.user_id,
        template="payment_failed",
        context={
            "amount": invoice.amount_due / 100,
            "retry_date": invoice.next_payment_attempt
        }
    )

    # Stripe will auto-retry per Smart Retries schedule
    # After 4 failed attempts, subscription will be canceled
```

### Microtransactions (Virtual Gifts, Event Tickets)

```python
@router.post("/api/payments/gift")
async def send_virtual_gift(
    recipient_id: UUID,
    gift_type: str,
    current_user: User = Depends(get_current_user)
):
    gift_price = GIFT_PRICES[gift_type]  # e.g., $4.99

    # Create PaymentIntent
    payment_intent = await stripe.PaymentIntent.create(
        amount=int(gift_price * 100),  # Convert to cents
        currency="usd",
        customer=current_user.stripe_customer_id,
        metadata={
            "type": "virtual_gift",
            "sender_id": str(current_user.id),
            "recipient_id": str(recipient_id),
            "gift_type": gift_type
        },
        description=f"Virtual gift: {gift_type}"
    )

    return {"client_secret": payment_intent.client_secret}

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    # ...

    elif event.type == "payment_intent.succeeded":
        await handle_payment_intent_succeeded(event.data.object)

async def handle_payment_intent_succeeded(payment_intent):
    """One-time payment succeeded."""
    if payment_intent.metadata.get("type") == "virtual_gift":
        # Deliver virtual gift
        await db.create_virtual_gift(
            sender_id=payment_intent.metadata["sender_id"],
            recipient_id=payment_intent.metadata["recipient_id"],
            gift_type=payment_intent.metadata["gift_type"]
        )

        # Notify recipient
        await send_notification(
            payment_intent.metadata["recipient_id"],
            f"You received a {payment_intent.metadata['gift_type']}!"
        )
```

### Subscription Management

```python
# Upgrade/Downgrade
@router.put("/api/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: UUID,
    new_tier: Literal["premium", "elite"],
    current_user: User = Depends(get_current_user)
):
    subscription = await db.get_subscription(subscription_id)

    # Verify ownership
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update Stripe subscription
    stripe_subscription = await stripe.Subscription.retrieve(
        subscription.stripe_subscription_id
    )

    await stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        items=[{
            "id": stripe_subscription.items.data[0].id,
            "price": TIER_PRICE_IDS[new_tier]
        }],
        proration_behavior="create_prorations"  # Immediate change with proration
    )

    # Update database
    await db.update_subscription_tier(subscription.id, new_tier)

    return {"message": "Subscription updated", "new_tier": new_tier}

# Cancel subscription
@router.delete("/api/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: UUID,
    immediately: bool = False,  # Default: cancel at period end
    current_user: User = Depends(get_current_user)
):
    subscription = await db.get_subscription(subscription_id)

    if immediately:
        # Cancel immediately, no refund
        await stripe.Subscription.delete(subscription.stripe_subscription_id)
        await db.update_subscription_status(subscription.id, "canceled")
    else:
        # Cancel at period end (user keeps access until then)
        await stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        await db.update_subscription_status(subscription.id, "canceling")

    return {"message": "Subscription canceled"}
```

## Fraud Prevention

### Stripe Radar
- Automatic fraud detection with machine learning
- Block high-risk payments automatically
- Customizable rules (e.g., block if email domain suspicious)
- 3D Secure (SCA) for EU payments

### Custom Rules
```python
# Require 3D Secure for subscriptions >$20/mo
stripe.Subscription.create(
    customer=customer_id,
    items=[{"price": price_id}],
    payment_settings={
        "payment_method_types": ["card"],
        "payment_method_options": {
            "card": {
                "request_three_d_secure": "automatic"
            }
        }
    }
)
```

## Testing

```python
# Use Stripe test mode cards
TEST_CARDS = {
    "success": "4242424242424242",
    "decline": "4000000000000002",
    "sca_required": "4000002500003155",  # 3D Secure
}

# Test webhooks locally with Stripe CLI
# stripe listen --forward-to localhost:8000/webhooks/stripe
```

## Consequences

### Positive
- **Time to Market**: Full payment system in 2-3 weeks vs. 6+ months custom
- **PCI Compliance**: Stripe handles, saves $50K+ annual compliance costs
- **Fraud Prevention**: Radar prevents ~$2K-5K monthly in fraud losses
- **User Experience**: Smooth checkout, mobile wallets, saved cards
- **Revenue Optimization**: Smart retries recover ~15% of failed payments
- **Global Ready**: Multi-currency, local payment methods
- **Tax Automation**: Stripe Tax handles sales tax/VAT across jurisdictions

### Negative
- **Fees**: 2.9% + $0.30 per transaction (~$6K/month at $20K MRR)
- **Vendor Lock-In**: Migration to another processor is complex
- **Payout Delays**: 2-day rolling basis (7 days initially)
- **Account Risks**: Stripe can freeze accounts for ToS violations

### Mitigation
- Factor fees into pricing ($19.99 → $19.50 after fees)
- Design payment abstractions to allow future multi-processor support
- Maintain sufficient cash runway for payout delays
- Follow Stripe ToS strictly, enable fraud prevention

## Monitoring

```python
# Key metrics
PAYMENT_METRICS = [
    "subscription_conversion_rate",    # Target: >5%
    "payment_success_rate",            # Target: >95%
    "churn_rate",                      # Target: <5% monthly
    "failed_payment_recovery_rate",    # Target: >15%
    "avg_customer_lifetime_value",     # Target: >$200
]

# Alerts
- Payment success rate <92%: Check Stripe status, investigate
- Churn spike >10%: Review pricing, value proposition
- Webhook failures: Investigate endpoint reliability
```

## Related Decisions
- ADR-002: PostgreSQL (stores subscription records)
- ADR-006: JWT authentication (identifies users for payments)

## References
- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Radar Fraud Prevention](https://stripe.com/docs/radar)
- [SCA / 3D Secure](https://stripe.com/docs/strong-customer-authentication)

## Date
2025-11-17

## Authors
- Architect Agent
- Finance Team
- Product Owner
