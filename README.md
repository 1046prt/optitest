# Split Testing Suite

Compare two variants. Measure lift. Make a confident decision.

---

## What it does

Takes visitor and conversion counts for a control and a treatment group, then runs a complete frequentist analysis:

- Two-proportion z-test (two-sided, one-sided, or directional)
- 95% confidence interval for the lift
- Effect size — Cohen's h
- Power analysis and required sample size
- Decision recommendation with plain-English explanation
- Exportable Markdown and JSON reports

Everything is surfaced through a Streamlit dashboard or callable directly from Python.

---

## Getting started

```bash
# install
pip install -r requirements.txt

# run the dashboard
streamlit run dashboard/app.py

# run tests
pytest
```

For development, install in editable mode instead:

```bash
pip install -e ".[dev]"
```

---

## CSV formats

The dashboard accepts two CSV shapes.

**Aggregated** — one row per segment, or a single total row:

```
visitors_a,conversions_a,visitors_b,conversions_b
10000,450,10000,520
```

**Per-user** — one row per visitor:

```
variant,converted
A,0
A,1
B,1
B,0
```

Sample files are in `data/`.

---

## Python API

```python
from ab_testing_framework import run_ab_test

result = run_ab_test(
    visitors_a=10000, conversions_a=450,
    visitors_b=10000, conversions_b=520,
    alpha=0.05,
    alternative="two-sided",   # "larger" | "smaller" | "two-sided"
)

print(result.decision)          # Reject H₀
print(result.recommendation)    # Deploy Version B. Conversion increased by 15.6%...
print(result.z_test.p_value)    # 0.0212
print(result.power_analysis.power)  # 0.xx
```

---

## Project layout

```
src/ab_testing_framework/   statistical engine
  analysis.py               orchestrator — run_ab_test()
  z_test.py                 two-proportion z-test
  confidence_interval.py    Wald CI for lift
  effect_size.py            Cohen's h, relative lift
  power_analysis.py         observed power + sample size planning
  metrics.py                conversion rate calculations
  validation.py             input validation
  data_loader.py            CSV parsing (aggregated + per-user)
  report_generator.py       Markdown and JSON export
  visualization.py          Plotly charts (dark theme)

dashboard/app.py            Streamlit front-end
tests/test_framework.py     49 pytest tests
notebooks/                  EDA → Z-test → CI → Effect size
data/                       sample CSVs
reports/                    generated reports (git-ignored)
```

---

## Requirements

Python 3.10+ · numpy · pandas · scipy · statsmodels · plotly · streamlit

---

## Decision logic

A "Deploy" recommendation requires two conditions to both be true:

1. p-value < α
2. The confidence interval lower bound > 0

Passing the p-value threshold alone is not sufficient — the CI must fully exclude zero.
