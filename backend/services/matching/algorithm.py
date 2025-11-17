"""
Multi-factor compatibility matching algorithm.

Combines multiple factors to calculate overall compatibility scores:
- Attachment style compatibility (40% weight)
- Location proximity via PostGIS (20% weight)
- Interest/bio similarity via embeddings (20% weight)
- Age preference matching (10% weight)
- Other preference filters (10% weight)

Total compatibility score: 0-100 scale
"""

from dataclasses import dataclass
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AttachmentAssessment, Profile, User

from .compatibility import calculate_attachment_compatibility
from .embeddings import calculate_bio_similarity

# Scoring weights (must sum to 100%)
WEIGHTS = {
    "attachment": 0.40,  # 40% - Psychology-based compatibility
    "location": 0.20,  # 20% - Geographic proximity
    "interests": 0.20,  # 20% - Shared interests/values
    "age": 0.10,  # 10% - Age preference matching
    "other": 0.10,  # 10% - Other preferences (gender, etc.)
}


@dataclass
class UserMatchProfile:
    """Complete user profile for matching calculations."""

    user_id: UUID
    # Profile data
    age: int
    gender: str
    bio: str | None
    location_lat: float | None
    location_lon: float | None
    # Preferences
    looking_for_gender: str | None
    min_age: int | None
    max_age: int | None
    max_distance_km: int | None
    # Attachment data
    attachment_style: str
    anxiety_score: float
    avoidance_score: float
    # User metadata
    subscription_tier: str


@dataclass
class CompatibilityScore:
    """Detailed compatibility breakdown."""

    user_a_id: UUID
    user_b_id: UUID
    total_score: float
    # Component scores
    attachment_score: float
    location_score: float
    interests_score: float
    age_score: float
    other_score: float
    # Metadata
    attachment_styles: tuple[str, str]
    distance_km: float | None


