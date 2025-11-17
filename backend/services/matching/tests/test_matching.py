"""Comprehensive tests for matching service."""

import numpy as np
import pytest

from services.matching.algorithm import (
    calculate_age_preference_score,
    calculate_compatibility,
    calculate_location_score,
    calculate_other_preferences_score,
    passes_preference_filters,
)
from services.matching.compatibility import (
    calculate_attachment_compatibility,
    calculate_attachment_compatibility_from_scores,
    determine_attachment_style,
)
from services.matching.embeddings import (
    calculate_bio_similarity,
    calculate_cosine_similarity,
    generate_bio_embedding,
)

from .fixtures import (
    ANXIOUS_USER_NYC,
    AVOIDANT_USER_NYC,
    SECURE_USER_SF,
    SECURE_USER_SF_MALE,
    USER_EMPTY_BIO,
    USER_NO_LOCATION,
    create_test_user_profile,
)


class TestAttachmentCompatibility:
    """Test attachment theory compatibility calculations."""

    def test_determine_attachment_style_secure(self) -> None:
        """Test secure attachment style determination."""
        style = determine_attachment_style(30.0, 25.0)
        assert style == "secure"

    def test_determine_attachment_style_anxious(self) -> None:
        """Test anxious attachment style determination."""
        style = determine_attachment_style(75.0, 30.0)
        assert style == "anxious"

    def test_determine_attachment_style_avoidant(self) -> None:
        """Test avoidant attachment style determination."""
        style = determine_attachment_style(25.0, 80.0)
        assert style == "avoidant"

    def test_determine_attachment_style_fearful_avoidant(self) -> None:
        """Test fearful-avoidant attachment style determination."""
        style = determine_attachment_style(70.0, 75.0)
        assert style == "fearful-avoidant"

    def test_determine_attachment_style_boundary_cases(self) -> None:
        """Test boundary cases at threshold (50.0)."""
        # At exact threshold, should be low (secure/avoidant)
        style = determine_attachment_style(50.0, 50.0)
        assert style == "fearful-avoidant"

    def test_determine_attachment_style_invalid_scores(self) -> None:
        """Test invalid score ranges raise errors."""
        with pytest.raises(ValueError, match="Anxiety score must be 0-100"):
            determine_attachment_style(-10.0, 50.0)

        with pytest.raises(ValueError, match="Anxiety score must be 0-100"):
            determine_attachment_style(150.0, 50.0)

        with pytest.raises(ValueError, match="Avoidance score must be 0-100"):
            determine_attachment_style(50.0, -10.0)

    def test_calculate_attachment_compatibility_secure_secure(self) -> None:
        """Test secure-secure pairing (highest compatibility)."""
        score = calculate_attachment_compatibility("secure", "secure")
        assert score == 100.0

    def test_calculate_attachment_compatibility_secure_anxious(self) -> None:
        """Test secure-anxious pairing."""
        score = calculate_attachment_compatibility("secure", "anxious")
        assert score == 85.0

    def test_calculate_attachment_compatibility_anxious_avoidant(self) -> None:
        """Test anxious-avoidant pairing (lowest compatibility)."""
        score = calculate_attachment_compatibility("anxious", "avoidant")
        assert score == 40.0

    def test_calculate_attachment_compatibility_symmetric(self) -> None:
        """Test compatibility is symmetric (A-B = B-A)."""
        score_ab = calculate_attachment_compatibility("secure", "anxious")
        score_ba = calculate_attachment_compatibility("anxious", "secure")
        assert score_ab == score_ba

    def test_calculate_attachment_compatibility_from_scores(self) -> None:
        """Test end-to-end compatibility from raw scores."""
        score, style_a, style_b = calculate_attachment_compatibility_from_scores(
            30.0, 25.0, 35.0, 20.0
        )
        assert score == 100.0
        assert style_a == "secure"
        assert style_b == "secure"


