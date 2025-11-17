# Premium Tiers & Ethical Monetization Strategy

## Core Philosophy

> **"Premium unlocks MORE opportunities, not BETTER matches."**
>
> Free users receive the same quality matches as paid users. Premium removes friction and provides coaching tools, but never creates artificial scarcity or "pay-to-win" dynamics.

---

## Subscription Tier Comparison

### Feature Matrix

| Feature | Free | Premium ($12.99/mo) | Elite ($29.99/mo) |
|---------|------|---------------------|-------------------|
| **CORE MATCHING** | | | |
| Attachment assessment | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| Daily match quality | ✅ Same algorithm | ✅ Same algorithm | ✅ Same algorithm |
| Daily match quantity | 🎯 5-10 matches | 🎯 30-50 matches | 🎯 Unlimited browsing |
| Match filters (basic) | ✅ Age, distance, gender | ✅ Age, distance, gender | ✅ Age, distance, gender |
| Match filters (advanced) | ❌ | ✅ Attachment style, interests, values | ✅ All filters + custom |
| **AI FEATURES** | | | |
| AI Practice Companions | ✅ 3 sessions/week | ✅ Unlimited | ✅ Unlimited + priority |
| AI-generated icebreakers | 💰 $2 each | ✅ 10/day included | ✅ Unlimited |
| AI Communication Coaching | ❌ | ❌ | ✅ Real-time analysis |
| Post-date reflection tools | ❌ | ✅ Basic | ✅ Advanced + trends |
| **COMMUNICATION** | | | |
| Send messages | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| See who liked you | ❌ | ✅ Full list | ✅ Full list + timestamps |
| Read receipts | ❌ | ✅ | ✅ |
| Message priority | ❌ Standard queue | ✅ Priority delivery | ✅ Highest priority |
| Undo swipes | ❌ | ✅ 5/day | ✅ Unlimited |
| **VISIBILITY** | | | |
| Profile views | 🔒 Blurred | ✅ See all viewers | ✅ See all + insights |
| Profile boost | 💰 $3.99 each | ✅ 1 free/week | ✅ 1 free/day |
| Priority placement | ❌ | ✅ 2x visibility | ✅ 5x visibility |
| **SAFETY & VERIFICATION** | | | |
| Photo verification | ✅ | ✅ | ✅ Priority review |
| ID verification (optional) | ✅ | ✅ | ✅ + badge |
| Incognito mode | ❌ | ✅ | ✅ + selective visibility |
| Block & report | ✅ Unlimited | ✅ Unlimited | ✅ + priority support |
| **EVENTS & COMMUNITY** | | | |
| View event listings | ✅ | ✅ | ✅ |
| RSVP to events | 💰 $10-50 per event | ✅ 1 free/month + discounts | ✅ 2 free/month + 50% off |
| Host private events | ❌ | ❌ | ✅ Request hosting |
| Community forums | ✅ Read-only | ✅ Full access | ✅ + Expert AMAs |
| **VIDEO DATING** | | | |
| Video calls in-app | ✅ 30 min/week | ✅ Unlimited | ✅ Unlimited + recording |
| Video date scheduling | ❌ | ✅ Calendar integration | ✅ + AI scheduling assistant |
| Icebreaker prompts | ❌ | ✅ | ✅ + personalized |
| **ANALYTICS & INSIGHTS** | | | |
| Profile strength score | ✅ Basic | ✅ Detailed | ✅ + optimization tips |
| Match analytics | ❌ | ✅ Weekly reports | ✅ Real-time dashboard |
| Attachment growth tracking | ❌ | ✅ Monthly | ✅ + personalized coaching |
| Response rate stats | ❌ | ✅ | ✅ + benchmarking |
| **SUPPORT** | | | |
| Help center | ✅ | ✅ | ✅ |
| Email support | ✅ 48-hour response | ✅ 24-hour response | ✅ Priority 4-hour response |
| Dating coach access | ❌ | ❌ | 💰 $49/session (20% off) |

---

## Pricing Strategy

### Subscription Pricing

