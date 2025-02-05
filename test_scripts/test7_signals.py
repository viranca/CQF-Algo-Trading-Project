import psycopg2
import pandas as pd

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
MINUTE_SIGNALS_TABLE_NAME = "ticker_minute_signals"
DAILY_SIGNALS_TABLE_NAME = "ticker_daily_signals"

def fetch_all_signals():
    """Fetch all trading signals from the PostgreSQL database."""
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
        
        # Query to fetch all minute signals
        minute_query = f"SELECT * FROM {MINUTE_SIGNALS_TABLE_NAME};"
        
        # Execute the query
        cursor.execute(minute_query)
        
        # Fetch all minute results
        minute_results = cursor.fetchall()
        
        # Get column names for minute signals
        minute_colnames = [desc[0] for desc in cursor.description]
        
        # Create a DataFrame for minute signals
        minute_df = pd.DataFrame(minute_results, columns=minute_colnames)
        
        # Query to fetch all daily signals
        daily_query = f"SELECT * FROM {DAILY_SIGNALS_TABLE_NAME};"
        
        # Execute the query
        cursor.execute(daily_query)
        
        # Fetch all daily results
        daily_results = cursor.fetchall()
        
        # Get column names for daily signals
        daily_colnames = [desc[0] for desc in cursor.description]
        
        # Create a DataFrame for daily signals
        daily_df = pd.DataFrame(daily_results, columns=daily_colnames)
        
        return minute_df, daily_df

    except psycopg2.Error as e:
        print(f"Error fetching signals from PostgreSQL database: {e}")
        return None, None
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Example usage
if __name__ == "__main__":
    minute_signals_data, daily_signals_data = fetch_all_signals()
    
    if minute_signals_data is not None and daily_signals_data is not None:
        print("Minute Signals Data:")
        print(minute_signals_data)
        print("Daily Signals Data:")
        print(daily_signals_data)
