# MarketSync

**Weekly rebalancing portfolio with an email report generated and sent automatically.**

---

## Overview
This project scrapes stock data from Screener.in, generates a model portfolio using a custom scoring and allocation strategy, and sends a detailed email report (with the new portfolio attached) on a schedule (e.g., via cron or Render jobs). It also archives previous portfolios and can track gains using live prices.

---

## Features
- **Scrapes latest stock data** from a Screener.in custom screen.
- **Ranks stocks** using a weighted scoring formula based on financial metrics.
- **Allocates capital** using inverse rank allocation.
- **Archives old portfolios** with timestamped filenames for easy tracking.
- **Sends an HTML email report** with the new portfolio and summary stats.
- **Fetches live prices** for accurate gain/loss calculation.
- **Designed for automation** (cron, Render jobs, etc.).

---

## File Descriptions

- `stock_sim.py`  
  Main script for scraping, portfolio generation, archiving, and price fetching. Contains all core logic and helper functions.

- `portfolio_reporter.py`  
  Script for running the portfolio update, sending the email report, and (optionally) pushing results to cloud or email. Designed for cron/Render jobs.

- `.env`  
  **Not tracked by git.** Stores sensitive email credentials and configuration. See below for required variables.

- `requirements.txt`  
  Python dependencies for the project.

- `.gitignore`  
  Ensures `.env` and all generated CSVs are not tracked by git.

- `stocks.csv`  
  The latest generated portfolio (not tracked by git).

- `stocks_YYYYMMDD_HHMMSS.csv`  
  Archived portfolios, automatically created before each new run (not tracked by git).

---

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/AnirudhKumar99/MarketSync.git
cd MarketSync
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Create a `.env` File
Create a file named `.env` in the project root with the following content (replace with your actual credentials):
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your.email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_FROM=your.email@gmail.com
EMAIL_TO=recipient@example.com
```

### 4. Run Locally
To generate a new portfolio and send the report:
```sh
python3 portfolio_reporter.py
```

### 5. Automate with Cron or Render
- **Cron:** Add a cron job (e.g., every Monday at 10am IST):
  ```cron
  30 4 * * 1 cd /path/to/MarketSync && /usr/bin/python3 portfolio_reporter.py
  ```
  (4:30 UTC = 10:00 IST)
- **Render:** Set up a scheduled job to pull from GitHub and run `python3 portfolio_reporter.py`.

---

## How It Works
1. **Scraping:** Pulls the latest stock data from a Screener.in screen.
2. **Portfolio Generation:** Ranks and allocates capital using a custom formula.
3. **Archiving:** Renames the previous `stocks.csv` to a timestamped archive.
4. **Email Report:** Sends an HTML email with the new portfolio and a summary of gains if the previous portfolio was sold at current prices.
5. **Live Price Fetching:** Uses the Screener company code to fetch the latest price for each stock.

---

## Environment Variables (.env)
- `EMAIL_HOST` - SMTP server (e.g., smtp.gmail.com)
- `EMAIL_PORT` - SMTP port (e.g., 587)
- `EMAIL_HOST_USER` - SMTP username (your email)
- `EMAIL_HOST_PASSWORD` - SMTP password or app password
- `EMAIL_FROM` - Sender email address
- `EMAIL_TO` - Recipient email address (comma-separated for multiple)

---

## Notes & Tips
- **.env and all CSVs are ignored by git** for security and privacy.
- **App Passwords:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833?hl=en) if 2FA is enabled.
- **Render/Cloud:** Make sure to set environment variables in your cloud dashboard if not using a `.env` file.
- **Debugging:** The scripts print helpful debug info if anything goes wrong (e.g., missing columns, price fetch errors).
- **Extending:** You can easily add new metrics or change the scoring formula in `stock_sim.py`.

---

## Example Output

- **stocks.csv** (latest portfolio):
  | Code | Name | CMPRs. | Qty | Investment | Score |
  |------|------|--------|-----|------------|-------|
  | KILITCH | Kilitch Drugs | 1013.0 | 10 | 10130.0 | 0.42 |

- **Email Report:**
  - HTML summary of new portfolio
  - Top 5 holdings table
  - Amount if previous portfolio was sold at current prices
  - `stocks.csv` attached

---

## License
MIT (or specify your license here)

---

## Author
[Anirudh Kumar](https://github.com/AnirudhKumar99)