class TestEmbeddings:
    """Test interest/bio similarity embeddings."""

    def test_generate_bio_embedding_shape(self) -> None:
        """Test embedding has correct dimensionality."""
        bio = "I love hiking and photography"
        embedding = generate_bio_embedding(bio)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32

    def test_generate_bio_embedding_normalized(self) -> None:
        """Test embeddings are normalized."""
        bio = "I love hiking and photography"
        embedding = generate_bio_embedding(bio)
        norm = np.linalg.norm(embedding)
        assert 0.99 <= norm <= 1.01

    def test_generate_bio_embedding_empty_bio(self) -> None:
        """Test empty bio returns zero vector."""
        embedding = generate_bio_embedding("")
        assert np.allclose(embedding, np.zeros(384))

    def test_calculate_cosine_similarity_identical(self) -> None:
        """Test cosine similarity of identical vectors."""
        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        similarity = calculate_cosine_similarity(vec, vec)
        assert similarity == 1.0

    def test_calculate_cosine_similarity_orthogonal(self) -> None:
        """Test cosine similarity of orthogonal vectors."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        similarity = calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.01

    def test_calculate_cosine_similarity_opposite(self) -> None:
        """Test cosine similarity of opposite vectors."""
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        similarity = calculate_cosine_similarity(vec1, vec2)
        assert similarity == -1.0

    def test_calculate_cosine_similarity_dimension_mismatch(self) -> None:
        """Test error on dimension mismatch."""
        vec1 = np.array([1.0, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        with pytest.raises(ValueError, match="Embedding dimensions must match"):
            calculate_cosine_similarity(vec1, vec2)

    def test_calculate_bio_similarity_similar_bios(self) -> None:
        """Test high similarity for similar bios."""
        bio1 = "I love hiking, camping, and outdoor adventures"
        bio2 = "Passionate about nature, hiking, and exploring the outdoors"
        similarity = calculate_bio_similarity(bio1, bio2)
        assert similarity > 70.0  # Should be quite similar

    def test_calculate_bio_similarity_different_bios(self) -> None:
        """Test low similarity for different bios."""
        bio1 = "Software engineer who loves coding and technology"
        bio2 = "Professional chef passionate about cooking and culinary arts"
        similarity = calculate_bio_similarity(bio1, bio2)
        assert similarity < 60.0  # Should be less similar

    def test_calculate_bio_similarity_empty_bios(self) -> None:
        """Test similarity with empty bios."""
        similarity = calculate_bio_similarity("", "")
        # Empty bios result in zero vectors, which have 50% similarity on 0-100 scale
        assert 45.0 <= similarity <= 55.0


class TestLocationScoring:
    """Test location proximity scoring."""

    def test_calculate_location_score_very_close(self) -> None:
        """Test scoring for very close users (<10km)."""
        user_a = create_test_user_profile(location_lat=37.7749, location_lon=-122.4194)
        user_b = create_test_user_profile(location_lat=37.7849, location_lon=-122.4294)
        score, distance = calculate_location_score(user_a, user_b)
        assert score == 100.0
        assert distance is not None
        assert distance < 2.0  # Should be ~1.5km

    def test_calculate_location_score_medium_distance(self) -> None:
        """Test scoring for medium distance (25-50km)."""
        user_a = create_test_user_profile(location_lat=37.7749, location_lon=-122.4194)
        user_b = create_test_user_profile(location_lat=37.3382, location_lon=-121.8863)
        score, distance = calculate_location_score(user_a, user_b)
        assert score == 60.0
        assert distance is not None
        assert 40.0 < distance < 70.0

    def test_calculate_location_score_far_distance(self) -> None:
        """Test scoring for far distance (200km+)."""
        user_a = create_test_user_profile(location_lat=37.7749, location_lon=-122.4194)  # SF
        user_b = create_test_user_profile(location_lat=34.0522, location_lon=-118.2437)  # LA
        score, distance = calculate_location_score(user_a, user_b)
        assert score == 0.0
        assert distance is not None
        assert distance > 500.0

    def test_calculate_location_score_missing_location(self) -> None:
        """Test scoring when location is missing."""
        user_a = create_test_user_profile(location_lat=None, location_lon=None)
        user_b = create_test_user_profile(location_lat=37.7749, location_lon=-122.4194)
        score, distance = calculate_location_score(user_a, user_b)
        assert score == 50.0  # Moderate score for missing location
        assert distance is None


class TestAgePreferences:
    """Test age preference matching."""

    def test_calculate_age_preference_score_mutual_match(self) -> None:
        """Test both users in each other's age range."""
        user_a = create_test_user_profile(age=28, min_age=25, max_age=35)
        user_b = create_test_user_profile(age=30, min_age=25, max_age=32)
        score = calculate_age_preference_score(user_a, user_b)
        assert score == 100.0

    def test_calculate_age_preference_score_one_match(self) -> None:
        """Test only one user in other's range."""
        user_a = create_test_user_profile(age=28, min_age=25, max_age=35)
        user_b = create_test_user_profile(age=40, min_age=35, max_age=45)
        score = calculate_age_preference_score(user_a, user_b)
        assert score == 50.0

    def test_calculate_age_preference_score_no_match(self) -> None:
        """Test neither user in other's range."""
        user_a = create_test_user_profile(age=22, min_age=20, max_age=25)
        user_b = create_test_user_profile(age=40, min_age=35, max_age=45)
        score = calculate_age_preference_score(user_a, user_b)
        assert score == 0.0

    def test_calculate_age_preference_score_no_preferences(self) -> None:
        """Test with no age preferences set."""
        user_a = create_test_user_profile(age=28, min_age=None, max_age=None)
        user_b = create_test_user_profile(age=30, min_age=None, max_age=None)
        score = calculate_age_preference_score(user_a, user_b)
        assert score == 100.0  # No restrictions = match


