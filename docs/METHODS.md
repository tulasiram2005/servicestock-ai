# Methods and limits

All money is USD under synthetic cost assumptions. Demand is the first 24 public Monash
car-parts series; upstream missing values were replaced with zero. This subset is sparse and
not a representative sample of a company's inventory.

ABC uses trailing annual consumption times synthetic unit cost; boundaries are cumulative
80% and 95%. ADI is periods/nonzero periods; CV2 is population nonzero variance/mean squared.
Pattern cutoffs are 1.32 and 0.49. Zero-demand series have undefined ADI/CV2.

Forecasts: last-observation naive, period-12 seasonal naive, Croston, SBA (0.95 correction
with alpha 0.1), TSB, and LightGBM lag/rolling features. Six validation origins select a model
by demand-pattern aggregate MAE; selection patterns are frozen using history before those
validation origins, excluding the final 12 validation/test periods. The final six origins are
held out. Displayed current demand patterns still use full history and do not control model
selection. A regression test changes future test demand and verifies unchanged selection
patterns and validation scores. MASE is undefined when
the training naive denominator is zero. No MAPE is used. Forecast interval radii are empirical
historical absolute changes; nominal coverage is not calibrated. TreeSHAP contributions explain
the LightGBM model, which need not be the selected forecasting model.

Policy uses independent monthly empirical resampling over a lognormal lead time, capped at
12 months. Baseline is two months of cover. Candidate base stocks minimize expected modeled cost
subject to cycle service and no worse fill rate than baseline. Holding cost uses expected ending
inventory, not continuous-time average inventory. Shortage and expedite costs are annualized
by 12/mean lead months. Draws are paired for baseline/optimized; bootstrap intervals and centered
paired-bootstrap p-values are computed on cost differences. This is an illustrative lead-time
cycle approximation, not a validated replenishment simulator or an implemented (s,S) process.

Regression uses synthetic supplier/category/season/order-size features with disjoint train,
calibration and test rows; predicted delay feeds simulated lead time. NLP uses synthetic labels
and held-out phrase templates with TF-IDF/logistic regression. Zero-shot comparison is pending.
Distribution comparisons use AIC; KS p-values are descriptive only because parameters are
estimated and demand is discrete. Pooling is a theoretical independent-equal-variance safety
stock estimate, not measured savings. BOM lead rollup assumes parallel procurement.

DIO = recommended inventory value / trailing annual demand valued at synthetic standard cost * 365.
PPV = (actual price - standard price) * quantity. Budget variance = actual PO spend - budget.
These are demonstration scorecards, not audited accounting measures.
