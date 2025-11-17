"""
Database seed data for development environment.

Creates test users, profiles, and sample data for local development and testing.
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import (
    AIInteraction,
    AttachmentAssessment,
    Base,
    ComplianceLog,
    ConsentLog,
    Event,
    EventRegistration,
    Match,
    Message,
    Payment,
    Profile,
    Subscription,
    User,
)


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/saltbitter_dev")


def create_seed_data() -> None:
    """Create seed data for development environment."""

    # Create database engine and session
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("🌱 Seeding database with test data...")

        # Create test users
        users = []
        user_data = [
            {
                "email": "alice@example.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPQg0J5CWu",  # password: test123
                "verified": True,
                "subscription_tier": "free",
            },
            {
                "email": "bob@example.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPQg0J5CWu",
                "verified": True,
                "subscription_tier": "premium",
            },
            {
                "email": "charlie@example.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPQg0J5CWu",
                "verified": True,
                "subscription_tier": "elite",
            },
            {
                "email": "diana@example.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPQg0J5CWu",
                "verified": True,
                "subscription_tier": "free",
            },
            {
                "email": "ethan@example.com",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPQg0J5CWu",
                "verified": False,
                "subscription_tier": "free",
            },
        ]

        for data in user_data:
            user = User(**data)
            session.add(user)
            users.append(user)

        session.flush()  # Get user IDs
        print(f"✓ Created {len(users)} test users")

        # Create profiles
        profile_data = [
            {
                "user_id": users[0].id,
                "name": "Alice Johnson",
                "age": 28,
                "gender": "female",
                "bio": "Love hiking, reading, and good coffee. Looking for someone genuine and kind.",
                "photos": ["https://example.com/alice1.jpg", "https://example.com/alice2.jpg"],
                "completeness_score": 85.0,
                "looking_for_gender": "male",
                "min_age": 25,
                "max_age": 35,
                "max_distance_km": 50,
            },
            {
                "user_id": users[1].id,
                "name": "Bob Smith",
                "age": 32,
                "gender": "male",
                "bio": "Software engineer who enjoys rock climbing and cooking. Seeking meaningful connections.",
                "photos": ["https://example.com/bob1.jpg"],
                "completeness_score": 70.0,
                "looking_for_gender": "female",
                "min_age": 26,
                "max_age": 36,
                "max_distance_km": 30,
            },
            {
                "user_id": users[2].id,
                "name": "Charlie Davis",
                "age": 30,
                "gender": "non-binary",
                "bio": "Artist and musician. Passionate about environmental causes and social justice.",
                "photos": ["https://example.com/charlie1.jpg", "https://example.com/charlie2.jpg"],
                "completeness_score": 90.0,
                "looking_for_gender": "any",
                "min_age": 25,
                "max_age": 40,
                "max_distance_km": 100,
            },
            {
                "user_id": users[3].id,
                "name": "Diana Martinez",
                "age": 27,
                "gender": "female",
                "bio": "Yoga instructor and wellness coach. Love nature, meditation, and meaningful conversations.",
                "photos": ["https://example.com/diana1.jpg"],
                "completeness_score": 75.0,
                "looking_for_gender": "male",
                "min_age": 25,
                "max_age": 35,
                "max_distance_km": 40,
            },
        ]

        for data in profile_data:
            profile = Profile(**data)
            session.add(profile)

        print(f"✓ Created {len(profile_data)} test profiles")

        # Create attachment assessments
        assessment_data = [
            {
                "user_id": users[0].id,
                "anxiety_score": 25.0,
                "avoidance_score": 20.0,
                "style": "secure",
            },
            {
                "user_id": users[1].id,
                "anxiety_score": 65.0,
                "avoidance_score": 30.0,
                "style": "anxious",
            },
            {
                "user_id": users[2].id,
                "anxiety_score": 30.0,
                "avoidance_score": 70.0,
                "style": "avoidant",
            },
            {
                "user_id": users[3].id,
                "anxiety_score": 70.0,
                "avoidance_score": 65.0,
                "style": "fearful-avoidant",
            },
        ]

        for data in assessment_data:
            assessment = AttachmentAssessment(**data)
            session.add(assessment)

        print(f"✓ Created {len(assessment_data)} attachment assessments")

        # Create matches
        match_data = [
            {
                "user_a_id": users[0].id,
                "user_b_id": users[1].id,
                "compatibility_score": 85.5,
                "status": "matched",
            },
            {
                "user_a_id": users[0].id,
                "user_b_id": users[2].id,
                "compatibility_score": 72.3,
                "status": "pending",
            },
            {
                "user_a_id": users[1].id,
                "user_b_id": users[3].id,
                "compatibility_score": 68.9,
                "status": "liked",
            },
        ]

        for data in match_data:
            match = Match(**data)
            session.add(match)

        print(f"✓ Created {len(match_data)} test matches")

        # Create messages
        message_data = [
            {
                "from_user_id": users[0].id,
                "to_user_id": users[1].id,
                "content": "Hi Bob! I saw you like rock climbing too. Where do you usually go?",
                "sent_at": datetime.now() - timedelta(hours=2),
            },
            {
                "from_user_id": users[1].id,
                "to_user_id": users[0].id,
                "content": "Hey Alice! I usually go to the climbing gym downtown. Have you been there?",
                "sent_at": datetime.now() - timedelta(hours=1),
                "read_at": datetime.now() - timedelta(minutes=30),
            },
            {
                "from_user_id": users[0].id,
                "to_user_id": users[1].id,
                "content": "Yes! I love that place. Maybe we could go together sometime?",
                "sent_at": datetime.now() - timedelta(minutes=15),
            },
        ]

        for data in message_data:
            message = Message(**data)
            session.add(message)

        print(f"✓ Created {len(message_data)} test messages")

        # Create subscriptions
        subscription_data = [
            {
                "user_id": users[1].id,
                "tier": "premium",
                "status": "active",
                "stripe_customer_id": "cus_test_bob",
                "stripe_subscription_id": "sub_test_bob_premium",
                "current_period_start": datetime.now() - timedelta(days=10),
                "current_period_end": datetime.now() + timedelta(days=20),
            },
            {
                "user_id": users[2].id,
                "tier": "elite",
                "status": "active",
                "stripe_customer_id": "cus_test_charlie",
                "stripe_subscription_id": "sub_test_charlie_elite",
                "current_period_start": datetime.now() - timedelta(days=5),
                "current_period_end": datetime.now() + timedelta(days=25),
            },
        ]

        for data in subscription_data:
            subscription = Subscription(**data)
            session.add(subscription)

        print(f"✓ Created {len(subscription_data)} test subscriptions")

        # Create payments
        payment_data = [
            {
                "user_id": users[1].id,
                "amount": Decimal("12.99"),
                "type": "subscription",
                "status": "succeeded",
                "stripe_payment_id": "pi_test_bob_1",
            },
            {
                "user_id": users[2].id,
                "amount": Decimal("29.99"),
                "type": "subscription",
                "status": "succeeded",
                "stripe_payment_id": "pi_test_charlie_1",
            },
            {
                "user_id": users[0].id,
                "amount": Decimal("4.99"),
                "type": "profile_boost",
                "status": "succeeded",
                "stripe_payment_id": "pi_test_alice_1",
            },
        ]

        for data in payment_data:
            payment = Payment(**data)
            session.add(payment)

        print(f"✓ Created {len(payment_data)} test payments")

        # Create events
        event_data = [
            {
                "title": "Virtual Speed Dating Night",
                "description": "Join us for a fun evening of 5-minute conversations!",
                "type": "speed_dating",
                "start_time": datetime.now() + timedelta(days=7, hours=19),
                "end_time": datetime.now() + timedelta(days=7, hours=21),
                "capacity": 30,
                "price": Decimal("15.00"),
                "host_name": "Sarah Thompson",
                "video_url": "https://zoom.us/j/test123",
            },
            {
                "title": "Communication Workshop",
                "description": "Learn effective communication strategies for dating",
                "type": "workshop",
                "start_time": datetime.now() + timedelta(days=14, hours=18),
                "end_time": datetime.now() + timedelta(days=14, hours=20),
                "capacity": 50,
                "price": Decimal("0.00"),
                "host_name": "Dr. Emily Chen",
            },
        ]

        for data in event_data:
            event = Event(**data)
            session.add(event)

        session.flush()  # Get event IDs
        print(f"✓ Created {len(event_data)} test events")

        # Create AI interactions
        ai_interaction_data = [
            {
                "user_id": users[0].id,
                "ai_type": "practice_companion",
                "disclosure_shown": True,
                "user_consented": True,
                "session_id": "session_001",
            },
            {
                "user_id": users[2].id,
                "ai_type": "relationship_coach",
                "disclosure_shown": True,
                "user_consented": True,
                "session_id": "session_002",
            },
        ]

        for data in ai_interaction_data:
            interaction = AIInteraction(**data)
            session.add(interaction)

        print(f"✓ Created {len(ai_interaction_data)} AI interactions")

        # Create consent logs
        consent_data = [
            {
                "user_id": users[0].id,
                "consent_type": "psychological_assessment",
                "granted": True,
                "consent_text": "I consent to psychological assessment data being used for matching",
                "ip_address": "192.168.1.1",
            },
            {
                "user_id": users[1].id,
                "consent_type": "ai_features",
                "granted": True,
                "consent_text": "I consent to using AI practice companions",
                "ip_address": "192.168.1.2",
            },
            {
                "user_id": users[2].id,
                "consent_type": "marketing",
                "granted": False,
                "consent_text": "I do not consent to marketing communications",
                "ip_address": "192.168.1.3",
            },
        ]

        for data in consent_data:
            consent = ConsentLog(**data)
            session.add(consent)

        print(f"✓ Created {len(consent_data)} consent logs")

        # Create compliance logs
        compliance_data = [
            {
                "user_id": users[0].id,
                "action_type": "ai_disclosure",
                "metadata": {"ai_type": "practice_companion", "disclosure_version": "1.0"},
                "regulatory_framework": "eu_ai_act",
            },
            {
                "user_id": users[1].id,
                "action_type": "data_export",
                "metadata": {"format": "json", "file_size": "2.5MB"},
                "regulatory_framework": "gdpr",
            },
        ]

        for data in compliance_data:
            log = ComplianceLog(**data)
            session.add(log)

        print(f"✓ Created {len(compliance_data)} compliance logs")

        # Commit all changes
        session.commit()
        print("\n✅ Database seeded successfully!")
        print(f"   - {len(users)} users")
        print(f"   - {len(profile_data)} profiles")
        print(f"   - {len(assessment_data)} attachment assessments")
        print(f"   - {len(match_data)} matches")
        print(f"   - {len(message_data)} messages")
        print(f"   - {len(subscription_data)} subscriptions")
        print(f"   - {len(payment_data)} payments")
        print(f"   - {len(event_data)} events")
        print(f"   - {len(ai_interaction_data)} AI interactions")
        print(f"   - {len(consent_data)} consent logs")
        print(f"   - {len(compliance_data)} compliance logs")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    create_seed_data()