class TestOtherPreferences:
    """Test other preference filters (gender, etc.)."""

    def test_calculate_other_preferences_score_mutual_gender_match(self) -> None:
        """Test both users looking for each other's gender."""
        user_a = create_test_user_profile(gender="female", looking_for_gender="male")
        user_b = create_test_user_profile(gender="male", looking_for_gender="female")
        score = calculate_other_preferences_score(user_a, user_b)
        assert score == 100.0

    def test_calculate_other_preferences_score_one_gender_match(self) -> None:
        """Test only one user's gender preference matches."""
        user_a = create_test_user_profile(gender="female", looking_for_gender="male")
        user_b = create_test_user_profile(gender="male", looking_for_gender="male")
        score = calculate_other_preferences_score(user_a, user_b)
        assert score == 50.0

    def test_calculate_other_preferences_score_no_gender_match(self) -> None:
        """Test neither gender preference matches."""
        user_a = create_test_user_profile(gender="female", looking_for_gender="female")
        user_b = create_test_user_profile(gender="male", looking_for_gender="male")
        score = calculate_other_preferences_score(user_a, user_b)
        assert score == 0.0

    def test_calculate_other_preferences_score_any_gender(self) -> None:
        """Test 'any' gender preference."""
        user_a = create_test_user_profile(gender="female", looking_for_gender="any")
        user_b = create_test_user_profile(gender="male", looking_for_gender="female")
        score = calculate_other_preferences_score(user_a, user_b)
        assert score == 100.0


