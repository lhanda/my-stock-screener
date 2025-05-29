import streamlit as st
import pandas as pd
import altair as alt

from screener import main as run_screener, HELP_TEXT
from data_fetcher import get_sp500_tickers, fetch_financial_data

# Page setup
st.set_page_config(page_title="Graham Stock Screener", layout="wide")
st.title("📈 Benjamin Graham Stock Screener")

# Cache ticker list and financial data for 1 hour
@st.cache_data(ttl=3600)
def load_tickers():
    return get_sp500_tickers()

@st.cache_data(ttl=3600)
def load_financial_data(tickers):
    return fetch_financial_data(tickers)

# Sidebar filters
st.sidebar.header("Filters")
max_pb = st.sidebar.slider("Max Price to Book (P/B) Ratio", 1.0, 5.0, 3.0)
max_de = st.sidebar.slider("Max Debt to Equity (D/E) Ratio", 0, 200, 100)

try:
    with st.spinner("Loading tickers..."):
        tickers = load_tickers()

    with st.spinner(f"Fetching financial data for {len(tickers)} tickers..."):
        df = load_financial_data(tickers)

    # Run screener
    results = run_screener(df)

    # Apply user filters on screener results
    filtered_results = results[
        (results["pb"] <= max_pb) & (results["de"] <= max_de)
    ].reset_index(drop=True)

    if filtered_results.empty:
        st.warning("No stocks passed the filter criteria.")
    else:
        # Pagination setup
        st.subheader(f"Top {len(filtered_results)} Graham-Ranked Stocks")
        page_size = 10
        max_page = (len(filtered_results) - 1) // page_size + 1
        page = st.number_input("Page", min_value=1, max_value=max_page, value=1, step=1)

        start = (page - 1) * page_size
        end = start + page_size

        # Rename columns for better context
        def label_with_help(col):
            return f"{col} ℹ️" if col in HELP_TEXT else col

        renamed = {col: label_with_help(col) for col in filtered_results.columns}
        st.dataframe(filtered_results.iloc[start:end].rename(columns=renamed), use_container_width=True)

        # Help section
        with st.expander("ℹ️ Column Definitions"):
            for col, desc in HELP_TEXT.items():
                st.markdown(f"**{col}**: {desc}")

        # Download button
        csv = filtered_results.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Results as CSV", csv, "graham_screener_results.csv", "text/csv")

        # Charts
        st.markdown("---")
        st.subheader("📊 Score Distribution")
        st.bar_chart(filtered_results["score"])

        st.subheader("💹 Price vs Intrinsic Value")
        st.altair_chart(
            alt.Chart(filtered_results)
            .mark_circle(size=60)
            .encode(
                x="price",
                y="intrinsic_value",
                color="score",
                tooltip=["ticker", "price", "intrinsic_value", "score"],
            )
            .interactive(),
            use_container_width=True,
        )

except Exception as e:
    st.error(f"An error occurred: {e}")
