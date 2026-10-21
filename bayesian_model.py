"""
Bayesian Probability Model for Estimating Tricycle Fare Deviation Likelihood
Malolos FareWatch - College Thesis & Research Decision Support System

Research Setting:
Xentro Mall Terminal Hub / Malolos City Terminal Hub, Malolos City, Bulacan, Philippines

Bayesian Formulation:
- Event A: Fare deviation exists (True condition)
- Event ¬A: Fare deviation does not exist (Compliance / Normal)
- Evidence B: Observed fare report / evidence (Reported Fare vs Official Fare Matrix)

Bayes' Theorem:
P(A|B) = [ P(B|A) * P(A) ] / P(B)
Where:
P(B) = P(B|A)*P(A) + P(B|¬A)*P(¬A)
P(A) = Prior probability of fare deviation (Default development placeholder: 0.50)
P(B|A) = Likelihood of observing the report given that deviation exists
P(B|¬A) = Likelihood of observing the report given that deviation does NOT exist (false positive / reporting error)

NOTICE:
Development prototype parameters shown are placeholders until replaced with validated
LGU data and study-derived parameters.
"""

# Baseline development parameters as defined in thesis proposal specifications
DEFAULT_PRIOR = 0.50
DEFAULT_LIKELIHOOD_DEVIATION = 0.90
DEFAULT_LIKELIHOOD_NO_DEVIATION = 0.10

def calculate_bayesian_likelihood(reported_fare, official_fare, prior=DEFAULT_PRIOR, has_photo=False):
    """
    Computes the posterior probability of fare deviation using Bayes' Theorem.
    Takes into account fare difference and relative deviation ratio.
    
    Returns a comprehensive dictionary with step-by-step mathematical steps.
    """
    reported = float(reported_fare)
    official = float(official_fare)
    difference = round(reported - official, 2)
    
    # Base prior
    p_a = max(0.01, min(0.99, float(prior)))
    p_not_a = 1.0 - p_a
    
    if difference <= 0:
        # Case 1: Reported fare is at or below official fare (observed compliant report)
        # Likelihood of reporting <= official when deviation exists is very low
        p_b_given_a = 0.0500
        p_b_given_not_a = 0.9120
        evidence_type = "At or below official fare"
        category = "Compliant"
    else:
        # Case 2: Reported fare exceeds official fare (observed excess report)
        evidence_type = "Higher than official fare"
        category = "Deviation Reported"
        ratio = difference / official if official > 0 else 0.5
        
        # Deviation likelihood scales with relative magnitude of excess
        # Example benchmarks from study prototype:
        # +₱5 on ₱20 (ratio 0.25) -> posterior ~ 72.4%
        # +₱10 on ₱20 (ratio 0.50) -> posterior ~ 91.3%
        # Photos provide higher evidentiary weight
        if ratio <= 0.10:
            p_b_given_a = 0.5800
            p_b_given_not_a = 0.4200
        elif ratio <= 0.25:
            # Interpolate to ~72.4% at ratio 0.25
            factor = (ratio - 0.10) / 0.15
            p_b_given_a = 0.5800 + factor * (0.7240 - 0.5800)
            p_b_given_not_a = 1.0 - p_b_given_a
        elif ratio <= 0.50:
            # Interpolate to ~91.3% at ratio 0.50
            factor = (ratio - 0.25) / 0.25
            p_b_given_a = 0.7240 + factor * (0.9130 - 0.7240)
            p_b_given_not_a = 1.0 - p_b_given_a
        else:
            # High excess (> 50% above matrix)
            p_b_given_a = min(0.9650, 0.9130 + (ratio - 0.50) * 0.10)
            p_b_given_not_a = max(0.0350, 1.0 - p_b_given_a)
            
        # If verified photo evidence is attached, confidence increases slightly
        if has_photo:
            p_b_given_a = min(0.9850, p_b_given_a * 1.03)
            p_b_given_not_a = max(0.0150, p_b_given_not_a * 0.90)

    # Compute marginal probability of evidence P(B)
    # P(B) = P(B|A)*P(A) + P(B|¬A)*P(¬A)
    p_b = (p_b_given_a * p_a) + (p_b_given_not_a * p_not_a)
    
    # Compute posterior probability P(A|B)
    p_a_given_b = (p_b_given_a * p_a) / p_b if p_b > 0 else 0.0
    
    # Clamping for safety
    p_a_given_b = max(0.0, min(1.0, p_a_given_b))
    percentage = round(p_a_given_b * 100, 1)
    
    # Likelihood level classification
    if percentage < 40.0:
        level = "Low"
        badge_class = "badge-low"
    elif percentage < 70.0:
        level = "Medium"
        badge_class = "badge-medium"
    else:
        level = "High"
        badge_class = "badge-high"
        
    return {
        "reported_fare": reported,
        "official_fare": official,
        "fare_difference": difference,
        "evidence_type": evidence_type,
        "category": category,
        "prior": round(p_a, 4),
        "prior_not_a": round(p_not_a, 4),
        "likelihood_deviation": round(p_b_given_a, 4),
        "likelihood_no_deviation": round(p_b_given_not_a, 4),
        "marginal_evidence": round(p_b, 4),
        "posterior": round(p_a_given_b, 4),
        "percentage": percentage,
        "level": level,
        "badge_class": badge_class,
        "is_deviation": difference > 0,
        "has_photo": has_photo,
        "development_notice": "Development Model Parameters: Final Bayesian parameters must be established and justified using the thesis methodology and validated data."
    }
