import yfinance as yf
import psycopg2
from psycopg2 import sql
import csv
import pandas as pd
from datetime import datetime, timedelta

# Database connection parameters
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
TABLE_NAME = "yfinance_daily"

def fetch_daily_data(ticker_symbol):
    """Fetch daily data for a given ticker symbol from Yahoo Finance."""
    ticker = yf.Ticker(ticker_symbol)
    # Fetch daily data for the last year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = ticker.history(interval="1d", start=start_date, end=end_date)
    data['ticker'] = ticker_symbol  # Add ticker column
    return data

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
            [(index, row['ticker'], row['Open'], row['High'], row['Low'], row['Close'], row['Volume']) for index, row in data.iterrows()])
        
        connection.commit()
        #print("Data stored successfully!")

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
        daily_data = fetch_daily_data(ticker_symbol)
        if not daily_data.empty:
            store_data_in_db(daily_data, TABLE_NAME)
            #print(f"Data for {ticker_symbol} stored successfully!")
        else:
            print(f"No data to display for {ticker_symbol}.")
