import os
import smtplib
import stock_sim
from email.message import EmailMessage
from datetime import datetime
import pandas as pd

# Email configuration (use environment variables for security)
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_FROM = os.environ.get('EMAIL_FROM', EMAIL_HOST_USER)
EMAIL_TO = os.environ.get('EMAIL_TO')

# Run the portfolio update and get the new portfolio
screener_df = stock_sim.fetch_screener_data()
capital = stock_sim.get_current_capital()
new_portfolio = stock_sim.generate_portfolio(screener_df, capital)
stock_sim.save_new_portfolio(new_portfolio)

# Find the most recent archived portfolio (if any)
archive_files = [f for f in os.listdir('.') if f.startswith('stocks_') and f.endswith('.csv')]
archive_files.sort(reverse=True)
previous_portfolio_file = archive_files[0] if archive_files else None

# Calculate the amount made by selling the previous portfolio
amount_made = None
if previous_portfolio_file:
    prev_df = pd.read_csv(previous_portfolio_file)
    # Merge with current prices
    merged = pd.merge(prev_df, screener_df, left_on='Name', right_on='Name', how='inner')
    merged['Current_Value'] = merged['Qty'] * merged['CMPRs.']
    amount_made = merged['Current_Value'].sum()

# Prepare the HTML email
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
subject = f"Stock Portfolio Update - {now}"

html = f"""
<html>
  <body>
    <h2>Stock Portfolio Update - {now}</h2>
    <p><b>New portfolio generated and saved as <code>stocks.csv</code>.</b></p>
    <p><b>Capital used:</b> ₹{capital:,.2f}</p>
"""
if amount_made is not None:
    html += f"<p><b>Amount if previous portfolio was sold at current prices:</b> ₹{amount_made:,.2f}</p>"
html += """
    <h3>Top 5 Holdings:</h3>
    <table border="1" cellpadding="5" cellspacing="0">
      <tr>
        <th>Name</th><th>Price</th><th>Qty</th><th>Investment</th><th>Score</th>
      </tr>
"""
for _, row in new_portfolio.head(5).iterrows():
    html += f"<tr><td>{row['Name']}</td><td>{row['CMPRs.']}</td><td>{row['Qty']}</td><td>{row['Investment']}</td><td>{row['Score']:.4f}</td></tr>"
html += """
    </table>
    <p>See attached CSV for full portfolio.</p>
  </body>
</html>
"""

# Prepare the email message
msg = EmailMessage()
msg['Subject'] = subject
msg['From'] = EMAIL_FROM
msg['To'] = EMAIL_TO
msg.set_content('This email contains an HTML part and an attachment.')
msg.add_alternative(html, subtype='html')

# Attach the new portfolio CSV
with open('stocks.csv', 'rb') as f:
    msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename='stocks.csv')

# Send the email
with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
    server.starttls()
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    server.send_message(msg)
    print(f"Email sent to {EMAIL_TO}") 