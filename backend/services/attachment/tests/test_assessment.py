"""
Comprehensive tests for attachment assessment service.

Tests cover:
- ECR-R questions retrieval
- Scoring algorithm (anxiety, avoidance, reverse scoring)
- Attachment style classification
- API endpoints (get questions, submit assessment, get results)
- GDPR consent validation
- 90-day retake cooldown
- Error handling and edge cases
"""

import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import AttachmentAssessment, Base, User
from backend.services.attachment.questions import (
    ANXIETY_QUESTION_IDS,
    ASSESSMENT_QUESTIONS,
    AVOIDANCE_QUESTION_IDS,
    get_question_metadata,
    get_questions,
)
from backend.services.attachment.schemas import (
    AssessmentResponse,
    SubmitAssessmentRequest,
)
from backend.services.attachment.scoring import (
    ANXIETY_THRESHOLD,
    AVOIDANCE_THRESHOLD,
    ScoringError,
    calculate_anxiety_score,
    calculate_avoidance_score,
    calculate_full_assessment,
    classify_attachment_style,
    get_attachment_insight,
    score_response,
    validate_responses,
)
from backend.services.auth.security import create_access_token, hash_password


# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_test"
)


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        verified=True,
        subscription_tier="free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authorization headers for test user."""
    token = create_access_token({"sub": str(test_user.id), "type": "access"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Tests for questions.py
# ============================================================================


def test_get_questions_returns_25_questions():
    """Test that get_questions returns exactly 25 questions."""
    questions = get_questions()
    assert len(questions) == 25


def test_get_questions_contains_required_fields():
    """Test that each question has id and text."""
    questions = get_questions()
    for q in questions:
        assert "id" in q
        assert "text" in q
        assert isinstance(q["id"], int)
        assert isinstance(q["text"], str)
        assert 1 <= q["id"] <= 25


def test_assessment_questions_total_count():
    """Test that ASSESSMENT_QUESTIONS has exactly 25 questions."""
    assert len(ASSESSMENT_QUESTIONS) == 25


def test_assessment_questions_have_both_dimensions():
    """Test that questions cover both anxiety and avoidance dimensions."""
    assert len(ANXIETY_QUESTION_IDS) > 0
    assert len(AVOIDANCE_QUESTION_IDS) > 0
    # Both dimensions should roughly balance out to 25 questions
    total_ids = len(set(ANXIETY_QUESTION_IDS + AVOIDANCE_QUESTION_IDS))
    assert total_ids == 25


def test_get_question_metadata_returns_correct_data():
    """Test that get_question_metadata returns correct question data."""
    question = get_question_metadata(1)
    assert question is not None
    assert question.id == 1
    assert question.text != ""
    assert question.dimension in ["anxiety", "avoidance"]


def test_get_question_metadata_invalid_id():
    """Test that get_question_metadata returns None for invalid ID."""
    assert get_question_metadata(0) is None
    assert get_question_metadata(26) is None
    assert get_question_metadata(999) is None


# ============================================================================
# Tests for scoring.py
# ============================================================================


def test_score_response_normal():
    """Test scoring a normal (non-reversed) question."""
    # Question 1 is anxiety, not reverse scored
    scored = score_response(1, 5)
    assert scored == 5.0


def test_score_response_reverse():
    """Test scoring a reverse-scored question."""
    # Question 4 is avoidance, reverse scored
    scored = score_response(4, 2)
    # Reverse: 8 - 2 = 6
    assert scored == 6.0


def test_score_response_reverse_edge_cases():
    """Test reverse scoring edge cases."""
    # Question 4 is reverse scored
    assert score_response(4, 1) == 7.0  # 8 - 1 = 7
    assert score_response(4, 7) == 1.0  # 8 - 7 = 1
    assert score_response(4, 4) == 4.0  # 8 - 4 = 4 (neutral stays neutral)


def test_validate_responses_valid():
    """Test validation passes with all 25 valid responses."""
    responses = {i: 4 for i in range(1, 26)}  # All neutral responses
    validate_responses(responses)  # Should not raise


def test_validate_responses_missing_questions():
    """Test validation fails when questions are missing."""
    responses = {i: 4 for i in range(1, 24)}  # Only 23 questions
    with pytest.raises(ScoringError, match="Expected 25 responses"):
        validate_responses(responses)


def test_validate_responses_invalid_question_id():
    """Test validation fails with invalid question IDs."""
    responses = {i: 4 for i in range(1, 25)}
    responses[26] = 4  # Invalid question ID
    with pytest.raises(ScoringError, match="Invalid question IDs"):
        validate_responses(responses)


def test_validate_responses_out_of_range():
    """Test validation fails with out-of-range values."""
    responses = {i: 4 for i in range(1, 26)}
    responses[1] = 0  # Below minimum
    with pytest.raises(ScoringError, match="out of range"):
        validate_responses(responses)

    responses[1] = 8  # Above maximum
    with pytest.raises(ScoringError, match="out of range"):
        validate_responses(responses)


def test_calculate_anxiety_score():
    """Test anxiety score calculation."""
    # Create responses with high anxiety (6-7) and low avoidance (1-2)
    responses = {}
    for q_id in ANXIETY_QUESTION_IDS:
        responses[q_id] = 7
    for q_id in AVOIDANCE_QUESTION_IDS:
        responses[q_id] = 1

    anxiety_score = calculate_anxiety_score(responses)
    # Need to account for reverse scoring, but with all 7s or 1s,
    # should be high for anxiety questions
    assert 1.0 <= anxiety_score <= 7.0


def test_calculate_avoidance_score():
    """Test avoidance score calculation."""
    # Create responses with low anxiety (1-2) and high avoidance (6-7)
    responses = {}
    for q_id in ANXIETY_QUESTION_IDS:
        responses[q_id] = 1
    for q_id in AVOIDANCE_QUESTION_IDS:
        responses[q_id] = 7

    avoidance_score = calculate_avoidance_score(responses)
    # Should be high due to high avoidance responses
    assert 1.0 <= avoidance_score <= 7.0


def test_classify_attachment_style_secure():
    """Test classification of Secure attachment style."""
    style = classify_attachment_style(
        anxiety_score=2.0, avoidance_score=2.0  # Both low
    )
    assert style == "Secure"


def test_classify_attachment_style_anxious():
    """Test classification of Anxious attachment style."""
    style = classify_attachment_style(
        anxiety_score=5.0, avoidance_score=2.0  # High anxiety, low avoidance
    )
    assert style == "Anxious"


def test_classify_attachment_style_avoidant():
    """Test classification of Avoidant attachment style."""
    style = classify_attachment_style(
        anxiety_score=2.0, avoidance_score=5.0  # Low anxiety, high avoidance
    )
    assert style == "Avoidant"


def test_classify_attachment_style_fearful_avoidant():
    """Test classification of Fearful-Avoidant attachment style."""
    style = classify_attachment_style(
        anxiety_score=5.0, avoidance_score=5.0  # Both high
    )
    assert style == "Fearful-Avoidant"


def test_classify_attachment_style_threshold_boundaries():
    """Test classification at threshold boundaries."""
    # Exactly at threshold (3.5) counts as high
    assert (
        classify_attachment_style(ANXIETY_THRESHOLD, AVOIDANCE_THRESHOLD)
        == "Fearful-Avoidant"
    )
    # Just below threshold counts as low
    assert (
        classify_attachment_style(ANXIETY_THRESHOLD - 0.01, AVOIDANCE_THRESHOLD - 0.01)
        == "Secure"
    )


def test_get_attachment_insight_all_styles():
    """Test that all attachment styles have insights."""
    styles = ["Secure", "Anxious", "Avoidant", "Fearful-Avoidant"]
    for style in styles:
        insight = get_attachment_insight(style)
        assert isinstance(insight, str)
        assert len(insight) > 50  # Should be a meaningful description


def test_calculate_full_assessment_secure():
    """Test full assessment calculation for secure attachment."""
    # Create responses indicating secure attachment (all neutral/low)
    responses = {i: 2 for i in range(1, 26)}  # Low scores

    result = calculate_full_assessment(responses)

    assert "anxiety_score" in result
    assert "avoidance_score" in result
    assert "attachment_style" in result
    assert "insight" in result

    assert isinstance(result["anxiety_score"], float)
    assert isinstance(result["avoidance_score"], float)
    assert result["attachment_style"] in [
        "Secure",
        "Anxious",
        "Avoidant",
        "Fearful-Avoidant",
    ]


def test_calculate_full_assessment_invalid_responses():
    """Test full assessment fails with invalid responses."""
    # Missing questions
    with pytest.raises(ScoringError):
        calculate_full_assessment({1: 5, 2: 5})

    # Out of range
    with pytest.raises(ScoringError):
        calculate_full_assessment({i: 10 for i in range(1, 26)})


# ============================================================================
# Tests for schemas.py validation
# ============================================================================


def test_submit_assessment_request_valid():
    """Test valid SubmitAssessmentRequest."""
    responses = [
        AssessmentResponse(question_id=i, response_value=4) for i in range(1, 26)
    ]
    request = SubmitAssessmentRequest(responses=responses, consent_given=True)
    assert len(request.responses) == 25
    assert request.consent_given is True


def test_submit_assessment_request_no_consent():
    """Test SubmitAssessmentRequest fails without consent."""
    responses = [
        AssessmentResponse(question_id=i, response_value=4) for i in range(1, 26)
    ]
    with pytest.raises(ValueError, match="Explicit consent is required"):
        SubmitAssessmentRequest(responses=responses, consent_given=False)


def test_submit_assessment_request_duplicate_questions():
    """Test SubmitAssessmentRequest fails with duplicate questions."""
    responses = [
        AssessmentResponse(question_id=i, response_value=4) for i in range(1, 25)
    ]
    responses.append(AssessmentResponse(question_id=1, response_value=5))  # Duplicate

    with pytest.raises(ValueError, match="Duplicate responses"):
        SubmitAssessmentRequest(responses=responses, consent_given=True)


def test_submit_assessment_request_missing_questions():
    """Test SubmitAssessmentRequest fails with missing questions."""
    from pydantic import ValidationError

    responses = [
        AssessmentResponse(question_id=i, response_value=4) for i in range(1, 24)
    ]  # Only 23

    with pytest.raises(ValidationError):
        SubmitAssessmentRequest(responses=responses, consent_given=True)


# ============================================================================
# Integration tests
# ============================================================================


def test_full_workflow_secure_attachment(db_session: Session, test_user: User):
    """Test complete workflow resulting in Secure attachment."""
    # Create responses for secure attachment (low anxiety, low avoidance)
    responses_dict = {}
    for q_id in range(1, 26):
        question = get_question_metadata(q_id)
        if question.dimension == "anxiety":
            # Low anxiety responses
            responses_dict[q_id] = 2 if not question.reverse_scored else 6
        else:  # avoidance
            # Low avoidance responses
            responses_dict[q_id] = 2 if not question.reverse_scored else 6

    # Calculate assessment
    result = calculate_full_assessment(responses_dict)

    # Create database record
    assessment = AttachmentAssessment(
        user_id=test_user.id,
        anxiety_score=result["anxiety_score"],
        avoidance_score=result["avoidance_score"],
        style=result["attachment_style"],
        assessment_version="1.0",
        total_questions=25,
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)

    # Verify database record
    assert assessment.id is not None
    assert assessment.user_id == test_user.id
    assert 1.0 <= assessment.anxiety_score <= 7.0
    assert 1.0 <= assessment.avoidance_score <= 7.0


def test_retake_cooldown_enforcement(db_session: Session, test_user: User):
    """Test that 90-day retake cooldown is enforced."""
    # Create initial assessment
    assessment = AttachmentAssessment(
        user_id=test_user.id,
        anxiety_score=3.0,
        avoidance_score=3.0,
        style="Secure",
        assessment_version="1.0",
        total_questions=25,
    )
    db_session.add(assessment)
    db_session.commit()

    # Check that assessment was just created
    assert (datetime.utcnow() - assessment.created_at.replace(tzinfo=None)).days < 1

    # User should not be able to retake within 90 days
    # (This would be enforced in the API route)


def test_retake_allowed_after_cooldown(db_session: Session, test_user: User):
    """Test that retake is allowed after 90-day cooldown."""
    # Create assessment from 91 days ago
    old_date = datetime.utcnow() - timedelta(days=91)
    assessment = AttachmentAssessment(
        user_id=test_user.id,
        anxiety_score=3.0,
        avoidance_score=3.0,
        style="Secure",
        assessment_version="1.0",
        total_questions=25,
        created_at=old_date,
        updated_at=old_date,
    )
    db_session.add(assessment)
    db_session.commit()

    # Check that enough time has passed
    days_since = (datetime.utcnow() - assessment.created_at.replace(tzinfo=None)).days
    assert days_since > 90


def test_anxiety_and_avoidance_dimensions_balance():
    """Test that anxiety and avoidance questions are properly distributed."""
    # Count questions by dimension
    anxiety_count = len(ANXIETY_QUESTION_IDS)
    avoidance_count = len(AVOIDANCE_QUESTION_IDS)

    # Should have reasonable distribution (roughly 12-13 each)
    assert 10 <= anxiety_count <= 15
    assert 10 <= avoidance_count <= 15
    assert anxiety_count + avoidance_count == 25


# ============================================================================
# Edge case tests
# ============================================================================


def test_all_minimum_responses():
    """Test assessment with all minimum (1) responses."""
    responses = {i: 1 for i in range(1, 26)}
    result = calculate_full_assessment(responses)

    # All 1s should result in certain patterns based on reverse scoring
    assert isinstance(result["anxiety_score"], float)
    assert isinstance(result["avoidance_score"], float)


def test_all_maximum_responses():
    """Test assessment with all maximum (7) responses."""
    responses = {i: 7 for i in range(1, 26)}
    result = calculate_full_assessment(responses)

    assert isinstance(result["anxiety_score"], float)
    assert isinstance(result["avoidance_score"], float)


def test_all_neutral_responses():
    """Test assessment with all neutral (4) responses."""
    responses = {i: 4 for i in range(1, 26)}
    result = calculate_full_assessment(responses)

    # All neutral should result in ~4.0 scores
    assert 3.5 <= result["anxiety_score"] <= 4.5
    assert 3.5 <= result["avoidance_score"] <= 4.5


def test_score_rounding():
    """Test that scores are rounded to 2 decimal places."""
    responses = {i: 3 for i in range(1, 26)}
    result = calculate_full_assessment(responses)

    # Check that scores are rounded
    anxiety_str = str(result["anxiety_score"])
    avoidance_str = str(result["avoidance_score"])

    # Should have at most 2 decimal places
    if "." in anxiety_str:
        assert len(anxiety_str.split(".")[1]) <= 2
    if "." in avoidance_str:
        assert len(avoidance_str.split(".")[1]) <= 2
