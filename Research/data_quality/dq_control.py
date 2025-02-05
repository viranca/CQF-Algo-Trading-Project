import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# Database connection parameters
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "research"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
YFINANCE_DAILY_TABLE_NAME = "yfinance_daily"
YFINANCE_MINUTE_TABLE_NAME = "yfinance_minute"
ALPACA_DAILY_TABLE_NAME = "alpaca_daily"
ALPACA_MINUTE_TABLE_NAME = "alpaca_minute"

def fetch_data_from_db(table_name):
    """Fetch data from the PostgreSQL database for the specified table."""
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
        
        # Query to fetch all data from the specified table
        query = f"SELECT * FROM {table_name};"
        
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

def data_quality_assessment(yfinance_df, alpaca_df):
    """Perform data quality assessment and comparison between yfinance and alpaca data for each ticker."""
    if yfinance_df is None or alpaca_df is None:
        print("Data not available for quality assessment.")
        return

    # Get unique tickers from both datasets
    yfinance_tickers = yfinance_df['ticker'].unique()
    alpaca_tickers = alpaca_df['ticker'].unique()
    
    # Find common tickers
    common_tickers = set(yfinance_tickers).intersection(set(alpaca_tickers))
    
    # Initialize a list to collect results
    results_list = []
    
    for ticker in common_tickers:
        # Filter data for the current ticker
        yfinance_ticker_data = yfinance_df[yfinance_df['ticker'] == ticker]
        alpaca_ticker_data = alpaca_df[alpaca_df['ticker'] == ticker]
        
        # Collect missing values
        missing_values_yfinance = yfinance_ticker_data.isnull().sum()
        missing_values_alpaca = alpaca_ticker_data.isnull().sum()

        # Collect duplicate counts
        duplicates_yfinance = yfinance_ticker_data.duplicated().sum()
        duplicates_alpaca = alpaca_ticker_data.duplicated().sum()

        # Collect basic statistics
        stats_yfinance = yfinance_ticker_data.describe()
        stats_alpaca = alpaca_ticker_data.describe()

        # Collect data ranges
        range_yfinance = yfinance_ticker_data.agg(['min', 'max'])
        range_alpaca = alpaca_ticker_data.agg(['min', 'max'])

        # Collect data consistency
        consistency_results = {}
        common_columns = set(yfinance_ticker_data.columns).intersection(set(alpaca_ticker_data.columns))
        for column in common_columns:
            if pd.api.types.is_numeric_dtype(yfinance_ticker_data[column]) and pd.api.types.is_numeric_dtype(alpaca_ticker_data[column]):
                mean_diff = (yfinance_ticker_data[column] - alpaca_ticker_data[column]).mean()
                correlation = yfinance_ticker_data[column].corr(alpaca_ticker_data[column])
                consistency_results[column] = {'mean_diff': mean_diff, 'correlation': correlation}

        # Append results to the list
        results_list.append({
            'ticker': ticker,
            'missing_values_yfinance': missing_values_yfinance,
            'missing_values_alpaca': missing_values_alpaca,
            'duplicates_yfinance': duplicates_yfinance,
            'duplicates_alpaca': duplicates_alpaca,
            'stats_yfinance': stats_yfinance,
            'stats_alpaca': stats_alpaca,
            'range_yfinance': range_yfinance,
            'range_alpaca': range_alpaca,
            'consistency_results': consistency_results
        })
    
    # Convert results list to a DataFrame for better visualization
    results_df = pd.DataFrame(results_list)
    print(results_df)

    # Plotting missing values for all tickers in a single plot
    plt.figure(figsize=(15, 7))
    for ticker in common_tickers:
        yfinance_missing = results_df.loc[results_df['ticker'] == ticker, 'missing_values_yfinance'].values[0]
        alpaca_missing = results_df.loc[results_df['ticker'] == ticker, 'missing_values_alpaca'].values[0]
        
        plt.bar(yfinance_missing.index, yfinance_missing.values, alpha=0.5, label=f'{ticker} YFinance Missing')
        plt.bar(alpaca_missing.index, alpaca_missing.values, alpha=0.5, label=f'{ticker} Alpaca Missing')
    
    plt.title('Missing Values for Common Tickers')
    plt.xlabel('Columns')
    plt.ylabel('Missing Count')
    plt.legend()
    plt.show()

# Fetch data from the database
yfinance_daily_data = fetch_data_from_db(YFINANCE_DAILY_TABLE_NAME)
yfinance_minute_data = fetch_data_from_db(YFINANCE_MINUTE_TABLE_NAME)
alpaca_daily_data = fetch_data_from_db(ALPACA_DAILY_TABLE_NAME)
alpaca_minute_data = fetch_data_from_db(ALPACA_MINUTE_TABLE_NAME)

# Perform data quality assessment
print("Daily Data Quality Assessment:")
data_quality_assessment(yfinance_daily_data, alpaca_daily_data)

print("\nMinute Data Quality Assessment:")
data_quality_assessment(yfinance_minute_data, alpaca_minute_data)
