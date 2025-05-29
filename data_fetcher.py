import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'constituents'}) or soup.find('table', {'class': 'wikitable sortable'})
        tickers = [row.find_all('td')[0].text.strip().replace('.', '-') for row in table.find_all('tr')[1:]]
        return tickers
    except Exception as e:
        print("Failed to fetch S&P 500 tickers:", e)
        return []

def parse_percent(value):
    try:
        return float(value.strip('%')) / 100
    except Exception:
        return 0.0

def get_growth_estimates(ticker):
    url = f'https://finance.yahoo.com/quote/{ticker}/analysis'

    for attempt in range(3):  # Retry 3 times
        try:
            print(f"[{ticker}][Attempt {attempt}] Get growth estimates...")
            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code == 429:
                print(f"[{ticker}] Blocked with 429 Too Many Requests — backing off...")
                time.sleep(2 ** attempt)
                continue

            if response.status_code in [401, 403]:
                print(f"[{ticker}] Access denied with HTTP error {response.status_code}")
                return {"Current year": 0.0}

            if response.status_code != 200:
                print(f"[{ticker}] HTTP error {response.status_code}")
                return {"Current year": 0.0}

            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')

            for table in tables:
                if f'{ticker}' in table.text:
                    for row in table.find_all('tr'):
                        cells = row.find_all('td')
                        if cells and f'{ticker}' in cells[0].text:
                            growth_data = {
                                "Current qtr.": parse_percent(cells[1].text),
                                "Next qtr.": parse_percent(cells[2].text),
                                "Current year": parse_percent(cells[3].text),
                                "Next year": parse_percent(cells[4].text)
                            }
                            print(f"[{ticker}] Growth estimates found: {growth_data}")
                            return growth_data

            print(f"[{ticker}] Growth table found but data row missing.")
            return {"Current year": 0.0}

        except Exception as e:
            print(f"[{ticker}] Scraping error: {e}")
            time.sleep(2 ** attempt)

    return {"Current year": 0.0}

def fetch_financial_data(tickers):
    data = []

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching data for {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info

            price = info.get("currentPrice")
            eps = info.get("trailingEps")
            pb = info.get("priceToBook", 999)
            de = info.get("debtToEquity", 999)

            growths = get_growth_estimates(ticker)
            growth = growths.get("Current year", 0)

            print(f"Growth for {ticker}: {growth:.2%}")

            if price is not None and eps is not None:
                data.append({
                    "ticker": ticker,
                    "price": price,
                    "eps": eps,
                    "growth": growth,
                    "pb": pb,
                    "de": de
                })

            time.sleep(1)

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    return pd.DataFrame(data)

# Example usage:
if __name__ == "__main__":
    tickers = get_sp500_tickers()
    if tickers:
        df = fetch_financial_data(tickers[:10])  # Limit to 10 tickers for testing
        print(df)
    else:
        print("No tickers to process.")
