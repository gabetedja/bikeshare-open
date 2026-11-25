# Exercise 4 — Target transformations for HGB

Run from the repository root with the pinned project environment:

```bash
OMP_NUM_THREADS=2 .venv/bin/python -m experiments.target_transform_validation
```

The experiment rebuilds the official features in memory. It filters the raw rows through the validation cutoff before feature construction, fits on the 348 retained 2011 dates, and scores the 182 dates in January–June 2012. All three HGB runs use identical features, estimator settings, and dates. Results are printed to stdout. The official count-scale pipeline and `reports/metrics.json` remain the baseline.

## Validation results

| Model or target | R² | MAE (rides/day) |
| --- | ---: | ---: |
| Training mean | −0.9318 | 2002.2 |
| Yesterday's count | 0.4507 | 900.6 |
| Ridge, count | 0.6439 | 836.5 |
| HGB, count | 0.2448 | 1272.6 |
| HGB, additive residual | 0.7199 | 721.2 |
| HGB, demand ratio | 0.7520 | 677.8 |

## Choice and scientific rationale

Use the **demand ratio** for the separate experiment. Let *m(t)* be the mean observed count from calendar days *t−7* through *t−1*. The existing feature builder reindexes to a daily calendar and shifts counts by one day before rolling. The experiment requires a finite positive mean for every included date.

Train HGB on `cnt / m(t)` and multiply its predicted ratio by `m(t)`. The additive alternative trains on `cnt - m(t)` and adds back `m(t)`. Both inverses are applied before computing R² and MAE against observed ride counts. The current day's count is used as the training outcome and for scoring. The inverse uses only the previous week's observed counts, so it assumes those counts are available when issuing each daily forecast.

An adaptive local level lets the count prediction scale up as ridership grows, while the trees learn deviations around that level. Mean daily counts rose from 3493.5 in training to 5152.1 in validation, while mean ratios moved from 1.0153 to 1.0299. The additive residual also improved both metrics, supporting the value of accounting for the recent demand level. The ratio performed best here, consistent with deviations scaling with the demand level.

The ratio improved on count HGB by 0.5072 R² and 594.8 rides/day MAE, and beat Ridge by 0.1081 R² and 158.7 rides/day MAE. These are meaningful differences on this validation period. The comparison provides no uncertainty estimate, and choosing among candidates on one validation period leaves generalization unverified.
