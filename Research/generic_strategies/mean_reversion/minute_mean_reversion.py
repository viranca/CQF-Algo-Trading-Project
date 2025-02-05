import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal
from technical_indicators.rolling_z_score import calculate_rolling_z_score

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

def generate_mean_reversion_signals(df, window=10):
    """Generate mean reversion signals based on rolling z-score."""
    df['signal'] = 'neutral'
    
    # Convert 'close' to float if it's of type Decimal
    if df['close'].dtype == 'object' or isinstance(df['close'].iloc[0], Decimal):
        df['close'] = df['close'].astype(float)
    
    # Calculate rolling z-score using the imported function
    df = calculate_rolling_z_score(df, window=window)
    
    # Signal conditions
    buy_signal = df['z_score'] < -2
    sell_signal = df['z_score'] > 2
    
    df.loc[buy_signal, 'signal'] = 'buy'
    df.loc[sell_signal, 'signal'] = 'sell'
    
    return df

def plot_data_with_signals(df, title):
    """Plot the close price and signals for the given DataFrame."""
    # Drop rows where 'close' or 'z_score' is NaN
    df = df.dropna(subset=['close', 'z_score'])
    
    # Convert 'datetime' to datetime type if not already
    df['datetime'] = pd.to_datetime(df['datetime'])

    plt.figure(figsize=(12, 6))
    plt.plot(df['datetime'], df['close'], label='Close Price')
    
    # Plot signals
    buy_mask = df['signal'] == 'buy'
    sell_mask = df['signal'] == 'sell'
    
    plt.scatter(df[buy_mask]['datetime'], df[buy_mask]['close'], 
               color='green', marker='^', label='Buy Signal')
    plt.scatter(df[sell_mask]['datetime'], df[sell_mask]['close'], 
               color='red', marker='v', label='Sell Signal')
    
    plt.title(title)
    plt.xlabel('Datetime')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()

def write_data_to_db(df, table_name):
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
        
        # Create table with signal column
        create_table_query = f"""
        CREATE TABLE {table_name} (
            datetime TIMESTAMP,
            ticker VARCHAR(10),
            close FLOAT,
            z_score FLOAT,
            signal VARCHAR(10),
            PRIMARY KEY (datetime, ticker)
        );
        """
        cursor.execute(create_table_query)
        
        # Insert data into the table
        for _, row in df.iterrows():
            insert_query = f"""
            INSERT INTO {table_name} (datetime, ticker, close, z_score, signal)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (datetime, ticker) DO UPDATE SET
            close = EXCLUDED.close,
            z_score = EXCLUDED.z_score,
            signal = EXCLUDED.signal;
            """
            cursor.execute(insert_query, (row['datetime'], row['ticker'], row['close'], row['z_score'], row['signal']))
        
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

def write_signals_to_minute_signals_table(df):
    """Write the signals to the minute signals table in the PostgreSQL database."""
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
        
        # Add new column for signal if it doesn't exist
        add_columns_query = f"""
        ALTER TABLE {SIGNALS_TABLE_NAME} 
        ADD COLUMN IF NOT EXISTS signal VARCHAR(10);
        """
        cursor.execute(add_columns_query)
        
        # Insert signals into the minute signals table
        for _, row in df.iterrows():
            insert_query = f"""
            INSERT INTO {SIGNALS_TABLE_NAME} (datetime, ticker, signal)
            VALUES (%s, %s, %s)
            ON CONFLICT (datetime, ticker) DO UPDATE SET
            signal = EXCLUDED.signal;
            """
            cursor.execute(insert_query, (row['datetime'], row['ticker'], row['signal']))
        
        # Commit the transaction
        connection.commit()

    except psycopg2.Error as e:
        print(f"Error writing signals to PostgreSQL database: {e}")
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
        # Generate mean reversion signals
        minute_data_with_signals = generate_mean_reversion_signals(minute_data)
        print(f"Minute Data with Rolling Z-Score and Signals for {ticker}:")
        print(minute_data_with_signals)
        # Plot minute data with signals
        plot_data_with_signals(minute_data_with_signals, f"Minute Data with Rolling Z-Score Signals for {ticker}")
        # Write the data with signals back to the database
        write_data_to_db(minute_data_with_signals, INDICATORS_TABLE_NAME)
        # Write the signals to the minute signals table
        write_signals_to_minute_signals_table(minute_data_with_signals)