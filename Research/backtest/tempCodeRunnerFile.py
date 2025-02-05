import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
TICKER_MINUTE_INDICATORS_TABLE_NAME = "ticker_minute_indicators"

def fetch_minute_indicator_data():
    """Fetch ticker minute indicator data from the PostgreSQL database."""
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
        
        # Query to fetch all data from the ticker minute indicators table
        minute_query = f"SELECT * FROM {TICKER_MINUTE_INDICATORS_TABLE_NAME};"
        cursor.execute(minute_query)
        minute_results = cursor.fetchall()
        minute_colnames = [desc[0] for desc in cursor.description]
        minute_df = pd.DataFrame(minute_results, columns=minute_colnames)
        
        return minute_df

    except psycopg2.Error as e:
        print(f"Error fetching ticker minute indicator data from PostgreSQL database: {e}")
        return None
    finally:
        # Close the cursor and connection
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def backtrade_with_trend(minute_df):
    """Perform backtrading using the trend column in the DataFrame and compute backtesting metrics."""
    if 'trend' not in minute_df.columns:
        print("No trend column found in the data.")
        return

    # Initialize variables for backtrading
    cash = 10000  # Starting cash
    position = 0  # Current position (number of shares)
    portfolio_value = cash
    trades = 0
    wins = 0
    losses = 0
    max_drawdown = 0
    peak_value = cash
    returns = []
    cash_history = []
    drawdown_history = []
    sortino_history = []
    sharpe_history = []

    # Iterate over each row in the DataFrame
    for index, row in minute_df.iterrows():
        trend = row['trend']
        price = row['close']

        if trend == 'uptrend' and cash >= price:
            # Buy one share
            position += 1
            cash -= price
            trades += 1
            print(f"Buying at {price}, Cash: {cash}, Position: {position}")

        elif trend == 'downtrend' and position > 0:
            # Sell one share
            position -= 1
            cash += price
            trades += 1
            print(f"Selling at {price}, Cash: {cash}, Position: {position}")

            # Determine if the trade was a win or a loss
            if price > minute_df.iloc[index - 1]['close']:
                wins += 1
            else:
                losses += 1

        # Update peak value and calculate drawdown
        current_value = cash + position * price
        if current_value > peak_value:
            peak_value = current_value
        drawdown = (peak_value - current_value) / peak_value
        drawdown_history.append(drawdown)
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        # Calculate returns for Sortino and Sharpe Ratios
        if index > 0:
            prev_value = cash + position * minute_df.iloc[index - 1]['close']
            returns.append((current_value - prev_value) / prev_value)

        # Record cash history for plotting
        cash_history.append(cash)

        # Calculate Sortino and Sharpe Ratios
        if len(returns) > 1:
            downside_returns = [r for r in returns if r < 0]
            expected_return = np.mean(returns)
            downside_deviation = np.sqrt(np.mean(np.square(downside_returns))) if downside_returns else np.nan
            sortino_ratio = expected_return / downside_deviation if downside_deviation != 0 else np.nan
            sortino_history.append(sortino_ratio)

            sharpe_ratio = expected_return / np.std(returns) if np.std(returns) != 0 else np.nan
            sharpe_history.append(sharpe_ratio)

    # Calculate final portfolio value
    portfolio_value = cash + position * minute_df.iloc[-1]['close']
    print(f"Final Portfolio Value: {portfolio_value}")

    # Compute backtesting metrics
    total_return = (portfolio_value - 10000) / 10000 * 100
    win_rate = (wins / trades) * 100 if trades > 0 else 0
    print(f"Total Return: {total_return:.2f}%")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Number of Trades: {trades}")
    print(f"Win Rate: {win_rate:.2f}%")

    # Compute rolling Value at Risk (VaR)
    if len(returns) > 0:
        rolling_var = np.percentile(returns, 5)
    else:
        rolling_var = np.nan
    print(f"Rolling VaR (5%): {rolling_var:.2f}")
    # Combine plots into a single figure with subplots
    fig, axs = plt.subplots(3, 1, figsize=(7, 18))

    # Plot Ticker Price
    axs[0].plot(minute_df.index, minute_df['close'], label='Ticker Price')
    axs[0].set_title('Ticker Price')
    axs[0].legend()

    # Plot Trading Trend
    axs[1].plot(minute_df.index, minute_df['trend'].apply(lambda x: 1 if x == 'uptrend' else -1 if x == 'downtrend' else 0), label='Trend')
    axs[1].set_title('Trading Trend')
    axs[1].legend()

    # Plot Cash Over Time
    axs[2].plot(minute_df.index, cash_history, label='Cash')
    axs[2].set_title('Cash Over Time')
    axs[2].legend()

    # Adjust layout and show the combined plot
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(7, 6))
    plt.plot(minute_df.index, [-d for d in drawdown_history], label='Drawdown')
    plt.title('Drawdown Over Time')
    plt.legend()
    plt.show()

    # Remove the initial couple of hours of Sortino and Sharpe ratios
    start_index = 120  # Assuming 2 hours of data with minute intervals
    plt.figure(figsize=(7, 6))
    plt.plot(minute_df.index[start_index+2:], sortino_history[start_index:], label='Sortino Ratio')
    plt.title('Sortino Ratio Over Time')
    plt.legend()
    plt.show()

    plt.figure(figsize=(7, 6))
    plt.plot(minute_df.index[start_index+2:], sharpe_history[start_index:], label='Sharpe Ratio')
    plt.title('Sharpe Ratio Over Time')
    plt.legend()
    plt.show()

# Example usage
ticker_minute_data = fetch_minute_indicator_data()

if ticker_minute_data is not None:
    print("Ticker Minute Indicator Data:")
    print(ticker_minute_data)
    backtrade_with_trend(ticker_minute_data)
