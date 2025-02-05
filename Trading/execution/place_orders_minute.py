import psycopg2
import pandas as pd
import alpaca_trade_api as tradeapi

# Database connection parameters
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
MINUTE_SIGNAL_TABLE_NAME = "ticker_minute_signals"
PORTFOLIO_TABLE_NAME = "portfolio_orders"

# Alpaca API credentials
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"
APCA_API_KEY_ID = "removed"
APCA_API_SECRET_KEY = "removed"

# Initialize the Alpaca API
api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL, api_version='v2')

def fetch_minute_signal_table():
    """Fetch minute signal table from the PostgreSQL database."""
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
        
        # Query to fetch data from the minute signal table
        signal_query = f"SELECT * FROM {MINUTE_SIGNAL_TABLE_NAME};"
        cursor.execute(signal_query)
        results = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        minute_signal_df = pd.DataFrame(results, columns=colnames)
        
        return minute_signal_df

    except psycopg2.Error as e:
        print(f"Error fetching minute signal table from PostgreSQL database: {e}")
        return None
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def place_orders(minute_signal_df):
    """Place orders using the Alpaca API based on the signals and trends."""
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

        for index, row in minute_signal_df.iterrows():
            signal = row['signal']
            symbol = row['symbol']
            price = row['close']
            trend = row.get('trend', None)  # Assuming 'trend' column exists

            order_side = None

            # Determine if a buy order should be placed
            if signal == 'buy' or (trend and trend.lower() == 'uptrend'):
                order_side = 'buy'
            # Determine if a sell order should be placed
            elif signal == 'sell' or (trend and trend.lower() == 'downtrend'):
                order_side = 'sell'

            if order_side:
                try:
                    api.submit_order(
                        symbol=symbol,
                        qty=1,
                        side=order_side,
                        type='market',
                        time_in_force='gtc'
                    )
                    print(f"Placed {order_side} order for {symbol} at {price}")

                    # Insert order into portfolio table
                    insert_query = f"""
                    INSERT INTO {PORTFOLIO_TABLE_NAME} (symbol, side, price, timestamp)
                    VALUES (%s, %s, %s, NOW());
                    """
                    cursor.execute(insert_query, (symbol, order_side, price))
                    connection.commit()

                except Exception as e:
                    print(f"Failed to place {order_side} order for {symbol}: {e}")

    except psycopg2.Error as e:
        print(f"Error interacting with PostgreSQL database: {e}")
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Example usage
minute_signal_data = fetch_minute_signal_table()
if minute_signal_data is not None:
    print("Data from minute signal table:")
    print(minute_signal_data)
    place_orders(minute_signal_data)
