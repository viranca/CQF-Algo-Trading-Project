def compute_adx(df, span=14):
    """
    Compute the Average Directional Index (ADX) for each ticker in a specified window.

    Parameters:
    df (pd.DataFrame): DataFrame containing columns ['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume']
    span (int): The span for the ADX calculation.

    Returns:
    pd.DataFrame: DataFrame with additional columns representing the ADX, +DI, and -DI for each ticker.
    """
    # Ensure the DataFrame is sorted by datetime
    df = df.sort_values(by='datetime')

    # Calculate True Range (TR)
    df['prev_close'] = df.groupby('ticker')['close'].shift(1)
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = (df['high'] - df['prev_close']).abs()
    df['low_prev_close'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)

    # Calculate Directional Movement (+DM, -DM)
    df['prev_high'] = df.groupby('ticker')['high'].shift(1)
    df['prev_low'] = df.groupby('ticker')['low'].shift(1)
    df['+dm'] = df['high'] - df['prev_high']
    df['-dm'] = df['prev_low'] - df['low']
    df['+dm'] = df.apply(lambda row: row['+dm'] if row['+dm'] > row['-dm'] and row['+dm'] > 0 else 0, axis=1)
    df['-dm'] = df.apply(lambda row: row['-dm'] if row['-dm'] > row['+dm'] and row['-dm'] > 0 else 0, axis=1)

    # Calculate smoothed TR, +DM, -DM
    df['atr'] = df.groupby('ticker')['tr'].transform(lambda x: x.ewm(span=span, adjust=False).mean())
    df['+di'] = 100 * df.groupby('ticker')['+dm'].transform(lambda x: x.ewm(span=span, adjust=False).mean()) / df['atr']
    df['-di'] = 100 * df.groupby('ticker')['-dm'].transform(lambda x: x.ewm(span=span, adjust=False).mean()) / df['atr']

    # Calculate DX and ADX
    df['dx'] = (abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])) * 100
    df['adx'] = df.groupby('ticker')['dx'].transform(lambda x: x.ewm(span=span, adjust=False).mean())

    # Drop intermediate columns
    df.drop(['prev_close', 'high_low', 'high_prev_close', 'low_prev_close', 'tr', 'prev_high', 'prev_low', '+dm', '-dm', 'atr', 'dx'], axis=1, inplace=True)

    return df
