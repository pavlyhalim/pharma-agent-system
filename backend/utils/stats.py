"""
Statistical utilities for meta-analysis and confidence intervals.
"""

import numpy as np
from scipy import stats
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def wilson_score_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a proportion.

    This is more accurate than the normal approximation, especially for
    small sample sizes or extreme proportions.

    Args:
        successes: Number of successes (e.g., non-responders)
        trials: Total number of trials (e.g., total patients)
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 0.0)

    p = successes / trials
    z = stats.norm.ppf((1 + confidence) / 2)

    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return (lower, upper)


def pooled_proportion(
    proportions: List[float],
    sample_sizes: List[int],
    method: str = "inverse_variance"
) -> Tuple[float, Tuple[float, float]]:
    """
    Calculate pooled proportion across multiple studies.

    Args:
        proportions: List of proportions from each study
        sample_sizes: List of sample sizes for each study
        method: Weighting method ("inverse_variance" or "sample_size")

    Returns:
        Tuple of (pooled_proportion, (lower_ci, upper_ci))
    """
    if not proportions or not sample_sizes:
        return (0.0, (0.0, 0.0))

    proportions = np.array(proportions)
    sample_sizes = np.array(sample_sizes)

    # Calculate weights
    if method == "inverse_variance":
        # Weight by inverse variance: w_i = 1 / var(p_i)
        variances = proportions * (1 - proportions) / sample_sizes
        variances = np.maximum(variances, 1e-10)  # Avoid division by zero
        weights = 1 / variances
    else:  # sample_size
        weights = sample_sizes

    weights = weights / weights.sum()  # Normalize

    # Pooled estimate
    pooled = np.sum(weights * proportions)

    # Pooled variance (simplified for fixed-effect model)
    total_n = sample_sizes.sum()
    pooled_variance = pooled * (1 - pooled) / total_n

    # Confidence interval using normal approximation
    z = stats.norm.ppf(0.975)  # 95% CI
    margin = z * np.sqrt(pooled_variance)

    lower = max(0.0, pooled - margin)
    upper = min(1.0, pooled + margin)

    return (pooled, (lower, upper))


def random_effects_meta_analysis(
    effects: List[float],
    variances: List[float],
    confidence: float = 0.95
) -> Dict[str, Any]:
    """
    Random-effects meta-analysis using DerSimonian-Laird method.

    Args:
        effects: List of effect sizes (e.g., log odds ratios, proportions)
        variances: List of within-study variances
        confidence: Confidence level

    Returns:
        Dictionary with pooled effect, CI, tau^2, I^2, etc.
    """
    effects = np.array(effects)
    variances = np.array(variances)
    n = len(effects)

    if n == 0:
        return {"pooled_effect": None, "ci": (None, None), "tau2": None, "I2": None}

    # Fixed-effect weights
    weights_fe = 1 / variances

    # Q statistic (heterogeneity)
    pooled_fe = np.sum(weights_fe * effects) / np.sum(weights_fe)
    Q = np.sum(weights_fe * (effects - pooled_fe)**2)

    # Between-study variance (tau^2) using DerSimonian-Laird
    df = n - 1
    C = np.sum(weights_fe) - np.sum(weights_fe**2) / np.sum(weights_fe)
    tau2 = max(0, (Q - df) / C)

    # I^2 statistic (percentage of variation due to heterogeneity)
    I2 = max(0, (Q - df) / Q) * 100 if Q > 0 else 0

    # Random-effects weights
    weights_re = 1 / (variances + tau2)

    # Pooled effect
    pooled_re = np.sum(weights_re * effects) / np.sum(weights_re)
    pooled_variance = 1 / np.sum(weights_re)

    # Confidence interval
    z = stats.norm.ppf((1 + confidence) / 2)
    margin = z * np.sqrt(pooled_variance)
    lower = pooled_re - margin
    upper = pooled_re + margin

    return {
        "pooled_effect": pooled_re,
        "ci": (lower, upper),
        "tau2": tau2,
        "I2": I2,
        "Q": Q,
        "p_heterogeneity": 1 - stats.chi2.cdf(Q, df) if df > 0 else None,
        "n_studies": n
    }


