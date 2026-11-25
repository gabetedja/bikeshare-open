# DSC 180A Assignment 7, Exercise 3 — Peer leakage audit

## Teammate's GitHub repository

[Azi23333/bikeshare-open](https://github.com/Azi23333/bikeshare-open), from the local checkout's `origin`. I audited `../bikeshare-peer-audit` at commit `f63b5dc`.

## Incomplete Claude Code leakage-auditor run

Claude Code inspected the peer repository, but repeated Ollama API errors prevented it from producing a final report. Its verification script reportedly found that `cnt_lag_1` equaled `cnt` on every processed row. That result was unverified and conflicted with the source, which shifts the target by one row after reindexing to a daily calendar.

**Transcript from the incomplete Claude Code run.** The excerpt includes the script's reported finding and an Ollama API retry.

```text
❯ Audit the repository located at ../bikeshare-peer-audit, not the current bikeshare-open repository.

  Check for target leakage, temporal-split violations, missing baselines, and reproducibility problems.

  Verify findings using the actual source code. Report only issues that could change numerical results or invalidate a methodological conclusion.

  Include supporting file paths and line numbers. Do not modify either repository or execute unreviewed project code.

  Give me your complete audit findings.

  Thought for 14m 39s, searched for 1 pattern, read 8 files

Let me now check the metrics file and any model output to verify baseline reporting:

  Thought for 20m 3s, read 1 file, ran 1 shell command · 1 failed

Now let me verify key claims about the data and code:

⏺ Bash(cd /Users/gabrieltedja/Documents/DSC180A/bikeshare-peer-audit && python -I << 'EOF'
  import sys
  sys.path.insert(0, '.')

  import pandas as pd
  from src.config import FORBIDDEN, TARGET
  from src.features import feature_columns, build_features, encode_weather

  df = pd.read_csv('data/raw/bike_daily.csv')
  TARGET = "cnt"

  print("=" * 60)
  print("CHECK 1: TARGET LEAKAGE (casual + registered == cnt)")
  print("=" * 60)
  diff = df["casual"] + df["registered"] - df[TARGET]
  print(f"Max absolute difference: {abs(diff).max()}")
  print(f"All rows match exactly: {(df['casual'] + df['registered'] == df[TARGET]).all()}")

  raw_df = df.reset_index(drop=True)
  feats = build_features(raw_df)
  final_cols = feature_columns(feats)
  print(f"\nFeature columns returned by feature_columns(): {final_cols}")

  print("\n" + "=" * 60)
  print("CHECK 1.5 CONTINUED: Verify no derived target column exists")
  print("=" * 60)
  for col in final_cols:
      if "cnt" in col.lower() and col not in [TARGET, f"{TARGET}_lag_1", f"{TARGET}_lag_7", f"{TARGET}_roll_7", f"{TARGET}_roll_range_7"]:
          print(f"WARNING: Unusual cnt-derived column found: {col}")

  print("\n" + "=" * 60)
  print("CHECK 1.6: Direct check - does the feature set contain 'cnt'?")
  print("=" * 60)
  if "cnt" in final_cols:
      print("ERROR: The target column 'cnt' is directly in the feature set!")
  else:
      print("OK: Target column not in features")

  print("\n" + "=" * 60)
  print("CHECK 1.7: Verify lagged columns are NOT equal to target")
  print("=" * 60)
  if "cnt_lag_1" in final_cols:
      if (feats["cnt_lag_1"] == feats[TARGET]).all():
          print("ERROR: cnt_lag_1 equals target directly - this is leakage!")
      else:
          sample_idx = 10
          if feats.iloc[sample_idx]["cnt_lag_1"] != feats.iloc[sample_idx][TARGET]:
              print(f"OK: cnt_lag_1[{sample_idx}] differs from target (lag works correctly)")

  print("\nAll leakage checks completed.")
  EOF
  )
============================================================
CHECK 1: TARGET LEAKAGE (casual + registered == cnt)
============================================================
Max absolute difference: 0
All rows match exactly: True

Feature columns returned by feature_columns(): ['temp', 'atemp', 'hum', 'windspeed', 'dayofweek', 'is_weekend', 'is_holiday', 'is_workday', 'month_sin', 'month_cos', 'weather_severity', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7', 'cnt_roll_range_7']

============================================================
CHECK 1.5 CONTINUED: Verify no derived target column exists
============================================================

============================================================
CHECK 1.6: Direct check - does the feature set contain 'cnt'?
============================================================
OK: Target column not in features

============================================================
CHECK 1.7: Verify lagged columns are NOT equal to target
============================================================
ERROR: cnt_lag_1 equals target directly - this is leakage!

All leakage checks completed.

✻ API error · retrying… · attempt 2/10
```

## Independent verification (Codex)

Codex used our project's virtual environment (NumPy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1) to load the peer's tracked CSV and run the peer's feature builder in memory. The CSV's SHA-256 matched the configured digest. The checkout had no processed Parquet, so the check covers a fresh build from the audited commit. The exact data or script that produced Claude's reported result could not be verified.

The peer findings below come from Codex's independent verification. The separate self-audit and its provenance are recorded at the end of this document.

### Target leakage

For every retained feature date, Codex looked up the raw count separately at that date and one calendar day earlier, using unique date keys. The rebuilt target matched the raw same-day count on all 714 rows. The lag matched the previous day's raw count on **714/714** rows and the same-day raw count on **0/714** rows. For example, on 2011-01-10 the lag was 822 and the same-day count was 1,321. The alleged current-target leakage is a false positive for this checkout.

The seven-day lag, trailing mean, and trailing range also matched values computed independently from the raw counts on the appropriate prior calendar dates. `casual + registered == cnt` on all 728 raw rows, but the selected model inputs contained neither component, the target itself, nor any other configured forbidden column. Every raw column was classified and the 15 selected inputs matched the saved metrics. The feature selector still admits any numeric column outside the denylist, so running the raw-schema test matters when inputs change. That is a future schema-drift risk, with no observed effect on these scores.

### Temporal split and baselines

| Split | First retained date | Last retained date | Rows |
| --- | --- | --- | ---: |
| Train | 2011-01-10 | 2011-12-31 | 348 |
| Validation | 2012-01-01 | 2012-06-30 | 182 |
| Test | 2012-07-01 | 2012-12-31 | 184 |

The split code uses disjoint date cutoffs, and the training loop fits every model on training rows only, including Ridge's scaler. Prior observed counts across split boundaries are valid for a rolling one-day-ahead evaluation. A forecast issued before same-day weather is observed would need forecast-time weather inputs or a separate evaluation. The saved scores are conditional on the weather inputs used here. The peer report says feature selection used validation. The code and artifacts cannot independently establish when the authors first looked at held-out scores.

Both the training-mean and yesterday-count baselines report R² and MAE for validation and test. The in-memory rerun matched both baselines and Ridge to the published precision. Ridge led persistence on test R² (0.6279 vs. 0.5099), while persistence had lower test MAE (840.1 vs. 863.1 rides). The deployment preference therefore depends on which error metric matters.

### Reproducibility

The checkout provides a tracked raw CSV, pinned dependencies, a seeded HGB estimator, and commands for the full pipeline. The checksum guard runs during the ingest command. Calling `load_raw()` directly checks columns and row count but does not enforce the checksum.

The in-memory HGB rerun still differed from the saved report with the README's `OMP_NUM_THREADS=2` setting. The cause is unresolved.

| Split | Saved R² / MAE | Recomputed R² / MAE |
| --- | ---: | ---: |
| Validation | 0.0711 / 1402.3 | 0.0651 / 1411.8 |
| Test | −0.6792 / 2087.9 | −0.6392 / 2067.2 |

This is a confirmed reproducibility discrepancy for the exact HGB scores. In both runs, HGB had negative test R², beat the training mean, and trailed persistence and Ridge. The separate Exercise 4 target-ratio experiment was outside this rerun.

## My provisional verdict

I would provisionally accept the peer's one-day-ahead comparison. The date-aligned evidence rules out the reported lag leakage for the audited commit, and the split and baselines support the main comparison. I would qualify the reported HGB scores until the discrepancy is explained. I provisionally favor persistence if typical absolute error and operational simplicity matter most, and Ridge if larger errors should carry more weight. This verdict assumes yesterday's count and the weather inputs are available at forecast time.

## Self-audit fallback (Codex)

The Claude Agent SDK connectivity probe succeeded. The full self-audit against local Ollama timed out after 119.03 seconds with exit code 124 and an `unrecognized_model` warning. It produced no candidate JSONL. The later 15-minute attempt was stopped at my request before it returned a record.

`reports/audit.jsonl` contains one independently verified Codex self-audit record for commit `d3ef964`. It uses the runner's report schema and includes provenance identifying Codex as the generator and the SDK audit as incomplete.

Codex rebuilt the features from the unchanged raw CSV and joined the retained rows to raw counts by date. All 714 one-day lags matched the previous calendar day's count, and zero matched the current day's count. The seven-day lag and both trailing means matched independent prior-day calculations. None of the 15 selected features was forbidden. The splits were disjoint and chronological, with 348 training, 182 validation, and 184 test rows. Training-only refits of all four official models reproduced every saved validation and test R² and MAE to the reported precision.

The results assume same-day weather inputs are available at forecast issuance. The training selector also relies on the raw-schema test to flag unexpected numeric inputs before they can enter the model. Neither caveat revealed target leakage in the audited data. The substitute supplies methodology evidence. A grading requirement for a completed Claude Agent SDK run remains unmet.