class TestPreferenceFilters:
    """Test hard preference filtering."""

    def test_passes_preference_filters_all_match(self) -> None:
        """Test users that pass all filters."""
        user_a = create_test_user_profile(
            age=28,
            gender="female",
            looking_for_gender="male",
            min_age=25,
            max_age=35,
            max_distance_km=50,
            location_lat=37.7749,
            location_lon=-122.4194,
        )
        user_b = create_test_user_profile(
            age=30,
            gender="male",
            looking_for_gender="female",
            min_age=25,
            max_age=32,
            max_distance_km=25,
            location_lat=37.7849,
            location_lon=-122.4294,
        )
        assert passes_preference_filters(user_a, user_b) is True

    def test_passes_preference_filters_gender_mismatch(self) -> None:
        """Test gender preference filter fails."""
        user_a = create_test_user_profile(gender="female", looking_for_gender="female")
        user_b = create_test_user_profile(gender="male", looking_for_gender="female")
        assert passes_preference_filters(user_a, user_b) is False

    def test_passes_preference_filters_age_out_of_range(self) -> None:
        """Test age filter fails."""
        user_a = create_test_user_profile(age=22, min_age=25, max_age=35)
        user_b = create_test_user_profile(age=40, min_age=20, max_age=30)
        assert passes_preference_filters(user_a, user_b) is False

    def test_passes_preference_filters_distance_too_far(self) -> None:
        """Test distance filter fails."""
        user_a = create_test_user_profile(
            location_lat=37.7749,  # SF
            location_lon=-122.4194,
            max_distance_km=50,
        )
        user_b = create_test_user_profile(
            location_lat=34.0522,  # LA
            location_lon=-118.2437,
            max_distance_km=50,
        )
        assert passes_preference_filters(user_a, user_b) is False


class TestOverallCompatibility:
    """Test overall compatibility scoring."""

    def test_calculate_compatibility_high_score(self) -> None:
        """Test high compatibility between similar users."""
        score = calculate_compatibility(SECURE_USER_SF, SECURE_USER_SF_MALE)

        # Should have high compatibility
        assert score.total_score >= 80.0

        # Check individual components
        assert score.attachment_score == 100.0  # Both secure
        assert score.location_score == 100.0  # Very close
        assert score.interests_score > 70.0  # Similar bios
        assert score.age_score == 100.0  # In each other's range
        assert score.other_score == 100.0  # Gender preferences match

    def test_calculate_compatibility_low_score(self) -> None:
        """Test low compatibility between incompatible users."""
        score = calculate_compatibility(ANXIOUS_USER_NYC, AVOIDANT_USER_NYC)

        # Should have lower compatibility
        assert score.total_score < 70.0

        # Check attachment component
        assert score.attachment_score == 40.0  # Anxious-avoidant trap

    def test_calculate_compatibility_missing_location(self) -> None:
        """Test compatibility with missing location data."""
        score = calculate_compatibility(SECURE_USER_SF, USER_NO_LOCATION)

        # Should still calculate, with moderate location score
        assert score.total_score > 0.0
        assert score.location_score == 50.0
        assert score.distance_km is None

    def test_calculate_compatibility_empty_bio(self) -> None:
        """Test compatibility with empty bio."""
        score = calculate_compatibility(SECURE_USER_SF, USER_EMPTY_BIO)

        # Should still calculate, with moderate interest score
        assert score.total_score > 0.0
        # Empty bio gets neutral similarity score
        assert 40.0 <= score.interests_score <= 60.0

    def test_calculate_compatibility_score_range(self) -> None:
        """Test all scores are in valid 0-100 range."""
        score = calculate_compatibility(SECURE_USER_SF, SECURE_USER_SF_MALE)

        assert 0.0 <= score.total_score <= 100.0
        assert 0.0 <= score.attachment_score <= 100.0
        assert 0.0 <= score.location_score <= 100.0
        assert 0.0 <= score.interests_score <= 100.0
        assert 0.0 <= score.age_score <= 100.0
        assert 0.0 <= score.other_score <= 100.0

    def test_calculate_compatibility_returns_metadata(self) -> None:
        """Test compatibility score includes metadata."""
        score = calculate_compatibility(SECURE_USER_SF, SECURE_USER_SF_MALE)

        assert score.user_a_id == SECURE_USER_SF.user_id
        assert score.user_b_id == SECURE_USER_SF_MALE.user_id
        assert score.attachment_styles == ("secure", "secure")
        assert score.distance_km is not None
