import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# Constants
SCREENER_URL = "https://www.screener.in/screens/2961981/chatgpt-weekly/"
STOCKS_FILE = "stocks.csv"
DEFAULT_CAPITAL = 10_00_000  # ₹10 lakhs

def fetch_screener_data():
    """Scrape all stock data from Screener screen, handling pagination."""
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    columns = None
    page = 1
    limit = 25  # or 100 if supported

    # Check if SCREENER_URL already has a '?'
    param_join = '&' if '?' in SCREENER_URL else '?'

    while True:
        url = f"{SCREENER_URL}{param_join}page={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"class": "data-table"})
        if table is None:
            print(f"Page {page}: No table found, stopping.")
            break
        tbody = table.find("tbody")
        if tbody is None:
            print(f"Page {page}: No tbody found, stopping.")
            break
        rows = tbody.find_all("tr")
        # Find header row
        if columns is None:
            for row in rows:
                if all(cell.name == "th" for cell in row.find_all(["th", "td"])):
                    columns = [cell.get_text(strip=True).replace("\n", " ") for cell in row.find_all("th")]
                    break
        # Extract data rows
        page_data = []
        for row in rows:
            cells = row.find_all(["th", "td"])
            if any(cell.name == "th" for cell in cells):
                continue
            tds = row.find_all("td")
            if len(tds) != len(columns):
                continue
            row_data = [td.get_text(strip=True).replace(",", "") for td in tds]
            page_data.append(row_data)
        if not page_data:
            print(f"Page {page}: No data rows found, stopping.")
            break
        all_data.extend(page_data)
        print(f"Fetched {len(page_data)} rows from page {page}.")
        # print(page_data,limit)
        if len(page_data) < limit:
            break  # Last page
        page += 1

    if not all_data or columns is None:
        print("No data found.")
        return pd.DataFrame()
    df = pd.DataFrame(all_data, columns=columns)
    # Convert numeric columns to float where possible
    for col in columns:
        if col not in ["S.No.", "Name"]:
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                pass
    print(f"Total records fetched: {len(df)}")
    return df

def get_current_capital():
    """Read existing portfolio and calculate current capital from stocks.csv only."""
    try:
        portfolio = pd.read_csv(STOCKS_FILE)
        if "Investment" in portfolio.columns:
            total_value = portfolio["Investment"].sum()
            print("Current capital from stocks.csv:", total_value)
            return total_value
        else:
            # print("'Investment' column not found in stocks.csv. Using default capital.")
            return DEFAULT_CAPITAL
    except FileNotFoundError:
        # print("stocks.csv not found. Starting with default capital.")
        return DEFAULT_CAPITAL

def compute_weighted_score(df):
    # Normalize all relevant columns
    norm_cols = [
        "ROCE%", "Sales growth%", "Profit growth%", "P/E",
        "CMPRs.", "Div Yld%", "Qtr Profit Var%", "Qtr Sales Var%"
    ]
    for col in norm_cols:
        if col in df.columns:
            # Convert to numeric, coerce errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            max_val = df[col].max()
            min_val = df[col].min()
            df[col + "_norm"] = (df[col] - min_val) / (max_val - min_val + 1e-9)
        else:
            print(f"Warning: Column '{col}' not found in DataFrame.")
            df[col + "_norm"] = 0.0
    # Invert normalized P/E because lower is better
    df["inv_pe"] = 1 - df["P/E_norm"]
    # Redistribute the 0.15 weight from EPS growth 3Y % proportionally to the other metrics
    # Old total weight (excluding EPS growth 3Y %) = 0.85
    # New weights: multiply each by (1/0.85)
    w_20 = 0.20 / 0.85  # for ROCE%
    w_15 = 0.15 / 0.85  # for Sales growth%, Profit growth%, inv_pe
    w_05 = 0.05 / 0.85  # for CMPRs., Div Yld%, Qtr Profit Var%, Qtr Sales Var%
    df["Score"] = (
        w_20 * df["ROCE%_norm"] +
        w_15 * df["Sales growth%_norm"] +
        w_15 * df["Profit growth%_norm"] +
        w_15 * df["inv_pe"] +
        w_05 * df["CMPRs._norm"] +
        w_05 * df["Div Yld%_norm"] +
        w_05 * df["Qtr Profit Var%_norm"] +
        w_05 * df["Qtr Sales Var%_norm"]
    )
    df.sort_values("Score", ascending=False, inplace=True)
    return df

def generate_portfolio(screener_df, capital):
    """Create new portfolio using inverse rank allocation based on weighted custom score."""
    # Compute weighted score and sort
    screener_df = compute_weighted_score(screener_df)
    n = min(15, len(screener_df))
    selected = screener_df.head(n).copy()
    selected["Rank"] = range(1, n + 1)
    selected["Weight"] = (n + 1 - selected["Rank"]) / sum(range(1, n + 1))
    selected["Allocated"] = selected["Weight"] * capital
    selected["Qty"] = (selected["Allocated"] // selected["CMPRs."]).astype(int)
    selected["Investment"] = selected["Qty"] * selected["CMPRs."]
    return selected[["Name", "CMPRs.", "Qty", "Investment", "Score"]]

def save_new_portfolio(df):
    """Write updated portfolio to file, archiving old file with timestamp if present."""
    if os.path.exists(STOCKS_FILE):
        # Archive the old file with a sortable timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"stocks_{timestamp}.csv"
        os.rename(STOCKS_FILE, archive_name)
        print(f"Archived old portfolio to {archive_name}")
    df.to_csv(STOCKS_FILE, index=False)
    print(f"Saved new portfolio to {STOCKS_FILE}")

def main():
    screener_df = fetch_screener_data()
    # print(screener_df)
    capital = get_current_capital()
    print(capital)
    new_portfolio = generate_portfolio(screener_df, capital)
    print("New Portfolio:\n", new_portfolio)
    save_new_portfolio(new_portfolio)

if __name__ == "__main__":
    main()
