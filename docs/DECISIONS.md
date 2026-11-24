# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

2026-11-23, Exercise 1: Added `cnt_roll_3`, a three-day historical demand average computed after calendar reindexing with `shift(1)` before rolling, so only past rental counts are used. HGB validation R² improved from 0.2359 to 0.2448 (+0.0089), while Ridge declined from 0.6475 to 0.6439 (−0.0036). Because neither model achieved a 0.01 R² gain, the feature is not recommended for retention in the deployed model.
