import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from technical_indicators.EMA import compute_ema
from technical_indicators.ADX import compute_adx

# Database connection parameters
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
MINUTE_TABLE_NAME = "alpaca_minute"
INDICATORS_TABLE_NAME = "ticker_minute_indicators"
SIGNALS_TABLE_NAME = "ticker_minute_signals"

def fetch_data_from_db(query):
    """Fetch data from the PostgreSQL database based on the provided query."""
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
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Get column names
        colnames = [desc[0] for desc in cursor.description]
        
        # Create a DataFrame
        df = pd.DataFrame(results, columns=colnames)
        
        return df

    except psycopg2.Error as e:
        print(f"Error fetching data from PostgreSQL database: {e}")
        return None
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def generate_trend_signals(df):
    """Generate trend following signals based on EMA crossovers and ADX."""
    df['trend'] = 'neutral'
    
    # Define a threshold for ADX to consider a strong trend
    adx_threshold = 25
    
    # Uptrend conditions:
    # 1. Fast EMA (10) above medium EMA (20)
    # 2. Medium EMA (20) above slow EMA (50)
    # 3. Price above all EMAs
    # 4. ADX above threshold
    uptrend = (df['ema_10'] > df['ema_20']) & \
              (df['ema_20'] > df['ema_50']) & \
              (df['close'] > df['ema_10']) & \
              (df['adx'] > adx_threshold)
    
    # Downtrend conditions:
    # 1. Fast EMA (10) below medium EMA (20)
    # 2. Medium EMA (20) below slow EMA (50)
    # 3. Price below all EMAs
    # 4. ADX above threshold
    downtrend = (df['ema_10'] < df['ema_20']) & \
                (df['ema_20'] < df['ema_50']) & \
                (df['close'] < df['ema_10']) & \
                (df['adx'] > adx_threshold)
    
    df.loc[uptrend, 'trend'] = 'uptrend'
    df.loc[downtrend, 'trend'] = 'downtrend'
    
    return df

def plot_data_with_ema(df, title):
    """Plot the close price and EMAs for the given DataFrame, excluding empty dates and weekends."""
    # Drop rows where 'close' or any EMA is NaN
    df = df.dropna(subset=['close', 'ema_10', 'ema_20', 'ema_50'])
    
    # Convert 'datetime' to datetime type if not already
    df['datetime'] = pd.to_datetime(df['datetime'])

    plt.figure(figsize=(12, 6))
    plt.plot(df['datetime'], df['close'], label='Close Price')
    plt.plot(df['datetime'], df['ema_10'], label='EMA 10', linestyle='--')
    plt.plot(df['datetime'], df['ema_20'], label='EMA 20', linestyle='--')
    plt.plot(df['datetime'], df['ema_50'], label='EMA 50', linestyle='--')
    
    # Plot trend signals
    uptrend_mask = df['trend'] == 'uptrend'
    downtrend_mask = df['trend'] == 'downtrend'
    
    plt.scatter(df[uptrend_mask]['datetime'], df[uptrend_mask]['close'], 
               color='green', marker='^', label='Uptrend')
    plt.scatter(df[downtrend_mask]['datetime'], df[downtrend_mask]['close'], 
               color='red', marker='v', label='Downtrend')
    
    plt.title(title)
    plt.xlabel('Datetime')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_adx(df, title):
    """Plot the ADX and its components for the given DataFrame."""
    # Drop rows where 'adx', '+di', or '-di' is NaN
    df = df.dropna(subset=['adx', '+di', '-di'])
    
    # Convert 'datetime' to datetime type if not already
    df['datetime'] = pd.to_datetime(df['datetime'])

    plt.figure(figsize=(12, 6))
    plt.plot(df['datetime'], df['adx'], label='ADX', color='purple')
    plt.plot(df['datetime'], df['+di'], label='+DI', linestyle='--', color='green')
    plt.plot(df['datetime'], df['-di'], label='-DI', linestyle='--', color='red')
    plt.title(title)
    plt.xlabel('Datetime')
    plt.ylabel('ADX / DI')
    plt.legend()
    plt.grid(True)
    plt.show()

