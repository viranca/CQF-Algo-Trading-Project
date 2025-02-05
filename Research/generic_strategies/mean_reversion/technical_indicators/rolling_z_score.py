import pandas as pd

def calculate_rolling_z_score(df, window=20):
    """
    Calculate the rolling z-score for the 'close' prices in the given DataFrame.

    Parameters:
    - df: DataFrame containing at least the 'close' column.
    - window: The rolling window size for calculating the mean and standard deviation.

    Returns:
    - DataFrame with an additional 'z_score' column.
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column")

    # Calculate rolling mean and standard deviation
    rolling_mean = df['close'].rolling(window=window).mean()
    rolling_std = df['close'].rolling(window=window).std()

    # Calculate z-score
    df['z_score'] = (df['close'] - rolling_mean) / rolling_std

    return df

# Example usage
if __name__ == "__main__":
    # Sample data
    data = {
        'datetime': pd.date_range(start='2023-01-01', periods=30, freq='D'),
        'open': [100 + i for i in range(30)],
        'high': [105 + i for i in range(30)],
        'low': [95 + i for i in range(30)],
        'close': [102 + i for i in range(30)]
    }
    df = pd.DataFrame(data)

    # Calculate rolling z-score
    df_with_z_score = calculate_rolling_z_score(df)
    print(df_with_z_score)
