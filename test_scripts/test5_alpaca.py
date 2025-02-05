import psycopg2
import pandas as pd

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
MINUTE_TABLE_NAME = "alpaca_minute"
DAILY_TABLE_NAME = "alpaca_daily"

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

# Example usage
if __name__ == "__main__":
    minute_query = f"SELECT * FROM {MINUTE_TABLE_NAME};"
    daily_query = f"SELECT * FROM {DAILY_TABLE_NAME};"
    
    minute_data = fetch_data_from_db(minute_query)
    daily_data = fetch_data_from_db(daily_query)
    
    if minute_data is not None:
        print("Minute Data:")
        print(minute_data)
    
    if daily_data is not None:
        print("Daily Data:")
        print(daily_data)
