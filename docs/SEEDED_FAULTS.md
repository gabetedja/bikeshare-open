# Exercise 2 — Seeded Faults

## Fault 1: Forbidden Feature

### Intentional change
Modified feature_columns() in src/features.py to append
"casual" to the model's feature list.

This creates target leakage because casual is a component
of the target variable cnt.

### Hook stderr

```text
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/gabrieltedja/Documents/DSC180A/bikeshare-open/src/features.py:

feats =         dteday  instant  season      yr mnth  ... weather_severity cnt_lag_1  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   ...31.0  WINTER  2012.0  DEC  ...              1.0    1796.0      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'holiday', 'instant', ...})

tests/test_leakage.py:31: AssertionError
============================================ short test summary info =============================================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: forbidden columns in feature set: {'...
1 failed, 7 passed in 0.98s
```

### Failing test output

```text
$ /Users/gabrieltedja/Documents/DSC180A/bikeshare-open/.venv/bin/python -m pytest tests/test_leakage.py -q
.F......                                                                 [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'holiday', 'instant', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 7 passed in 1.37s
```

### Repair
Claude restored the original feature_columns() implementation
by removing the forbidden "casual" column.

### Repair turns
Claude repaired the fault in its first repair attempt, automatically following the hook feedback.

### Verification
All 16 tests passed after the repair.

### Git evidence
Fault commit: 001e3d7
Repair commit: 5c94115


## Fault 2: Unshifted Seven-Day Rolling Mean

### Intentional change
Modified `build_features()` in `src/features.py` by removing `.shift(1)` from the `cnt_roll_7` calculation.

Original (safe):
```python
out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
```

Faulty (leaky):
```python
out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
```

This creates target leakage because the rolling average includes the current day's `cnt`, which is the value the model is supposed to predict.

### Hook stderr
PostToolUse:Edit hook reported a problem
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/gabrieltedja/Documents/DSC180A/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:81: AssertionError
============================================ short test summary info =============================================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.float64(4389.0) == 4414.857142857143...
1 failed, 7 passed in 0.99s

### Failing test output

```text
$ /Users/gabrieltedja/Documents/DSC180A/bikeshare-open/.venv/bin/python -m pytest tests/test_leakage.py -q
.....F..                                                                 [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....428571  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1789.857143  2077.333333

[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:81: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.81s
```

### Repair
Claude restored `.shift(1)` before the seven-day rolling average, ensuring the feature uses only previous days' target values.

### Repair turns
1 repair turn. Claude restored `.shift(1)` in its first edit
after receiving the repair instruction.

### Verification
After Claude repaired the rolling-average calculation, I ran
`make test` using the project's virtual environment.

Result: 16 passed.

The corrected `cnt_roll_7` calculation excludes the current
day's target by shifting `cnt` one day before computing
the seven-day rolling average.

### Git evidence
Fault commit: c5af8af
Repair commit: 4234bbe


## Fault 3: Missing Weather Encoder Validation

### Intentional change

Modified `encode_weather()` in `src/features.py` by removing the validation that raises a `ValueError` for unknown weather labels.

The original implementation checked for labels absent from `WEATHER_ORDER` and rejected them.

The faulty implementation simply returns:

    return series.map(WEATHER_ORDER).astype(float)

Unknown labels such as `"STORMY"` now become `NaN` instead of causing an exception. Downstream `dropna()` may silently remove these rows.

### Hook stderr

No hook failure has been confirmed from the available output.

### Initial test results

After introducing the fault, I ran `make test`.

Result: 16 tests passed.

The existing tests did not detect the missing input validation, revealing a gap in test coverage.

### Regression test



### Failing test output

============================= test session starts ==============================
platform darwin -- Python 3.12.11, pytest-9.1.1, pluggy-1.7.0 -- /Users/gabrieltedja/Documents/DSC180A/bikeshare-open/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/gabrieltedja/Documents/DSC180A/bikeshare-open
plugins: anyio-4.16.0
collecting ... collected 1 item

tests/test_leakage.py::test_weather_encoder_rejects_unknown_label FAILED [100%]

=================================== FAILURES ===================================
__________________ test_weather_encoder_rejects_unknown_label __________________

    def test_weather_encoder_rejects_unknown_label():
        """encode_weather must raise ValueError for labels outside GOOD/MISTY/BAD."""
        # This tests the fault-injection from Exercise 2, Fault #3:
        # The encoder previously silently mapped unknown labels to NaN,
        # which dropna() would remove without any warning.
        unknown_label = "STORMY"
        series = pd.Series([unknown_label])
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:95: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_weather_encoder_rejects_unknown_label - Fa...
============================== 1 failed in 0.90s ===============================

### Repair
Claude restored the unknown-label validation in `encode_weather()`.
The encoder now raises `ValueError` for labels outside
`WEATHER_ORDER`, rather than silently mapping them to NaN.

### Repair turns
1 repair turn. Claude restored the validation on its first
repair attempt.

### Verification
Ran `make test` after restoring the validation.

Result: 17 passed in 2.51s.

The new regression test now passes.

### Git evidence
Fault commit: c10f11a
Regression test commit: 4021b01
Repair commit: c10e1fb
