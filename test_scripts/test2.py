import yfinance as yf
from datetime import datetime, timedelta

def fetch_and_print_minute_data(ticker_symbol):
    """Fetch the latest minute data for a given ticker symbol from Yahoo Finance and print it."""
    ticker = yf.Ticker(ticker_symbol)
    # Fetch the latest minute data
    now = datetime.now()
    start_time = now - timedelta(minutes=1)
    data = ticker.history(interval="1m", start=start_time, end=now)
    if data.empty:
        print("No minute data available for the given ticker symbol.")
    else:
        print(data)

# Example usage
if __name__ == "__main__":
    ticker_symbol = "AAPL"  # Example ticker symbol
    fetch_and_print_minute_data(ticker_symbol)