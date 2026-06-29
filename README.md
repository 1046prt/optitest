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

Install dependencies:

```bash
pip install -r requirements.txt
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

- The framework uses a one-sided two-proportion z-test to evaluate whether treatment improves conversion.
- The dashboard accepts manual inputs or a CSV upload.
