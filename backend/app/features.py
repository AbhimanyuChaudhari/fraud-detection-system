import pandas as pd
import numpy as np
from datetime import datetime


# Features we use from IEEE-CIS that work well for real-time scoring
FEATURE_COLS = [
    'TransactionAmt', 'ProductCD', 'card4', 'card6',
    'P_emaildomain', 'R_emaildomain', 'DeviceType',
    'TransactionAmt_log', 'TransactionAmt_zscore',
    'hour', 'day_of_week', 'is_weekend', 'is_night',
    'amt_round', 'decimal_part',
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all feature engineering to a dataframe of transactions.
    Works on both training data and single real-time transactions.
    """
    df = df.copy()

    # ── Amount features ──────────────────────────────────────────────────────
    df['TransactionAmt_log'] = np.log1p(df['TransactionAmt'])
    mean_amt = df['TransactionAmt'].mean()
    std_amt  = df['TransactionAmt'].std() + 1e-9
    df['TransactionAmt_zscore'] = (df['TransactionAmt'] - mean_amt) / std_amt
    df['amt_round']    = (df['TransactionAmt'] % 1 == 0).astype(int)
    df['decimal_part'] = df['TransactionAmt'] % 1

    # ── Time features ─────────────────────────────────────────────────────────
    # TransactionDT is seconds offset from a reference point
    df['hour']        = (df['TransactionDT'] / 3600 % 24).astype(int)
    df['day_of_week'] = (df['TransactionDT'] / 86400 % 7).astype(int)
    df['is_weekend']  = (df['day_of_week'] >= 5).astype(int)
    df['is_night']    = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)

    # ── Categorical encoding ──────────────────────────────────────────────────
    cat_cols = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain', 'DeviceType']
    for col in cat_cols:
        if col in df.columns:
            df[col] = pd.Categorical(df[col]).codes
        else:
            df[col] = -1

    return df


def engineer_single(transaction: dict, global_stats: dict = None) -> dict:
    """
    Engineer features for a single real-time transaction.
    global_stats: { mean_amt, std_amt } precomputed from training data.
    """
    amt = transaction.get('TransactionAmt', 0)
    dt  = transaction.get('TransactionDT', 0)

    mean_amt = global_stats.get('mean_amt', 500) if global_stats else 500
    std_amt  = global_stats.get('std_amt', 400)  if global_stats else 400

    features = {
        'TransactionAmt':        amt,
        'TransactionAmt_log':    np.log1p(amt),
        'TransactionAmt_zscore': (amt - mean_amt) / (std_amt + 1e-9),
        'amt_round':             int(amt % 1 == 0),
        'decimal_part':          amt % 1,
        'hour':                  int((dt / 3600) % 24),
        'day_of_week':           int((dt / 86400) % 7),
        'is_weekend':            int((dt / 86400) % 7 >= 5),
        'is_night':              int(((dt / 3600) % 24 >= 22) or ((dt / 3600) % 24 <= 6)),
        'ProductCD':             hash(transaction.get('ProductCD', '')) % 5,
        'card4':                 hash(transaction.get('card4', '')) % 10,
        'card6':                 hash(transaction.get('card6', '')) % 5,
        'P_emaildomain':         hash(transaction.get('P_emaildomain', '')) % 50,
        'R_emaildomain':         hash(transaction.get('R_emaildomain', '')) % 50,
        'DeviceType':            hash(transaction.get('DeviceType', '')) % 3,
    }
    return features