def write_data_to_db(df, table_name, columns=None):
    """Write the DataFrame to the PostgreSQL database under the specified table name."""
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
        
        # Drop table if it exists
        drop_table_query = f"DROP TABLE IF EXISTS {table_name};"
        cursor.execute(drop_table_query)
        
        # Create table with trend column
        if table_name == SIGNALS_TABLE_NAME:
            create_table_query = f"""
            CREATE TABLE {table_name} (
                datetime TIMESTAMP,
                ticker VARCHAR(10),
                trend VARCHAR(10),
                PRIMARY KEY (datetime, ticker)
            );
            """
        else:
            create_table_query = f"""
            CREATE TABLE {table_name} (
                datetime TIMESTAMP,
                ticker VARCHAR(10),
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume BIGINT,
                ema_10 FLOAT,
                ema_20 FLOAT,
                ema_50 FLOAT,
                adx FLOAT,
                plus_di FLOAT,
                minus_di FLOAT,
                trend VARCHAR(10),
                PRIMARY KEY (datetime, ticker)
            );
            """
        cursor.execute(create_table_query)
        
        # Insert data into the table
        for _, row in df.iterrows():
            if table_name == SIGNALS_TABLE_NAME:
                insert_query = f"""
                INSERT INTO {table_name} (datetime, ticker, trend)
                VALUES (%s, %s, %s)
                ON CONFLICT (datetime, ticker) DO UPDATE SET
                trend = EXCLUDED.trend;
                """
                cursor.execute(insert_query, (row['datetime'], row['ticker'], row['trend']))
            else:
                insert_query = f"""
                INSERT INTO {table_name} (datetime, ticker, open, high, low, close, volume, 
                                        ema_10, ema_20, ema_50, adx, plus_di, minus_di, trend)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (datetime, ticker) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                ema_10 = EXCLUDED.ema_10,
                ema_20 = EXCLUDED.ema_20,
                ema_50 = EXCLUDED.ema_50,
                adx = EXCLUDED.adx,
                plus_di = EXCLUDED.plus_di,
                minus_di = EXCLUDED.minus_di,
                trend = EXCLUDED.trend;
                """
                cursor.execute(insert_query, tuple(row))
        
        # Commit the transaction
        connection.commit()

    except psycopg2.Error as e:
        print(f"Error writing data to PostgreSQL database: {e}")
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Example usage
if __name__ == "__main__":
    # Query for a specific ticker, e.g., 'AAPL'
    ticker = 'AAPL'
    minute_query = f"SELECT * FROM {MINUTE_TABLE_NAME} WHERE ticker = '{ticker}';"
    
    minute_data = fetch_data_from_db(minute_query)
    
    if minute_data is not None:
        print(f"Minute Data for {ticker}:")
        print(minute_data)
        # Compute EMAs for minute data
        minute_data_with_ema_10 = compute_ema(minute_data, span=10)
        minute_data_with_ema_20 = compute_ema(minute_data_with_ema_10, span=20)
        minute_data_with_ema_50 = compute_ema(minute_data_with_ema_20, span=50)
        # Compute ADX for minute data
        minute_data_with_adx = compute_adx(minute_data_with_ema_50)
        # Generate trend signals
        minute_data_with_signals = generate_trend_signals(minute_data_with_adx)
        print(f"Minute Data with EMAs, ADX, and Trend Signals for {ticker}:")
        print(minute_data_with_signals)
        # Plot minute data with EMAs and trend signals
        plot_data_with_ema(minute_data_with_signals, f"Minute Data with EMAs and Trends for {ticker}")
        # Plot ADX separately
        plot_adx(minute_data_with_signals, f"ADX and DI for {ticker}")
        # Write the data with EMAs, ADX, and trend signals back to the database
        write_data_to_db(minute_data_with_signals, INDICATORS_TABLE_NAME)
        # Write only the ticker, datetime, and trend to the signals table
        signals_data = minute_data_with_signals[['datetime', 'ticker', 'trend']]
        write_data_to_db(signals_data, SIGNALS_TABLE_NAME)