def calculate_location_score(
    user_a: UserMatchProfile, user_b: UserMatchProfile
) -> tuple[float, float | None]:
    """
    Calculate location proximity score.

    Score based on distance between users:
    - 0-10km: 100 points
    - 10-25km: 80 points
    - 25-50km: 60 points
    - 50-100km: 40 points
    - 100-200km: 20 points
    - 200km+: 0 points

    Args:
        user_a: First user's profile
        user_b: Second user's profile

    Returns:
        tuple: (score, distance_km)
            - score: 0-100
            - distance_km: Distance in km, or None if location missing
    """
    # If either user missing location, return moderate score
    if (
        user_a.location_lat is None
        or user_a.location_lon is None
        or user_b.location_lat is None
        or user_b.location_lon is None
    ):
        return 50.0, None

    # Calculate distance using Haversine formula
    # Convert to radians
    lat1, lon1 = np.radians(user_a.location_lat), np.radians(user_a.location_lon)
    lat2, lon2 = np.radians(user_b.location_lat), np.radians(user_b.location_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    distance_km = float(6371 * c)  # Earth radius in km

    # Score based on distance brackets
    if distance_km <= 10:
        score = 100.0
    elif distance_km <= 25:
        score = 80.0
    elif distance_km <= 50:
        score = 60.0
    elif distance_km <= 100:
        score = 40.0
    elif distance_km <= 200:
        score = 20.0
    else:
        score = 0.0

    return score, distance_km


def calculate_age_preference_score(user_a: UserMatchProfile, user_b: UserMatchProfile) -> float:
    """
    Calculate age preference matching score.

    Checks if both users fall within each other's age preferences.
    - Both match: 100 points
    - One matches: 50 points
    - Neither matches: 0 points

    Args:
        user_a: First user's profile
        user_b: Second user's profile

    Returns:
        float: Score (0-100)
    """
    # Check if A is in B's age range
    a_in_b_range = True
    if user_b.min_age is not None and user_a.age < user_b.min_age:
        a_in_b_range = False
    if user_b.max_age is not None and user_a.age > user_b.max_age:
        a_in_b_range = False

    # Check if B is in A's age range
    b_in_a_range = True
    if user_a.min_age is not None and user_b.age < user_a.min_age:
        b_in_a_range = False
    if user_a.max_age is not None and user_b.age > user_a.max_age:
        b_in_a_range = False

    # Score based on mutual matching
    if a_in_b_range and b_in_a_range:
        return 100.0
    elif a_in_b_range or b_in_a_range:
        return 50.0
    else:
        return 0.0


def calculate_other_preferences_score(
    user_a: UserMatchProfile, user_b: UserMatchProfile
) -> float:
    """
    Calculate score for other preference filters (gender, etc.).

    Checks gender preferences match.

    Args:
        user_a: First user's profile
        user_b: Second user's profile

    Returns:
        float: Score (0-100)
    """
    # Check gender preferences
    gender_match_score = 0.0

    # Check if A is looking for B's gender
    if user_a.looking_for_gender:
        if user_a.looking_for_gender == user_b.gender or user_a.looking_for_gender == "any":
            gender_match_score += 50.0

    # Check if B is looking for A's gender
    if user_b.looking_for_gender:
        if user_b.looking_for_gender == user_a.gender or user_b.looking_for_gender == "any":
            gender_match_score += 50.0

    # If no preferences set, give moderate score
    if not user_a.looking_for_gender and not user_b.looking_for_gender:
        gender_match_score = 75.0

    return min(gender_match_score, 100.0)


def calculate_compatibility(user_a: UserMatchProfile, user_b: UserMatchProfile) -> CompatibilityScore:
    """
    Calculate overall compatibility score between two users.

    Combines all factors with appropriate weights to produce final score.

    Args:
        user_a: First user's complete profile
        user_b: Second user's complete profile

    Returns:
        CompatibilityScore: Detailed compatibility breakdown

    Examples:
        >>> # Two secure attachment users, close location, similar interests
        >>> user_a = UserMatchProfile(
        ...     user_id=UUID('00000000-0000-0000-0000-000000000001'),
        ...     age=28, gender='female', bio='Love hiking and nature',
        ...     location_lat=37.7749, location_lon=-122.4194,
        ...     looking_for_gender='male', min_age=25, max_age=35, max_distance_km=50,
        ...     attachment_style='secure', anxiety_score=30.0, avoidance_score=25.0,
        ...     subscription_tier='free'
        ... )
        >>> user_b = UserMatchProfile(
        ...     user_id=UUID('00000000-0000-0000-0000-000000000002'),
        ...     age=30, gender='male', bio='Passionate about hiking and outdoors',
        ...     location_lat=37.7849, location_lon=-122.4294,
        ...     looking_for_gender='female', min_age=25, max_age=32, max_distance_km=25,
        ...     attachment_style='secure', anxiety_score=35.0, avoidance_score=20.0,
        ...     subscription_tier='premium'
        ... )
        >>> score = calculate_compatibility(user_a, user_b)  # doctest: +SKIP
        >>> score.total_score >= 80  # High compatibility expected  # doctest: +SKIP
        True
    """
    # 1. Attachment compatibility (40% weight)
    attachment_score = calculate_attachment_compatibility(
        user_a.attachment_style, user_b.attachment_style  # type: ignore
    )

    # 2. Location proximity (20% weight)
    location_score, distance_km = calculate_location_score(user_a, user_b)

    # 3. Interest/bio similarity (20% weight)
    bio_a = user_a.bio or ""
    bio_b = user_b.bio or ""
    interests_score = calculate_bio_similarity(bio_a, bio_b)

    # 4. Age preference (10% weight)
    age_score = calculate_age_preference_score(user_a, user_b)

    # 5. Other preferences (10% weight)
    other_score = calculate_other_preferences_score(user_a, user_b)

    # Calculate weighted total
    total_score = (
        attachment_score * WEIGHTS["attachment"]
        + location_score * WEIGHTS["location"]
        + interests_score * WEIGHTS["interests"]
        + age_score * WEIGHTS["age"]
        + other_score * WEIGHTS["other"]
    )

    return CompatibilityScore(
        user_a_id=user_a.user_id,
        user_b_id=user_b.user_id,
        total_score=round(total_score, 2),
        attachment_score=round(attachment_score, 2),
        location_score=round(location_score, 2),
        interests_score=round(interests_score, 2),
        age_score=round(age_score, 2),
        other_score=round(other_score, 2),
        attachment_styles=(user_a.attachment_style, user_b.attachment_style),
        distance_km=round(distance_km, 2) if distance_km is not None else None,
    )


def passes_preference_filters(user_a: UserMatchProfile, user_b: UserMatchProfile) -> bool:
    """
    Check if two users pass each other's basic preference filters.

    Hard filters that must pass before scoring:
    - Gender preferences
    - Age range
    - Maximum distance

    Args:
        user_a: First user's profile
        user_b: Second user's profile

    Returns:
        bool: True if both users pass each other's filters
    """
    # Check A's preferences for B
    if user_a.looking_for_gender and user_a.looking_for_gender != "any":
        if user_b.gender != user_a.looking_for_gender:
            return False

    if user_a.min_age and user_b.age < user_a.min_age:
        return False
    if user_a.max_age and user_b.age > user_a.max_age:
        return False

    # Check B's preferences for A
    if user_b.looking_for_gender and user_b.looking_for_gender != "any":
        if user_a.gender != user_b.looking_for_gender:
            return False

    if user_b.min_age and user_a.age < user_b.min_age:
        return False
    if user_b.max_age and user_a.age > user_b.max_age:
        return False

    # Check distance (if both have location and max_distance set)
    if all(
        [
            user_a.location_lat,
            user_a.location_lon,
            user_b.location_lat,
            user_b.location_lon,
        ]
    ):
        _, distance_km = calculate_location_score(user_a, user_b)
        if distance_km is not None:
            if user_a.max_distance_km and distance_km > user_a.max_distance_km:
                return False
            if user_b.max_distance_km and distance_km > user_b.max_distance_km:
                return False

    return True


async def fetch_user_match_profile(db: AsyncSession, user_id: UUID) -> UserMatchProfile | None:
    """
    Fetch complete user profile for matching.

    Joins user, profile, and attachment assessment tables.

    Args:
        db: Database session
        user_id: User ID to fetch

    Returns:
        UserMatchProfile or None if user not found/incomplete
    """
    # Query joining all required tables
    query = (
        select(User, Profile, AttachmentAssessment)
        .join(Profile, Profile.user_id == User.id)
        .join(AttachmentAssessment, AttachmentAssessment.user_id == User.id)
        .where(User.id == user_id)
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        return None

    user, profile, attachment = row

    # Extract location coordinates if available
    location_lat = None
    location_lon = None
    if profile.location is not None:
        # PostGIS geography type - extract coordinates
        # location is stored as WKB, need to extract lat/lon
        # For now, we'll handle this in the query or use ST_X/ST_Y functions
        pass  # Will be handled via PostGIS functions in production

    return UserMatchProfile(
        user_id=user.id,
        age=profile.age,
        gender=profile.gender,
        bio=profile.bio,
        location_lat=location_lat,
        location_lon=location_lon,
        looking_for_gender=profile.looking_for_gender,
        min_age=profile.min_age,
        max_age=profile.max_age,
        max_distance_km=profile.max_distance_km,
        attachment_style=attachment.style,
        anxiety_score=attachment.anxiety_score,
        avoidance_score=attachment.avoidance_score,
        subscription_tier=user.subscription_tier,
    )
