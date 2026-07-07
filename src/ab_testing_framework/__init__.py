"""Split Testing Suite — public API.

Quick start::

    from ab_testing_framework import run_ab_test, bayesian_test, correct_pvalues

    # Standard frequentist test
    result = run_ab_test(visitors_a=10_000, conversions_a=450,
                         visitors_b=10_000, conversions_b=520)
    print(result.decision)           # Reject H₀
    print(result.srm.srm_detected)   # False

    # Bayesian complement
    from ab_testing_framework.validation import validate_input
    exp   = validate_input(10_000, 450, 10_000, 520)
    bayes = bayesian_test(exp)
    print(f"P(B > A) = {bayes.prob_b_beats_a:.1%}")

    # Multiple testing correction
    raw_pvalues = [0.03, 0.048, 0.20, 0.001]
    corrected   = correct_pvalues(raw_pvalues, method="benjamini_hochberg")
    print(corrected.rejected)        # (True, False, False, True)
"""

from .analysis import AbTestResult, run_ab_test
from .bayesian import BayesianResult, bayesian_test
from .chi_square import ChiSquareResult, perform_chi_square_test
from .confidence_interval import ConfidenceInterval, calculate_ci
from .data_loader import load_data
from .effect_size import EffectSizeResult, calculate_effect_size
from .metrics import ConversionMetrics, calculate_metrics
from .multiple_testing import MultipleTestingResult, correct_pvalues
from .power_analysis import PowerAnalysisResult, analyze_power, estimate_power, estimate_sample_size
from .report_generator import generate_markdown_report, generate_summary, save_report
from .sequential import SequentialResult, sequential_test
from .srm import SRMResult, check_srm
from .validation import ExperimentInput, validate_input
from .visualization import bar_chart, confidence_plot, distribution_plot, histogram, z_score_plot
from .z_test import ZTestResult, perform_z_test

__all__ = [
    # core
    "AbTestResult",
    "run_ab_test",
    # bayesian
    "BayesianResult",
    "bayesian_test",
    # chi-square
    "ChiSquareResult",
    "perform_chi_square_test",
    # confidence interval
    "ConfidenceInterval",
    "calculate_ci",
    # data
    "load_data",
    # effect size
    "EffectSizeResult",
    "calculate_effect_size",
    # metrics
    "ConversionMetrics",
    "calculate_metrics",
    # multiple testing
    "MultipleTestingResult",
    "correct_pvalues",
    # power
    "PowerAnalysisResult",
    "analyze_power",
    "estimate_power",
    "estimate_sample_size",
    # reporting
    "generate_markdown_report",
    "generate_summary",
    "save_report",
    # sequential
    "SequentialResult",
    "sequential_test",
    # srm
    "SRMResult",
    "check_srm",
    # validation
    "ExperimentInput",
    "validate_input",
    # visualization
    "bar_chart",
    "confidence_plot",
    "distribution_plot",
    "histogram",
    "z_score_plot",
    # z-test
    "ZTestResult",
    "perform_z_test",
]
