# A/B Testing Framework

A statistically sound A/B testing framework for comparing a control and a treatment variant, estimating lift, running hypothesis tests, computing confidence intervals, and presenting the result in a Streamlit dashboard.

## What it does

- Calculates conversion rates for both variants.
- Runs a two-proportion z-test.
- Estimates a 95% confidence interval for the lift.
- Computes effect size, including Cohen's h.
- Generates Plotly visualizations.
- Produces a readable experiment report.

## Project Layout

- `src/ab_testing_framework/` core statistical engine
- `dashboard/app.py` Streamlit dashboard
- `tests/` automated checks
- `data/sample_experiment.csv` example dataset
- `notebooks/` starter analysis notebooks

## Run It

Install runtime dependencies:

```bash
pip install -r requirements.txt
```

Or install the package in editable mode (recommended for development — also removes the need for any `sys.path` workarounds):

```bash
pip install -e ".[dev]"
```

Run the dashboard:

```bash
streamlit run dashboard/app.py
```

Run tests:

```bash
pytest
```

## Example Input

The sample dataset uses:

- Control visitors: 10000
- Control conversions: 450
- Treatment visitors: 10000
- Treatment conversions: 520

## Notes

- The framework uses a two-sided two-proportion z-test to evaluate whether treatment and control differ in conversion rate.
- A positive confidence interval lower bound is required (alongside p < α) to trigger a "Deploy" recommendation.
- The dashboard accepts manual inputs or a CSV upload.
