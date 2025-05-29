import os
import pandas as pd
from database import save_scores, get_last_score, init_db
from bond_yield import get_latest_aaa_yield_fred

AAA_BOND_YIELD = 4.4
DEFAULT_MOS = 0.25

HELP_TEXT = {
    "ticker": "Stock ticker symbol (e.g., AAPL, MSFT)",
    "price": "Current stock price retrieved from Yahoo Finance",
    "eps": "Trailing earnings per share (past 12 months)",
    "growth": "Estimated earnings growth for the current year",
    "pb": "Price-to-Book ratio; low values may indicate undervaluation",
    "de": "Debt-to-Equity ratio; high values may suggest financial risk",
    "intrinsic_value": "Estimated fair value using an adjusted Benjamin Graham formula",
    "score": "Relative value score: intrinsic value divided by current price",
    "buy_under": "Suggested buy-under price using 25% margin of safety",
    "actual_mos": "Actual margin of safety = 1 - (price / intrinsic value); 0 if price is too high",
    "last_score": "Score from previous run (used for historical comparison)",
    "score_change": "Change in score since last run"
}

def print_help():
    print("Column Definitions:\n")
    for col, desc in HELP_TEXT.items():
        print(f"{col}: {desc}")

def graham_value(eps, growth, bond_yield=AAA_BOND_YIELD, current_yield=4.88):
    try:
        fair_value = (eps * (7 + 100 * growth) * bond_yield) / current_yield
        return round(fair_value, 2)
    except Exception:
        return 0

def main(financial_df: pd.DataFrame):
    print("Initializing database...")
    init_db()

    print(f"Financial data input: {len(financial_df)} rows")

    print("Applying filters (P/B < 3, D/E < 100)...")
    filtered = financial_df[(financial_df["pb"] < 3) & (financial_df["de"] < 100)].copy()
    print(f"Number of stocks after filtering: {len(filtered)}")

    API_KEY = os.getenv("FRED_API_KEY")
    if not API_KEY:
        raise ValueError("FRED_API_KEY environment variable not set")

    print("Fetching bond yield for Graham formula...")
    try:
        current_yield = get_latest_aaa_yield_fred(API_KEY)
    except Exception as e:
        print("Error fetching bond yield, using fallback:", e)
        current_yield = 4.88

    print("Calculating Graham intrinsic value, buy-under price, and scores...")
    filtered["intrinsic_value"] = (
        filtered["eps"] * (7 + 100 * filtered["growth"]) * AAA_BOND_YIELD
    ) / current_yield
    filtered["intrinsic_value"] = filtered["intrinsic_value"].round(2)

    filtered = filtered[filtered["price"] > 0]  # avoid division by zero
    filtered["score"] = (filtered["intrinsic_value"] / filtered["price"]).round(2)
    filtered["buy_under"] = (filtered["intrinsic_value"] * (1 - DEFAULT_MOS)).round(2)

    filtered["actual_mos"] = filtered.apply(
        lambda r: round(1 - (r["price"] / r["intrinsic_value"]), 2)
        if r["price"] < r["intrinsic_value"] else 0,
        axis=1
    )

    print("Fetching last saved scores for historical comparison...")
    filtered["last_score"] = filtered["ticker"].apply(get_last_score).fillna(0).round(2)
    filtered["score_change"] = (filtered["score"] - filtered["last_score"]).round(2)

    print("Saving scores to database...")
    save_scores(filtered[["ticker", "score"]])

    print("Sorting results by score...")
    filtered.sort_values(by="score", ascending=False, inplace=True)

    # Optional: Export styled HTML with tooltips
    try:
        styled = filtered.style.set_tooltips([HELP_TEXT])
        styled.to_html("screener_results_with_help.html")
        print("Exported screener_results_with_help.html with tooltips.")
    except Exception as e:
        print("Failed to generate styled HTML:", e)

    print("Screener completed successfully.")
    return filtered.head(50)

# Optional CLI usage for help
if __name__ == "__main__":
    print_help()