def calculate_heterogeneity(
    effects: List[float],
    variances: List[float]
) -> Dict[str, float]:
    """
    Calculate heterogeneity statistics (I^2, tau^2, Q).

    Args:
        effects: List of effect sizes
        variances: List of within-study variances

    Returns:
        Dictionary with heterogeneity metrics
    """
    result = random_effects_meta_analysis(effects, variances)
    return {
        "I2": result["I2"],
        "tau2": result["tau2"],
        "Q": result["Q"],
        "p_value": result["p_heterogeneity"]
    }


def convert_effect_sizes(
    value: float,
    from_type: str,
    to_type: str,
    baseline_risk: Optional[float] = None
) -> Optional[float]:
    """
    Convert between different effect size measures.

    Args:
        value: Effect size value
        from_type: Source type (OR, RR, HR, risk_difference, proportion)
        to_type: Target type
        baseline_risk: Baseline risk/proportion (needed for some conversions)

    Returns:
        Converted effect size or None if conversion not supported
    """
    # Log transformations
    if from_type in ["OR", "RR", "HR"] and to_type == "log_OR":
        return np.log(value) if value > 0 else None

    # OR to probability (requires baseline odds)
    if from_type == "OR" and to_type == "probability" and baseline_risk is not None:
        baseline_odds = baseline_risk / (1 - baseline_risk)
        new_odds = baseline_odds * value
        return new_odds / (1 + new_odds)

    # RR to probability (requires baseline risk)
    if from_type == "RR" and to_type == "probability" and baseline_risk is not None:
        return baseline_risk * value

    # Risk difference to probability
    if from_type == "risk_difference" and to_type == "probability" and baseline_risk is not None:
        return baseline_risk + value

    # Identity
    if from_type == to_type:
        return value

    logger.warning(f"Conversion from {from_type} to {to_type} not implemented")
    return None


def assess_data_quality(
    sample_size: int,
    study_design: str,
    has_randomization: bool,
    has_blinding: bool,
    has_intent_to_treat: bool
) -> Tuple[str, List[str]]:
    """
    Assess quality of clinical data.

    Args:
        sample_size: Number of participants
        study_design: Type of study (RCT, observational, etc.)
        has_randomization: Whether randomized
        has_blinding: Whether blinded
        has_intent_to_treat: Whether ITT analysis

    Returns:
        Tuple of (quality_level, list_of_concerns)
    """
    concerns = []

    # Sample size
    if sample_size < 50:
        concerns.append("Very small sample size (<50)")
    elif sample_size < 100:
        concerns.append("Small sample size (<100)")

    # Study design
    if study_design.lower() not in ["rct", "randomized controlled trial"]:
        concerns.append("Not an RCT")

    # Methodological quality
    if not has_randomization:
        concerns.append("No randomization")

    if not has_blinding:
        concerns.append("No blinding")

    if not has_intent_to_treat:
        concerns.append("No intent-to-treat analysis")

    # Overall assessment
    if len(concerns) == 0 and sample_size >= 200:
        quality = "high"
    elif len(concerns) <= 2 and sample_size >= 100:
        quality = "moderate"
    else:
        quality = "low"

    return (quality, concerns)


def calculate_nnt(
    treatment_response: float,
    control_response: float
) -> Optional[int]:
    """
    Calculate Number Needed to Treat (NNT).

    Args:
        treatment_response: Response rate in treatment group
        control_response: Response rate in control group

    Returns:
        NNT (absolute value) or None if not calculable
    """
    risk_difference = treatment_response - control_response

    if abs(risk_difference) < 0.001:  # Essentially zero
        return None

    nnt = 1 / abs(risk_difference)
    return int(np.round(nnt))