```
┌────────────────────────────────────────────────────────────┐
│                    Premium - $12.99/month                   │
│                                                             │
│  Monthly: $12.99/mo                                        │
│  3 Months: $9.99/mo ($29.97 total) - SAVE 23%            │
│  6 Months: $7.99/mo ($47.94 total) - SAVE 38%            │
│  Annual: $6.99/mo ($83.88 total) - SAVE 46%              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                     Elite - $29.99/month                    │
│                                                             │
│  Monthly: $29.99/mo                                        │
│  3 Months: $24.99/mo ($74.97 total) - SAVE 17%           │
│  6 Months: $21.99/mo ($131.94 total) - SAVE 27%          │
│  Annual: $18.99/mo ($227.88 total) - SAVE 37%            │
└────────────────────────────────────────────────────────────┘
```

### Pricing Rationale

**Premium ($12.99)**
- Competitive with Tinder Plus ($14.99), Hinge Preferred ($9.99)
- Entry point for users who see value but aren't fully committed
- Covers infrastructure costs at ~40% profit margin

**Elite ($29.99)**
- Comparable to Match ($35.99), eHarmony Premium ($59.90)
- Appeals to serious daters willing to invest in tools
- Includes high-touch features (coaching, events)
- 65% profit margin (higher-touch features front-loaded)

### Dynamic Pricing (Ethical Implementation)

```python
def calculate_promotional_pricing(user: UserProfile) -> Dict:
    """
    Offer context-appropriate discounts without exploitation
    """

    base_prices = {
        "premium_monthly": 12.99,
        "elite_monthly": 29.99
    }

    # ETHICAL discounts (NEVER discriminatory)
    discounts = []

    # 1. New user welcome (first 30 days only)
    if user.days_since_signup <= 30:
        discounts.append({
            "type": "new_user",
            "percentage": 0.20,  # 20% off first month
            "message": "Welcome offer: 20% off your first month!"
        })

    # 2. Re-engagement (churned users, >90 days inactive)
    if user.days_since_last_login > 90:
        discounts.append({
            "type": "win_back",
            "percentage": 0.30,  # 30% off
            "message": "We missed you! 30% off to welcome you back"
        })

    # 3. Seasonal promotions (Valentine's, etc.)
    if is_seasonal_promotion_period():
        discounts.append({
            "type": "seasonal",
            "percentage": 0.15,
            "message": "Valentine's Special: 15% off Premium"
        })

    # 4. Bundle deal (annual subscription)
    if user.viewing_annual_option:
        # Already reflected in base pricing (46% off)
        pass

    # PROHIBITED: Price discrimination based on:
    # - Engagement/desperation signals (anxious attachment, frequent checking)
    # - Demographics (location, age, gender)
    # - Device type (iOS vs Android)
    # - Match success (struggling users charged more)

    # Apply best discount (don't stack)
    if discounts:
        best_discount = max(discounts, key=lambda x: x["percentage"])
        final_prices = {
            tier: price * (1 - best_discount["percentage"])
            for tier, price in base_prices.items()
        }
        return {
            "prices": final_prices,
            "discount": best_discount,
            "expires": datetime.utcnow() + timedelta(days=7)
        }

    return {"prices": base_prices, "discount": None}
```

---

## A La Carte Pricing (Microtransactions)

### Power-Ups & Enhancements

| Item | Price | What You Get | Expected Outcome | Free Alternative |
|------|-------|--------------|------------------|------------------|
| **Profile Boost (30 min)** | $3.99 | Peak-time visibility (6-9 PM) | 35-55 profile views, 5-10 matches | Complete profile for better organic reach |
| **Super Like** | $1.99 | Show strong interest with notification | 3x higher response rate | Use thoughtful first message (free) |
| **AI Icebreaker** | $1.99 | Personalized conversation starter | Higher quality opening, 40% response boost | Browse their profile for conversation hooks |
| **Read Receipts (7 days)** | $2.99 | See when they read your messages | Reduce anxiety about ghosting | Practice secure attachment patterns |
| **Spotlight (1 hour)** | $6.99 | Top of stack for 1 hour | 3-5x profile views | Use during peak hours for free |
| **Message Before Matching** | $4.99 | Send intro before they swipe | Bypass swipe requirement | Wait for mutual match (more authentic) |
| **AI Coaching Session** | $6.99 | 30-min guided practice + analysis | Improve communication skills | 3 free AI sessions/week |
| **Profile Review by Expert** | $19.99 | Human dating coach feedback | Professionally optimized profile | Use free profile tips in app |

