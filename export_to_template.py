"""
export_to_template.py
─────────────────────
Fills template_forecast_v00.csv with predictions from `august_intervals`.
 
Usage (add this cell at the bottom of your notebook):
    exec(open('export_to_template.py').read())
 
Or import the function:
    from export_to_template import fill_template
    output_df = fill_template(august_intervals, template_path, output_path)
"""
 
import pandas as pd
import numpy as np
 
 
def fill_template(august_intervals: pd.DataFrame,
                  template_path: str = './template_forecast_v00.csv',
                  output_path:   str = './August_2026_Forecast_v00.csv') -> pd.DataFrame:
    """
    Parameters
    ----------
    august_intervals : DataFrame
        Output of apply_intraday_profiles(). Must contain columns:
        Portfolio, Day, Interval, Call_Volume, Abandoned_Calls, Abandoned_Rate, CCT
    template_path : str
        Path to the blank template CSV.
    output_path : str
        Where to write the filled CSV.
 
    Returns
    -------
    filled : DataFrame  — the completed template (also written to output_path)
    """
 
    # ── 1. Load the template (keeps exact row order & interval labels) ────────
    template = pd.read_csv(template_path)
    print(f"Template loaded: {template.shape[0]} rows × {template.shape[1]} cols")
 
    # ── 2. Normalise the Interval column in *both* frames to match exactly ────
    #   Template uses  "0:00", "0:30", "10:00"  (no leading zero on hour)
    #   august_intervals may have "00:00:00", "00:30:00", "10:00:00" (HH:MM:SS)
    #   → strip seconds, drop leading zero on hour to match template
 
    def normalise_interval(s: str) -> str:
        """'00:30:00' → '0:30'   |   '10:00:00' → '10:00'   |   '0:30' → '0:30' """
        parts = str(s).strip().split(':')
        h = int(parts[0])
        m = int(parts[1])
        return f"{h}:{m:02d}"
 
    template['_interval_key'] = template['Interval'].apply(normalise_interval)
 
    pred = august_intervals.copy()
    pred['_interval_key'] = pred['Interval'].apply(normalise_interval)
 
    # ── 3. Ensure Abandoned_Rate is a decimal (0–1), not percentage ───────────
    #   The pipeline stores it as a decimal; template expects decimal too.
    #   (If yours is already 0–1, this is a no-op; if it's 0–100, divide.)
    if pred['Abandoned_Rate'].max() > 1.5:          # heuristic: must be % scale
        pred['Abandoned_Rate'] = pred['Abandoned_Rate'] / 100
        print("  ℹ️  Abandoned_Rate divided by 100 (was %-scale, now decimal)")
 
    # ── 4. Build a lookup: (Portfolio, Day, interval_key) → metrics ──────────
    metrics_cols = ['Call_Volume', 'Abandoned_Calls', 'Abandoned_Rate', 'CCT']
    lookup = (
        pred
        .groupby(['Portfolio', 'Day', '_interval_key'])[metrics_cols]
        .first()          # should already be unique; first() is a safety net
    )
 
    # ── 5. Fill the template row-by-row ──────────────────────────────────────
    filled = template.copy()
 
    portfolio_col_map = {
        'A': ('Calls_Offered_A', 'Abandoned_Calls_A', 'Abandoned_Rate_A', 'CCT_A'),
        'B': ('Calls_Offered_B', 'Abandoned_Calls_B', 'Abandoned_Rate_B', 'CCT_B'),
        'C': ('Calls_Offered_C', 'Abandoned_Calls_C', 'Abandoned_Rate_C', 'CCT_C'),
        'D': ('Calls_Offered_D', 'Abandoned_Calls_D', 'Abandoned_Rate_D', 'CCT_D'),
    }
 
    # Vectorised fill: iterate portfolios, merge on (Day, interval_key)
    for portfolio, (col_cv, col_abd, col_arate, col_cct) in portfolio_col_map.items():
        pf_pred = pred[pred['Portfolio'] == portfolio][
            ['Day', '_interval_key', 'Call_Volume', 'Abandoned_Calls', 'Abandoned_Rate', 'CCT']
        ].copy()
 
        pf_pred = pf_pred.rename(columns={
            'Call_Volume':     col_cv,
            'Abandoned_Calls': col_abd,
            'Abandoned_Rate':  col_arate,
            'CCT':             col_cct,
        })
 
        filled = filled.drop(columns=[col_cv, col_abd, col_arate, col_cct], errors='ignore')
        filled = filled.merge(pf_pred, on=['Day', '_interval_key'], how='left')
 
    # ── 6. Final dtype enforcement & non-negativity guarantee ────────────────
    for portfolio in 'ABCD':
        col_cv, col_abd, col_arate, col_cct = portfolio_col_map[portfolio]
 
        filled[col_cv]    = filled[col_cv].clip(lower=0).round(0).astype('Int64')
        filled[col_abd]   = filled[col_abd].clip(lower=0).round(0).astype('Int64')
        filled[col_arate] = filled[col_arate].clip(lower=0, upper=1).round(6)
        filled[col_cct]   = filled[col_cct].clip(lower=0).round(2)
 
    # ── 7. Restore original template column order & drop helper column ────────
    out_cols = list(template.columns)               # exact original order
    filled = filled[out_cols]                       # drop _interval_key automatically
 
    # ── 8. Write output ───────────────────────────────────────────────────────
    filled.to_csv(output_path, index=False)
    print(f"\n✅  Filled template saved → {output_path}")
    print(f"   Rows: {len(filled)}  |  Expected: {31 * 48} = {31*48}")
 
    # ── 9. Quick validation ───────────────────────────────────────────────────
    null_counts = filled.drop(columns=['Month','Day','Interval']).isnull().sum()
    if null_counts.sum() == 0:
        print("   ✅  No nulls — all cells filled.")
    else:
        print(f"\n   ⚠️  Null cells found:\n{null_counts[null_counts > 0]}")
 
    neg_check = {
        col: (filled[col] < 0).sum()
        for col in filled.columns
        if col not in ['Month', 'Day', 'Interval']
    }
    neg_total = sum(neg_check.values())
    if neg_total == 0:
        print("   ✅  No negative values.")
    else:
        print(f"   ⚠️  Negative values found: {neg_check}")
 
    print("\n=== Daily CV totals (spot check) ===")
    for portfolio in 'ABCD':
        col_cv = portfolio_col_map[portfolio][0]
        daily = filled.groupby('Day')[col_cv].sum()
        print(f"  Portfolio {portfolio}: "
              f"mean={daily.mean():.0f}  min={daily.min():.0f}  max={daily.max():.0f}")
 
    return filled
 
 
# ── Run immediately if executed as a script / exec()'d in notebook ────────────
if __name__ == '__main__' or '__file__' not in dir():
    try:
        # august_intervals must already exist in the notebook environment
        output_df = fill_template(
            august_intervals,
            template_path='./template_forecast_v00.csv',
            output_path='./August_2026_Forecast_v00.csv',
        )
        print("\n=== Preview (first 5 rows) ===")
        print(output_df.head().to_string())
    except NameError:
        print("⚠️  `august_intervals` not found in scope.")
        print("   Run Stages 1 & 2 first, then re-run this cell.")
 