import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame 

import pandas as pd
from datetime import datetime, timedelta

import psycopg2
from psycopg2 import sql, extras


# Alpaca API credentials
APCA_API_BASE_URL = "https://paper-api.alpaca.markets/v2"
APCA_API_KEY_ID = "removed"
APCA_API_SECRET_KEY = "removed"
    
# Database connection parameters
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
TABLE_NAME = "alpaca_minute"

def fetch_minute_data_from_alpaca(ticker_symbol):
    """Fetch minute data for a given ticker symbol from Alpaca Market Data API."""
    api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')
    
    # Define the time range for the data
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=7)  # Fetching minute data for the last 7 days
    
    # Convert dates to the required format (YYYY-MM-DD)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Fetch minute data
    barset = api.get_bars(ticker_symbol, TimeFrame.Minute, start=start_date_str, end=end_date_str).df
    
    # Add ticker column
    barset['ticker'] = ticker_symbol
    
    return barset

def store_data_in_db(data, table_name):
    """Store the fetched data into a PostgreSQL database."""
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        # Create a cursor object
        cursor = connection.cursor()
        
        # Create table if it doesn't exist
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table} (
                datetime TIMESTAMP,
                ticker VARCHAR(10),
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume BIGINT,
                PRIMARY KEY (datetime, ticker)
            );
        """).format(table=sql.Identifier(table_name))
        
        cursor.execute(create_table_query)
        connection.commit()
        
        # Use execute_batch for faster inserts
        insert_query = sql.SQL("""
            INSERT INTO {table} (datetime, ticker, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (datetime, ticker) DO NOTHING;
        """).format(table=sql.Identifier(table_name))
        
        psycopg2.extras.execute_batch(cursor, insert_query, 
            [(index, row['ticker'], row['open'], row['high'], row['low'], row['close'], row['volume']) for index, row in data.iterrows()])
        
        connection.commit()

    except psycopg2.Error as e:
        print(f"Error storing data in PostgreSQL database: {e}")
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def get_tickers_from_csv(file_path):
    """Read tickers from a CSV file."""
    tickers = pd.read_csv(file_path, header=None).squeeze().tolist()
    return [ticker.strip().strip('"') for ticker in tickers]

# Example usage
if __name__ == "__main__":
    tickers = get_tickers_from_csv('tickers.csv')
    for ticker_symbol in tickers:
        minute_data = fetch_minute_data_from_alpaca(ticker_symbol)
        if not minute_data.empty:
            store_data_in_db(minute_data, TABLE_NAME)
        else:
            print(f"No data to display for {ticker_symbol}.")
