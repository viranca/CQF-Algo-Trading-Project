from ib_insync import IB, Stock
import psycopg2
from psycopg2 import sql, extras
import pandas as pd
from datetime import datetime, timedelta

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
TABLE_NAME = "ibkr_daily"

def fetch_daily_data(ticker_symbol):
    """Fetch daily data for a given ticker symbol from Interactive Brokers."""
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    contract = Stock(ticker_symbol, 'SMART', 'USD')
    end_date = datetime.now().strftime('%Y%m%d %H:%M:%S')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d %H:%M:%S')
    bars = ib.reqHistoricalData(
        contract, endDateTime=end_date, durationStr='1 Y',
        barSizeSetting='1 day', whatToShow='TRADES', useRTH=True
    )
    data = pd.DataFrame(bars)
    data['ticker'] = ticker_symbol  # Add ticker column
    ib.disconnect()
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
            [(row['date'], row['ticker'], row['open'], row['high'], row['low'], row['close'], row['volume']) for index, row in data.iterrows()])
        
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
    tickers = get_tickers_from_csv('./Research/interactive_brokers/tickers.csv')
    for ticker_symbol in tickers:
        daily_data = fetch_daily_data(ticker_symbol)
        if not daily_data.empty:
            store_data_in_db(daily_data, TABLE_NAME)
            #print(f"Data for {ticker_symbol} stored successfully!")
        else:
            print(f"No data to display for {ticker_symbol}.")