### Bundles (Better Value)

```
┌───────────────────────────────────────────────────────────┐
│               Confidence Boost Bundle - $14.99            │
│                        (Save 25%)                          │
│                                                            │
│  • 3 Profile Boosts ($11.97 value)                       │
│  • 5 Super Likes ($9.95 value)                           │
│  • 1 AI Coaching Session ($6.99 value)                   │
│                                                            │
│  Total Value: $28.91 → Pay Only $14.99                   │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│              First Date Prep Bundle - $24.99              │
│                        (Save 30%)                          │
│                                                            │
│  • 1 Profile Review ($19.99 value)                       │
│  • 10 AI Icebreakers ($19.90 value)                     │
│  • 3 AI Coaching Sessions ($20.97 value)                 │
│  • 1 Month Read Receipts ($11.96 value)                 │
│                                                            │
│  Total Value: $72.82 → Pay Only $24.99                   │
└───────────────────────────────────────────────────────────┘
```

### Ethical Microtransaction Design

**✅ ETHICAL: Transparent, Value-Adding**

- Show historical success rates: "Last 100 boosts averaged 47 views"
- Warn when unlikely to help: "Your profile is 60% complete—finish it first for better results"
- Provide free alternatives: "Or try: Complete your profile (free!)"
- Time-limited (prevent addiction): "1 boost per 24 hours maximum"

**❌ UNETHICAL: Exploitative, Deceptive**

- ❌ Hiding high-quality matches behind paywalls
- ❌ Fake "someone liked you!" notifications to drive purchases
- ❌ Algorithmic throttling of free users
- ❌ Preying on anxious attachment: "Boost now or they'll move on!"
- ❌ Unlimited purchases encouraging compulsive spending

---

## Event-Based Revenue

### Community Events (Hybrid Revenue)

| Event Type | Attendance | Ticket Price | Revenue/Event | Frequency |
|------------|-----------|--------------|---------------|-----------|
| **Attachment-Based Speed Dating** | 20-40 people | $25 (Free: 1/mo Premium, 2/mo Elite) | $500-1000 | Monthly in each city |
| **Secure Communication Workshop** | 15-25 people | $35 (50% off Elite) | $525-875 | Quarterly |
| **Therapist-Led Relationships AMA** | 50-100 (virtual) | $15 (Free for Elite) | $750-1500 | Monthly |
| **Singles Hiking/Activity Group** | 10-20 people | $15-20 | $150-400 | Weekly |
| **Anxious-Avoidant Support Group** | 8-15 people | $20 | $160-300 | Bi-weekly |

### Event Economics

- **Average revenue per event**: $400-800
- **Cost per event**: $150-300 (venue, facilitator, materials)
- **Net margin**: 50-60%
- **Secondary benefit**: Community building → retention ↑↑

### Elite Tier Event Perks

- 2 free events per month (any type)
- 50% discount on additional events
- Private "Elite Singles Mixers" (quarterly, free)
- Option to request/host events in their city

---

## Revenue Projections & Unit Economics

### User Funnel Assumptions

```
Total Active Users: 100,000
├─ Free: 89,000 (89%)
├─ Premium: 9,000 (9%)
└─ Elite: 2,000 (2%)

Conversion Rates (Industry Benchmarks vs. Ours):
• Industry average: 3-8% pay
• SaltBitter target: 11% pay (premium positioning)
• Free → Premium: 9% (vs 6% industry)
• Premium → Elite: 2% of total users (vs 1% industry)
```

### Monthly Recurring Revenue (MRR)

| Tier | Users | Avg Price | MRR | ARR |
|------|-------|-----------|-----|-----|
| Free | 89,000 | $0 | $0 | $0 |
| Premium | 9,000 | $9.50 (avg with annual discounts) | $85,500 | $1,026,000 |
| Elite | 2,000 | $22.00 (avg with annual discounts) | $44,000 | $528,000 |
| **Total Subscriptions** | **11,000** | | **$129,500** | **$1,554,000** |

