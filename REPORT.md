# Capital Bikeshare demand forecast

## Results

The official pipeline forecasts total daily rides one day ahead. Models fit on 348 retained days in 2011, validate on 182 days in the first half of 2012, and test on 184 days in the second half of 2012. The table uses the saved count-scale results. MAE is in rides per day. [Official metrics](reports/metrics.json)

The raw series has a missing calendar date. The feature builder restores the daily grid before shifting counts, so a one-day lag refers to yesterday even when the previous recorded row is older. Rows that lack the required lag history are dropped. The pipeline excludes `casual` and `registered` from model inputs because their sum equals the target. The training-mean baseline estimates a fixed level using the training period. Persistence instead adapts each day by predicting yesterday's actual count.

| Model | Validation R² | Validation MAE | Test R² | Test MAE |
| --- | ---: | ---: | ---: | ---: |
| Training mean | −0.9318 | 2002.2 | −2.1441 | 2847.7 |
| Yesterday's count | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Ridge | 0.6439 | 836.5 | 0.5800 | 946.2 |
| HGB | 0.2448 | 1272.6 | −0.4507 | 1941.2 |

## Headline finding

Ridge led the official models on test R², while yesterday's count had the lowest test MAE. The count-scale HGB had negative test R² and still improved on the training-mean baseline on both metrics. The choice of model depends on how costly large errors are relative to the average absolute miss.

Mean demand rose from 3,493.5 rides per day in training to 5,152.1 in validation, about 47%. This shift helps explain why a forecast tied to the 2011 mean performs poorly and motivates an adaptive recent-demand level. A tree model fitted directly to counts can struggle to extrapolate beyond the levels represented in its training data. The aggregate scores alone cannot establish how much of HGB's error the level shift caused.

## Exercise 4: target transformation

**Validation only.** HGB trained on the count divided by the mean observed count over the previous seven calendar days reached R² **0.7520** and MAE **677.8** after multiplying each predicted ratio by that day's trailing mean. The mean uses only dates *t−7* through *t−1*. This lets the forecast adapt to changes in recent demand while the trees learn relative deviations. The additive residual alternative scored 0.7199 R² and 721.2 MAE.

The ratio improved on original HGB by 0.5072 R² and reduced MAE by 594.8 rides/day. It also beat Ridge by 0.1081 R² and 158.7 rides/day MAE. These differences are meaningful on this validation period. Held-out performance of the transformation remains unverified. The official results above use the original count target. [Experiment and reproduction command](docs/EXERCISE_4.md)

All three HGB variants used the same features, model settings, training dates, and validation dates. The experiment converted predictions to ride counts before scoring. Its use of recently observed counts assumes those counts are available at each daily forecast origin. A fixed-origin forecast for multiple future days would require a different evaluation because some of those recent counts would still be unknown.

## Exercise 5: ridge vs persistence

Across the same 184 held-out days, Ridge's R² of **0.5800** exceeded persistence's **0.5099** by **0.0701**. Ridge's MAE of **946.2** exceeded persistence's **840.1** by **106.1 rides/day**, about **12.6%**. Both differences are calculated from the saved metrics.

On a shared test set, R² equals one minus the sum of squared prediction errors divided by the sum of squared deviations from the test target mean. The denominator is the same for both models. Using the rounded scores, Ridge's squared-error total was about **14.3% lower** than persistence's, because the ratio of their squared-error totals is `(1 − 0.5800) / (1 − 0.5099)`. MAE averages absolute misses and weights each extra missed ride linearly. Doubling a day's absolute miss doubles its contribution to MAE and quadruples its contribution to squared error. One possible explanation is that Ridge reduced some large misses enough to offset increases elsewhere under squared loss. The aggregate scores establish the two totals' ordering, while the dates, frequencies, and sizes of the largest misses would require examining individual predictions.

I would favor persistence if the deployment goal is minimizing average absolute daily error. It won on that measure and needs only yesterday's observed count. Ridge is a candidate if unusually large misses have a disproportionate cost, given its lower aggregate squared error. It also needs a fitted model and reliable inputs at forecast time. If the operational cost depends on specific thresholds or on whether a forecast is too high or too low, I would evaluate that cost directly before choosing.

## Attribution

Claude Code used the local Qwen-backed `bikeshare-coder` model for the seeded-fault workflow and the peer audit attempt. The fault record includes the observed test and hook behavior, including the blocked fourth attempt. The peer audit stopped during repeated Ollama API errors before Claude produced a final report. [Seeded faults](docs/SEEDED_FAULTS.md) · [Peer audit transcript](docs/AUDIT.md)

Codex reproduced the historical leakage failures in detached worktrees, independently checked the peer's lag and evaluation by date, and drafted the historical fault reproduction skill. Codex manually rehearsed the skill procedure, with actual Claude Code invocation still unverified. Codex ran the separate Exercise 4 validation experiment and drafted the Exercise 5 comparison from the saved metrics and training code.

My decisions were to retain the chronological evaluation and official count-scale comparison, keep the transformed target as a separate validation experiment, and judge deployment against the error measure that best reflects operational cost. For average absolute misses I favor persistence, while Ridge remains a candidate when larger misses carry a disproportionate cost.
