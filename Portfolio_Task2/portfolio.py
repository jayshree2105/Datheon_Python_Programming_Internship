import csv
import glob
import os
import sqlite3
from datetime import datetime


def load_dataset():
  """तुमची downloaded S&P 500 फाइल लोड करते (कंपनीचे नाव, सेक्टर आणि किंमत असल्यास)."""
  script_dir = os.path.dirname(os.path.abspath(__file__))
  # folder मधील सर्व files शोधणे (portfolio.py, portfolio_summary.csv आणि .db सोडून)
  all_files = [
      f
      for f in os.listdir(script_dir)
      if os.path.isfile(os.path.join(script_dir, f))
      and not f.endswith((".py", ".db"))
      and f != "portfolio_summary.csv"
  ]

  dataset = {}
  if not all_files:
    
    return dataset

  file_path = os.path.join(script_dir, all_files[0])
  with open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames:
      return dataset

    ticker_col = next(
        (
            col
            for col in reader.fieldnames
            if col.strip().lower() in ("symbol", "ticker", "stock")
        ),
        None,
    )
    name_col = next(
        (
            col
            for col in reader.fieldnames
            if col.strip().lower() in ("security", "name", "company")
        ),
        None,
    )
    sector_col = next(
        (
            col
            for col in reader.fieldnames
            if "sector" in col.strip().lower()
        ),
        None,
    )
    price_col = next(
        (
            col
            for col in reader.fieldnames
            if col.strip().lower()
            in ("price", "close", "last sale", "current price", "adj close")
        ),
        None,
    )

    if ticker_col:
      for row in reader:
        ticker = row.get(ticker_col, "").strip().upper()
        if not ticker:
          continue

        price = None
        if price_col:
          raw_price = (
              row.get(price_col, "").replace("$", "").replace(",", "").strip()
          )
          try:
            if raw_price:
              price = float(raw_price)
          except ValueError:
            pass

        dataset[ticker] = {
            "name": row.get(name_col, "Unknown").strip() if name_col else "Unknown",
            "sector": row.get(sector_col, "Unknown").strip() if sector_col else "Unknown",
            "price": price,
        }

  return dataset


def init_database():
  """SQLite Database (portfolio.db) तयार करतो आणि table बनवतो."""
  script_dir = os.path.dirname(os.path.abspath(__file__))
  db_path = os.path.join(script_dir, "portfolio.db")
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()

  cursor.execute("""
      CREATE TABLE IF NOT EXISTS portfolio_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          timestamp TEXT,
          ticker TEXT,
          company_name TEXT,
          sector TEXT,
          quantity REAL,
          buy_price REAL,
          current_price REAL,
          total_invested REAL,
          current_value REAL,
          gain_loss_amount REAL,
          gain_loss_percent REAL
      )
  """)
  conn.commit()
  return conn, db_path