### Microtransaction Revenue

```
Monthly Microtransaction Revenue (per 100k users):

Profile Boosts:
  • 10% of free users buy 1/month: 8,900 × $3.99 = $35,500
  • 5% of Premium buy 1/month: 450 × $3.99 = $1,796
  Total: $37,296/month

Super Likes:
  • 8% of free users buy 5-pack: 7,120 × $7.95 = $56,604

AI Icebreakers:
  • 15% of free users buy 3/month: 13,350 × $5.97 = $79,700

Other (read receipts, coaching, etc.): ~$25,000/month

Total Microtransactions: $198,600/month → $2,383,200/year
```

### Event Revenue

```
Per City Economics (assumes 5 cities):
• 4 events per city per month × 5 cities = 20 events/month
• Average net revenue per event: $450
• Monthly event revenue: $9,000
• Annual event revenue: $108,000
```

### Total Revenue Summary (100k Active Users)

| Revenue Stream | Monthly | Annual | % of Total |
|----------------|---------|--------|------------|
| Premium Subscriptions | $85,500 | $1,026,000 | 41% |
| Elite Subscriptions | $44,000 | $528,000 | 21% |
| Microtransactions | $198,600 | $2,383,200 | 34% |
| Events | $9,000 | $108,000 | 4% |
| **TOTAL** | **$337,100** | **$4,045,200** | **100%** |

**ARPU (Average Revenue Per User)**: $4.05/month ($48.60/year)
**ARPPU (Average Revenue Per Paying User)**: $36.82/month

---

## Customer Lifetime Value (LTV) Analysis

### Cohort Retention (Psychology-Focused Apps)

| Month | Free Retention | Premium Retention | Elite Retention |
|-------|---------------|-------------------|-----------------|
| 1 | 100% | 100% | 100% |
| 3 | 45% | 78% | 85% |
| 6 | 28% | 65% | 80% |
| 12 | 15% | 52% | 75% |
| 24 | 8% | 40% | 65% |

**Why Higher Retention?**
- Psychology-informed = perceived as self-improvement tool
- Community events = emotional investment beyond dating
- Success in relationships = positive word-of-mouth

### LTV Calculation

```python
def calculate_ltv(tier: str) -> float:
    """
    Calculate customer lifetime value with retention curve
    """

    if tier == "free":
        # Microtransaction LTV
        avg_monthly_spend = 0.45  # Only 5-8% of free users ever pay
        retention_months = [1.0, 0.45, 0.28, 0.15, 0.08]
        ltv = sum(avg_monthly_spend * retention for retention in retention_months)
        return ltv  # ~$0.43 LTV for free users

    elif tier == "premium":
        avg_monthly_spend = 9.50  # Average across monthly/annual plans
        retention_months = [1.0, 0.85, 0.78, 0.65, 0.52, 0.45, 0.40, 0.35, 0.32, 0.30, 0.28, 0.26]
        ltv = sum(avg_monthly_spend * retention for retention in retention_months)
        return ltv  # ~$59.45 LTV

    elif tier == "elite":
        avg_monthly_spend = 22.00
        retention_months = [1.0, 0.90, 0.85, 0.80, 0.75, 0.72, 0.68, 0.65, 0.63, 0.62, 0.61, 0.60]
        ltv = sum(avg_monthly_spend * retention for retention in retention_months)
        return ltv  # ~$165.10 LTV

# Blended LTV (across all tiers)
blended_ltv = (
    (0.89 * calculate_ltv("free")) +
    (0.09 * calculate_ltv("premium")) +
    (0.02 * calculate_ltv("elite"))
)
# = (0.89 * $0.43) + (0.09 * $59.45) + (0.02 * $165.10)
# = $0.38 + $5.35 + $3.30
# = $9.03 Blended LTV
```

### Customer Acquisition Cost (CAC) Targets

**Target LTV:CAC Ratio**: 3:1 (healthy SaaS benchmark)

Given Blended LTV of $9.03:
- **Maximum CAC**: $3.00 per user

But premium users are more valuable:
- **Free User CAC Target**: $0.50 (LTV: $0.43—focus on conversion)
- **Premium User CAC Target**: $20 (LTV: $59.45, ratio 3:1)
- **Elite User CAC Target**: $55 (LTV: $165.10, ratio 3:1)

