"""Initial database schema with all 12 tables.

Revision ID: 001_initial
Revises:
Create Date: 2025-11-17 19:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Create all database tables.

    Creates:
    - PostGIS extension
    - 12 tables: users, profiles, attachment_assessments, matches, messages,
      ai_interactions, subscriptions, payments, events, event_registrations,
      consent_logs, compliance_logs
    - All indexes and constraints
    """

    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")  # For gen_random_uuid()

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("subscription_tier", sa.String(length=50), nullable=False, server_default=sa.text("'free'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_subscription_tier"), "users", ["subscription_tier"], unique=False)

    # Create profiles table
    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=50), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("photos", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("jsonb_build_array()"), nullable=False),
        sa.Column("location", geoalchemy2.types.Geography(geometry_type="POINT", srid=4326, from_text="ST_GeogFromText", name="geography"), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("looking_for_gender", sa.String(length=50), nullable=True),
        sa.Column("min_age", sa.Integer(), nullable=True),
        sa.Column("max_age", sa.Integer(), nullable=True),
        sa.Column("max_distance_km", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(op.f("ix_profiles_user_id"), "profiles", ["user_id"], unique=False)
    # Create spatial index for location using GIST
    op.execute("CREATE INDEX ix_profiles_location ON profiles USING GIST (location)")

    # Create attachment_assessments table
    op.create_table(
        "attachment_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("anxiety_score", sa.Float(), nullable=False),
        sa.Column("avoidance_score", sa.Float(), nullable=False),
        sa.Column("style", sa.String(length=50), nullable=False),
        sa.Column("assessment_version", sa.String(length=20), nullable=False, server_default=sa.text("'1.0'")),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default=sa.text("25")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_attachment_assessments_user_id"), "attachment_assessments", ["user_id"], unique=False)
    op.create_index(op.f("ix_attachment_assessments_style"), "attachment_assessments", ["style"], unique=False)

    # Create matches table
    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compatibility_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("user_a_id != user_b_id", name="different_users"),
        sa.CheckConstraint("compatibility_score >= 0 AND compatibility_score <= 100", name="valid_score"),
        sa.ForeignKeyConstraint(["user_a_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_b_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matches_user_a_id"), "matches", ["user_a_id"], unique=False)
    op.create_index(op.f("ix_matches_user_b_id"), "matches", ["user_b_id"], unique=False)
    op.create_index(op.f("ix_matches_status"), "matches", ["status"], unique=False)

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("from_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_from_user_id"), "messages", ["from_user_id"], unique=False)
    op.create_index(op.f("ix_messages_to_user_id"), "messages", ["to_user_id"], unique=False)
    op.create_index(op.f("ix_messages_sent_at"), "messages", ["sent_at"], unique=False)

    # Create ai_interactions table
    op.create_table(
        "ai_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_type", sa.String(length=100), nullable=False),
        sa.Column("disclosure_shown", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("user_consented", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_interactions_user_id"), "ai_interactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_ai_interactions_ai_type"), "ai_interactions", ["ai_type"], unique=False)

    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tier", sa.String(length=50), nullable=False, server_default=sa.text("'free'")),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_status"), "subscriptions", ["status"], unique=False)

    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("stripe_payment_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_invoice_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_payment_id"),
    )
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)
    op.create_index(op.f("ix_payments_created_at"), "payments", ["created_at"], unique=False)

    # Create events table
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("host_name", sa.String(length=255), nullable=True),
        sa.Column("video_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="valid_event_duration"),
        sa.CheckConstraint("capacity > 0", name="positive_capacity"),
        sa.CheckConstraint("price >= 0", name="non_negative_price"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_type"), "events", ["type"], unique=False)
    op.create_index(op.f("ix_events_start_time"), "events", ["start_time"], unique=False)

    # Create event_registrations table
    op.create_table(
        "event_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'registered'")),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_registrations_event_id"), "event_registrations", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_registrations_user_id"), "event_registrations", ["user_id"], unique=False)

    # Create consent_logs table
    op.create_table(
        "consent_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consent_type", sa.String(length=100), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("consent_text", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consent_logs_user_id"), "consent_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_consent_logs_consent_type"), "consent_logs", ["consent_type"], unique=False)

    # Create compliance_logs table
    op.create_table(
        "compliance_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("jsonb_build_object()"), nullable=False),
        sa.Column("regulatory_framework", sa.String(length=50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_compliance_logs_user_id"), "compliance_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_compliance_logs_action_type"), "compliance_logs", ["action_type"], unique=False)
    op.create_index(op.f("ix_compliance_logs_timestamp"), "compliance_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    """Downgrade: Drop all tables and extensions."""

    # Drop all tables in reverse order
    op.drop_index(op.f("ix_compliance_logs_timestamp"), table_name="compliance_logs")
    op.drop_index(op.f("ix_compliance_logs_action_type"), table_name="compliance_logs")
    op.drop_index(op.f("ix_compliance_logs_user_id"), table_name="compliance_logs")
    op.drop_table("compliance_logs")

    op.drop_index(op.f("ix_consent_logs_consent_type"), table_name="consent_logs")
    op.drop_index(op.f("ix_consent_logs_user_id"), table_name="consent_logs")
    op.drop_table("consent_logs")

    op.drop_index(op.f("ix_event_registrations_user_id"), table_name="event_registrations")
    op.drop_index(op.f("ix_event_registrations_event_id"), table_name="event_registrations")
    op.drop_table("event_registrations")

    op.drop_index(op.f("ix_events_start_time"), table_name="events")
    op.drop_index(op.f("ix_events_type"), table_name="events")
    op.drop_table("events")

    op.drop_index(op.f("ix_payments_created_at"), table_name="payments")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_table("payments")

    op.drop_index(op.f("ix_subscriptions_status"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index(op.f("ix_ai_interactions_ai_type"), table_name="ai_interactions")
    op.drop_index(op.f("ix_ai_interactions_user_id"), table_name="ai_interactions")
    op.drop_table("ai_interactions")

    op.drop_index(op.f("ix_messages_sent_at"), table_name="messages")
    op.drop_index(op.f("ix_messages_to_user_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_from_user_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_matches_status"), table_name="matches")
    op.drop_index(op.f("ix_matches_user_b_id"), table_name="matches")
    op.drop_index(op.f("ix_matches_user_a_id"), table_name="matches")
    op.drop_table("matches")

    op.drop_index(op.f("ix_attachment_assessments_style"), table_name="attachment_assessments")
    op.drop_index(op.f("ix_attachment_assessments_user_id"), table_name="attachment_assessments")
    op.drop_table("attachment_assessments")

    op.execute("DROP INDEX IF EXISTS ix_profiles_location")
    op.drop_index(op.f("ix_profiles_user_id"), table_name="profiles")
    op.drop_table("profiles")

    op.drop_index(op.f("ix_users_subscription_tier"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS postgis")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
