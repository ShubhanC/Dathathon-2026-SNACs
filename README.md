## Team078 - SNAC

# Call Center Volume & Performance Forecasting

## Intro
This model predicts the call center metrics for August 2026 across four 
distinct portfolios (A, B, C, and D) to optimize staffing. Accurate forecasting 
of Call Volume (CV), Average Handle Time (CTT), and Abandon Rates (ABD) is important
for workforce management. By predicting these metrics for August 2026, this tool
provides the organization the ability to optimize staffing levels, ensuring an adeqate 
number of agents are available to maintain service levels but stick to budget targets.

## Our Features
Our model relies on a mix of categorical and temporal features to account for 
the seasonal nature of call center traffic. We used temporal features like month,
day of the month, and day of the week to find the standard call patterns. We 
used US public holidays to account for significant drops in the pattern. To account 
for the cycle of weeks, we appy cyclical encoding to time variables using sine
and cosine transformations. Additionally, we utilize historical lag variables,
such as volume from the same day in the previous year, to provide a consistent 
baseline for the regressor and improve overall predictive stability.

## Two-Stage model
We utilize a top-down approach to handle interval-level high-variance, ensuring 
our 30-minute forcasts are accurate to daily totals. We start with stage 1, where 
individual XGBoost Regressors are trained for each portfolio to predict daily totals 
for call volume and handling time. In stage 2, these daily aggregates are transitioned 
into 30-minute intervals using HIstorical Intraday Profiles created by grouping 
past data by day of week and IntervalIdx. By calculating the specific metrics for 
each interval, and multiplying it by the stage 1 daily prediction, we generate a final 
48-interval forecast that is guaranteed to sum back to the predicted daily total.

## Results
The model achieved a strong predictive accuracy across all four portfolios, particularly 
for Call Volume and CCT, with Mean Absolute Percentage Errors (MAPE), ranging from 9.5% 
and 11.5% for volume and 1.9% to 2.6% for handling times. While the Abandon Rate shows a 
higher MAPE exceeding 100%, this is mainly caused by the high frequency of zero-value 
intervals in the historical data, whihc disproportionately inflates percentage-based 
error metrics. Overall, the stage 1 daily forecasts provided a reliable baseline that, 
when combined with the stage 2 intraday profiles, resulted in a mathematically 
accurate 30-minute forecast for the August 2026 period.
