import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
INDICATORS_TABLE_NAME = "ticker_daily_indicators"

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
    indicators_query = f"SELECT * FROM {INDICATORS_TABLE_NAME};"
    
    indicators_data = fetch_data_from_db(indicators_query)
    
    if indicators_data is not None:
        print("Daily Indicators Data:")
        print(indicators_data)                          

        ticker = 'AAPL'  # Specify the ticker you want to plot

        # Filter data for the specific ticker
        ticker_data = indicators_data[indicators_data['ticker'] == ticker]

        if not ticker_data.empty:
            print(f"Data for {ticker}:")
            print(ticker_data)

            # Plot the close price and EMAs
            plt.figure(figsize=(14, 7))
            plt.plot(ticker_data['datetime'], ticker_data['close'], label='Close Price', color='black')
            plt.plot(ticker_data['datetime'], ticker_data['ema_10'], label='EMA 10', color='blue')
            plt.plot(ticker_data['datetime'], ticker_data['ema_20'], label='EMA 20', color='red')
            plt.plot(ticker_data['datetime'], ticker_data['ema_50'], label='EMA 50', color='green')
            plt.title(f"Close Price and EMAs for {ticker}")
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Plot ADX and DI
            plt.figure(figsize=(14, 7))
            plt.plot(ticker_data['datetime'], ticker_data['adx'], label='ADX', color='purple')
            plt.plot(ticker_data['datetime'], ticker_data['plus_di'], label='+DI', color='green')
            plt.plot(ticker_data['datetime'], ticker_data['minus_di'], label='-DI', color='red')
            plt.title(f"ADX and DI for {ticker}")
            plt.xlabel('Date')
            plt.ylabel('Value')
            plt.legend()
            plt.grid(True)
            plt.show()
        else:
            print(f"No data available for ticker {ticker}.")
