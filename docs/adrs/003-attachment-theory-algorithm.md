# ADR-003: Attachment Theory as Core Matching Algorithm Component

## Status
Accepted

## Context
Dating platforms traditionally rely on surface-level matching criteria (age, location, interests). We want to create a psychology-informed platform that facilitates meaningful connections based on relationship compatibility.

### Traditional Matching Approaches
- Demographics (age, location, education)
- Shared interests and hobbies
- Swiping behavior and engagement patterns
- Machine learning on historical match success

### Our Requirements
- Evidence-based psychological framework
- Predictive of relationship success
- Actionable for users (self-awareness + growth)
- Differentiating factor in competitive market
- Ethically transparent and explainable

## Decision
We will use **Attachment Theory** as a core component (40% weight) of our matching algorithm, complemented by traditional factors.

### Attachment Theory Background
Developed by Bowlby and Ainsworth, attachment theory categorizes adult relationship patterns into four styles:
- **Secure** (50% of population): Comfortable with intimacy and independence
- **Anxious** (20%): Craves closeness, fears abandonment
- **Avoidant** (25%): Values independence, uncomfortable with vulnerability
- **Fearful-Avoidant** (5%): Desires closeness but fears intimacy

### Algorithm Weights
- Attachment compatibility: **40%**
- Shared interests: **25%**
- Values alignment: **20%**
- Demographics (age, location): **10%**
- Physical attractiveness ratings: **5%**

## Consequences

### Positive
- **Evidence-Based**: Decades of research support attachment theory's role in relationship success
- **Differentiation**: Unique value proposition in crowded dating market
- **User Growth**: Assessment provides self-awareness, users learn about their patterns
- **Match Quality**: Research shows secure-secure pairings have highest relationship satisfaction
- **Ethical AI**: Transparent, explainable algorithm vs. black-box ML
- **Premium Feature**: Attachment coaching can be monetized (Elite tier)

### Negative
- **Assessment Length**: 25-question ECR-R assessment may deter some users
- **Stigma Risk**: Users may feel "labeled" or judged
- **Complex Matching**: Not all combinations are equally compatible
- **Research Limitations**: Most studies on Western populations
- **False Precision**: Attachment is fluid, not fixed

### Mitigation
- Frame assessment as "relationship style" not "diagnosis"
- Emphasize growth mindset: styles can evolve
- Allow users to retake assessment quarterly
- Combine with other factors (not sole determinant)
- Clear communication: "insights for growth, not judgment"
- Offer optional attachment coaching for all users

## Technical Implementation

### Compatibility Matrix
```python
# Simplified compatibility scoring
COMPATIBILITY_MATRIX = {
    ("secure", "secure"): 1.0,        # Highest compatibility
    ("secure", "anxious"): 0.75,      # Secure can provide stability
    ("secure", "avoidant"): 0.70,     # Secure can handle space needs
    ("anxious", "anxious"): 0.50,     # Both need reassurance
    ("anxious", "avoidant"): 0.30,    # Classic trap (protest-withdraw)
    ("avoidant", "avoidant"): 0.60,   # Low intimacy but stable
    ("fearful", "secure"): 0.65,      # Secure provides safe space
    # ... full matrix with 16 combinations
}
```

### Assessment Tool
- ECR-R (Experiences in Close Relationships - Revised)
- 18 questions total (9 anxiety, 9 avoidance)
- 7-point Likert scale
- Takes 5-7 minutes to complete
- Optional: Allow manual override by user

### Privacy & Ethics
- Users choose whether to display attachment style on profile
- Clear explanation before assessment
- No negative framing (all styles are valid)
- Link to research and educational resources
- Option to opt-out and use traditional matching

## Related Decisions
- ADR-011: AI relationship coaching (extension of this decision)
- ADR-004: EU AI Act compliance (transparency requirements)

## References
- Mikulincer, M., & Shaver, P. R. (2007). *Attachment in Adulthood*
- [ECR-R Assessment Tool](https://www.psychology.sunysb.edu/attachment/measures/content/ecr-r_final.pdf)
- Hazan, C., & Shaver, P. (1987). Romantic love conceptualized as an attachment process
- Feeney, J. A. (2016). Adult romantic attachment: Developments in the study of couple relationships

## Date
2025-11-17

## Authors
- Architect Agent
- Psychology Advisory Board
- Product Owner
