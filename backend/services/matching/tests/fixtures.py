"""Test fixtures for matching service tests."""

from uuid import UUID, uuid4

from services.matching.algorithm import UserMatchProfile


def create_test_user_profile(
    user_id: UUID | None = None,
    age: int = 28,
    gender: str = "female",
    bio: str = "I love hiking and photography",
    location_lat: float | None = 37.7749,
    location_lon: float | None = -122.4194,
    looking_for_gender: str | None = "male",
    min_age: int | None = 25,
    max_age: int | None = 35,
    max_distance_km: int | None = 50,
    attachment_style: str = "secure",
    anxiety_score: float = 30.0,
    avoidance_score: float = 25.0,
    subscription_tier: str = "free",
) -> UserMatchProfile:
    """
    Create a test user match profile with default values.

    Args:
        user_id: User UUID (random if not provided)
        age: User age
        gender: User gender
        bio: User bio text
        location_lat: Latitude
        location_lon: Longitude
        looking_for_gender: Gender preference
        min_age: Minimum age preference
        max_age: Maximum age preference
        max_distance_km: Maximum distance preference
        attachment_style: Attachment style
        anxiety_score: Anxiety score (0-100)
        avoidance_score: Avoidance score (0-100)
        subscription_tier: Subscription tier

    Returns:
        UserMatchProfile: Test user profile
    """
    return UserMatchProfile(
        user_id=user_id or uuid4(),
        age=age,
        gender=gender,
        bio=bio,
        location_lat=location_lat,
        location_lon=location_lon,
        looking_for_gender=looking_for_gender,
        min_age=min_age,
        max_age=max_age,
        max_distance_km=max_distance_km,
        attachment_style=attachment_style,
        anxiety_score=anxiety_score,
        avoidance_score=avoidance_score,
        subscription_tier=subscription_tier,
    )


# Predefined test users
SECURE_USER_SF = create_test_user_profile(
    user_id=UUID("00000000-0000-0000-0000-000000000001"),
    age=28,
    gender="female",
    bio="Love hiking, photography, and exploring nature. Looking for genuine connections.",
    location_lat=37.7749,
    location_lon=-122.4194,
    attachment_style="secure",
    anxiety_score=30.0,
    avoidance_score=25.0,
)

SECURE_USER_SF_MALE = create_test_user_profile(
    user_id=UUID("00000000-0000-0000-0000-000000000002"),
    age=30,
    gender="male",
    bio="Passionate about hiking, outdoor adventures, and photography. Seeking meaningful relationship.",
    location_lat=37.7849,
    location_lon=-122.4294,
    looking_for_gender="female",
    min_age=25,
    max_age=32,
    attachment_style="secure",
    anxiety_score=35.0,
    avoidance_score=20.0,
    subscription_tier="premium",
)

ANXIOUS_USER_NYC = create_test_user_profile(
    user_id=UUID("00000000-0000-0000-0000-000000000003"),
    age=26,
    gender="female",
    bio="Love cooking, reading, and cozy nights in. Looking for someone special.",
    location_lat=40.7128,
    location_lon=-74.0060,
    attachment_style="anxious",
    anxiety_score=75.0,
    avoidance_score=30.0,
)

AVOIDANT_USER_NYC = create_test_user_profile(
    user_id=UUID("00000000-0000-0000-0000-000000000004"),
    age=32,
    gender="male",
    bio="Independent traveler, entrepreneur. Value freedom and personal space.",
    location_lat=40.7228,
    location_lon=-74.0160,
    looking_for_gender="female",
    min_age=24,
    max_age=35,
    attachment_style="avoidant",
    anxiety_score=25.0,
    avoidance_score=80.0,
)

USER_NO_LOCATION = create_test_user_profile(
    user_id=UUID("00000000-0000-0000-0000-000000000005"),
    age=29,
    gender="male",
    bio="Tech enthusiast, gamer, and coffee lover.",
    location_lat=None,
    location_lon=None,
    looking_for_gender="female",
    attachment_style="secure",
    anxiety_score=35.0,
    avoidance_score=30.0,
)

USER_EMPTY_BIO = create_test_user_profile(
    user_id=UUID("00000000-0000-0000-0000-000000000006"),
    age=27,
    gender="female",
    bio="",
    attachment_style="secure",
    anxiety_score=40.0,
    avoidance_score=35.0,
)