def save_to_database(conn, summary_rows):
  """सर्व calculations SQLite database मध्ये save करतो."""
  cursor = conn.cursor()
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  for row in summary_rows:
    cursor.execute(
        """
        INSERT INTO portfolio_history (
            timestamp, ticker, company_name, sector, quantity,
            buy_price, current_price, total_invested,
            current_value, gain_loss_amount, gain_loss_percent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now,
            row["Ticker"],
            row["Company_Name"],
            row["Sector"],
            row["Quantity"],
            row["Buy_Price"],
            row["Current_Price"],
            row["Total_Invested"],
            row["Current_Value"],
            row["Gain_Loss_Amount"],
            row["Gain_Loss_Percent"],
        ),
    )
  conn.commit()


def fetch_live_price(ticker):
  """yfinance install असल्यास live price घेतो."""
  try:
    import yfinance as yf

    stock = yf.Ticker(ticker)
    price = stock.fast_info.get("lastPrice")
    return float(price) if price else None
  except Exception:
    return None


def get_current_price(ticker, dataset):
  """Dataset, live price किंवा manual input मधून सध्याची किंमत घेतो."""
  if ticker in dataset:
    info = dataset[ticker]
    print(f"   [S&P 500 Match] {info['name']} | Sector: {info['sector']}")
    if info["price"] is not None:
      print(f"   [Dataset Price] Current price for {ticker}: ${info['price']:.2f}")
      return info["price"]

  live_price = fetch_live_price(ticker)
  if live_price is not None:
    print(f"   [Live Price] Current price for {ticker}: ${live_price:.2f}")
    return live_price

  while True:
    try:
      manual = float(
          input(f"   Enter current market price for {ticker} ($): ")
      )
      if manual > 0:
        return manual
      print("   Price must be greater than 0.")
    except ValueError:
      print("   Invalid number. Please enter a valid price.")


def main():
  dataset = load_dataset()
  conn, db_path = init_database()
  portfolio = {}

  print("=" * 75)
  print("                 STOCK PORTFOLIO PERFORMANCE TRACKER")
  print("=" * 75)
  if dataset:
    print(f"[Database Connected] Loaded {len(dataset)} companies from S&P 500 dataset.\n")
  else:
    print("[Info] No external dataset found. Using live/manual lookup.\n")

  while True:
    ticker = input("Enter stock ticker symbol (or 'done' to calculate): ").strip().upper()
    if ticker == "DONE":
      if not portfolio:
        print("Portfolio is empty. Add at least one stock first.\n")
        continue
      break

    if not ticker.isalpha():
      print("Invalid ticker symbol. Use letters only (e.g., AAPL, MSFT).\n")
      continue

    try:
      buy_price = float(input(f"Enter buy price per share for {ticker} ($): "))
      quantity = float(input(f"Enter share quantity for {ticker}: "))
      if buy_price <= 0 or quantity <= 0:
        print("Buy price and quantity must be greater than zero.\n")
        continue
    except ValueError:
      print("Invalid numeric input. Please try again.\n")
      continue

    current_price = get_current_price(ticker, dataset)
    company_name = dataset[ticker]["name"] if ticker in dataset else "N/A"
    sector = dataset[ticker]["sector"] if ticker in dataset else "N/A"

    if ticker in portfolio:
      old_qty = portfolio[ticker]["quantity"]
      old_cost = old_qty * portfolio[ticker]["buy_price"]
      new_cost = old_cost + (quantity * buy_price)
      total_qty = old_qty + quantity
      portfolio[ticker]["buy_price"] = new_cost / total_qty
      portfolio[ticker]["quantity"] = total_qty
      portfolio[ticker]["current_price"] = current_price
    else:
      portfolio[ticker] = {
          "company_name": company_name,
          "sector": sector,
          "buy_price": buy_price,
          "quantity": quantity,
          "current_price": current_price,
      }

    print(f"-> Added {quantity} shares of {ticker}.\n")

  # Performance calculations
  summary_rows = []
  total_invested = 0.0
  total_current_value = 0.0

  print("\n" + "=" * 95)
  print(
      f"{'TICKER':<8} {'COMPANY':<22} {'QTY':>7} {'BUY ($)':>10}"
      f" {'CURR ($)':>10} {'VALUE ($)':>12} {'GAIN/LOSS':>11}"
  )
  print("-" * 95)

  for ticker, data in portfolio.items():
    qty = data["quantity"]
    buy = data["buy_price"]
    curr = data["current_price"]
    name = data["company_name"]
    sector = data["sector"]

    invested = qty * buy
    current_val = qty * curr
    gain_loss_amt = current_val - invested
    gain_loss_pct = (gain_loss_amt / invested) * 100

    total_invested += invested
    total_current_value += current_val

    short_name = (name[:19] + "..") if len(name) > 21 else name
    print(
        f"{ticker:<8} {short_name:<22} {qty:>7.2f} {buy:>10.2f}"
        f" {curr:>10.2f} {current_val:>12.2f} {gain_loss_pct:>+10.2f}%"
    )

    summary_rows.append({
        "Ticker": ticker,
        "Company_Name": name,
        "Sector": sector,
        "Quantity": round(qty, 4),
        "Buy_Price": round(buy, 2),
        "Current_Price": round(curr, 2),
        "Total_Invested": round(invested, 2),
        "Current_Value": round(current_val, 2),
        "Gain_Loss_Amount": round(gain_loss_amt, 2),
        "Gain_Loss_Percent": round(gain_loss_pct, 2),
    })

  overall_diff = total_current_value - total_invested
  overall_pct = (
      (overall_diff / total_invested) * 100 if total_invested > 0 else 0.0
  )

  print("-" * 95)
  print(f"Total Invested Capital : ${total_invested:,.2f}")
  print(f"Current Market Value   : ${total_current_value:,.2f}")
  print(f"Overall Gain / Loss    : ${overall_diff:+,.2f} ({overall_pct:+.2f}%)")
  print("=" * 95)

  # 1. CSV फाइल मध्ये Export करणे
  script_dir = os.path.dirname(os.path.abspath(__file__))
  output_path = os.path.join(script_dir, "portfolio_summary.csv")

  fieldnames = [
      "Ticker",
      "Company_Name",
      "Sector",
      "Quantity",
      "Buy_Price",
      "Current_Price",
      "Total_Invested",
      "Current_Value",
      "Gain_Loss_Amount",
      "Gain_Loss_Percent",
  ]

  with open(output_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(summary_rows)

  # 2. SQLite Database मध्ये Save करणे
  save_to_database(conn, summary_rows)
  conn.close()

  print(f"\n[Success] CSV exported to: '{output_path}'")
  print(f"[Success] Records saved to SQLite Database: '{db_path}'")


if __name__ == "__main__":
  main()