**Acquisition Strategy**: Cast wide net with free tier (low CAC), convert to premium through value demonstration.

---

## Monetization Roadmap (Months 1-12)

### Phase 1: Launch (Months 1-3)
**Focus**: Build user base, validate core value proposition

- Launch with Free + Premium only (keep it simple)
- Pricing: Premium at $9.99/month (introductory pricing)
- No microtransactions yet (avoid "money grab" perception)
- Free events to build community

**Revenue Goal**: $5,000 MRR by Month 3
- 500 paying users × $10 avg = $5,000

### Phase 2: Optimization (Months 4-6)
**Focus**: Introduce microtransactions, test pricing

- Introduce profile boosts and super likes
- A/B test Premium pricing: $9.99 vs $12.99
- Launch first paid events in 2-3 cities
- Implement annual discount plans

**Revenue Goal**: $25,000 MRR by Month 6
- 2,000 Premium users × $10.50 = $21,000
- Microtransactions: $3,500/month
- Events: $500/month

### Phase 3: Expansion (Months 7-9)
**Focus**: Launch Elite tier, scale events

- Launch Elite tier at $29.99/month
- Expand events to 5 cities
- Introduce AI coaching packages
- Add bundles and package deals

**Revenue Goal**: $75,000 MRR by Month 9
- 5,000 Premium × $11 = $55,000
- 500 Elite × $24 = $12,000
- Microtransactions: $6,000
- Events: $2,000

### Phase 4: Maturity (Months 10-12)
**Focus**: Optimize conversion funnel, maximize ARPU

- Full feature set live
- Optimize pricing based on data
- Scale successful events, cut underperformers
- Launch affiliate partnerships (therapy, coaching)

**Revenue Goal**: $150,000 MRR by Month 12
- 10,000 Premium × $10 = $100,000
- 1,200 Elite × $23 = $27,600
- Microtransactions: $18,000
- Events: $4,400

---

## Ethical Safeguards in Monetization

### 1. **Free Tier Remains Valuable**
- Core matching never degraded
- Quality matches same as Premium
- No artificial scarcity ("You have 1 match! Upgrade to see more" ❌)

### 2. **Transparent Outcomes**
- Show realistic success rates for paid features
- Example: "Boosts average 47 views, 8 matches, 2-3 conversations"
- Warn when unlikely to help: "Your profile needs work first"

### 3. **No Exploitation of Vulnerability**
- Never target anxious attachment users with urgency tactics
- No "They're about to match someone else!" notifications
- No preying on loneliness or desperation

### 4. **Spending Limits**
- Optional self-imposed spending caps
- Warnings at $50/month, $100/month spend
- Encourage breaks: "You've been active 6 days straight—take a mental health day?"

### 5. **Value-Aligned Positioning**
- "Invest in your relationship skills" not "Buy more matches"
- Premium = convenience + coaching, not better outcomes
- Focus on self-improvement, not consumption

---

## Competitive Pricing Analysis

| App | Free Daily Likes | Premium Price | Key Premium Features |
|-----|------------------|---------------|----------------------|
| **Tinder** | 50-100 (but low-quality) | $14.99/mo | Unlimited likes, rewind, 5 super likes/week |
| **Bumble** | Unlimited (24h window) | $19.99/mo | Extend matches, rematch, see who liked |
| **Hinge** | 8 likes/day | $9.99/mo | Unlimited likes, see who liked, advanced filters |
| **Match** | View only, can't message | $35.99/mo | Required to message, events, phone support |
| **eHarmony** | See matches only | $59.90/mo | Required to communicate, compatibility reports |
| **SaltBitter** | 5-10 quality matches | $12.99/mo | Unlimited matches, AI coaching, attachment tools |

**SaltBitter Positioning**: Mid-tier pricing, premium psychology focus. More expensive than Hinge, less than Match, significantly better value than eHarmony for psych-focused features.

---

**Last Updated**: 2025-11-17
**Pricing Model**: Approved by Ethics Board
**Next Review**: Q1 2026 (Adjust based on user feedback and cohort data)
