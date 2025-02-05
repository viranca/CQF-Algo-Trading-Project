def compute_ema(df, span=14):
    """
    Compute the Exponential Moving Average (EMA) for each ticker in a specified window.

    Parameters:
    df (pd.DataFrame): DataFrame containing columns ['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume']
    span (int): The span for the EMA calculation.

    Returns:
    pd.DataFrame: DataFrame with an additional column representing the EMA for each ticker, named 'ema_<span>'.
    """
    # Ensure the DataFrame is sorted by datetime
    df = df.sort_values(by='datetime')

    # Define the column name based on the span
    ema_column_name = f'ema_{span}'

    # Group by ticker and calculate the EMA for the 'close' price
    df[ema_column_name] = df.groupby('ticker')['close'].transform(lambda x: x.ewm(span=span, adjust=False).mean())

    return df
