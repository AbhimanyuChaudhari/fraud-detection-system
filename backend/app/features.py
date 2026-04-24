import numpy as np


def engineer_single(transaction: dict, global_stats: dict = None) -> dict:
    """
    Engineer features for a single real-time transaction.
    Matches the feature set used in training.
    """
    amt      = float(transaction.get('TransactionAmt', 0))
    dt       = float(transaction.get('TransactionDT', 0))
    mean_amt = global_stats.get('mean_amt', 500) if global_stats else 500
    std_amt  = global_stats.get('std_amt',  400) if global_stats else 400

    features = {
        # Amount
        'TransactionAmt':        amt,
        'TransactionAmt_log':    np.log1p(amt),
        'TransactionAmt_zscore': (amt - mean_amt) / (std_amt + 1e-9),
        'amt_round':             int(amt % 1 == 0),
        'decimal_part':          amt % 1,
        'amt_cents':             int(amt * 100 % 100),

        # Time
        'hour':        int((dt / 3600) % 24),
        'day_of_week': int((dt / 86400) % 7),
        'is_weekend':  int((dt / 86400) % 7 >= 5),
        'is_night':    int(((dt / 3600) % 24 >= 22) or ((dt / 3600) % 24 <= 6)),
        'is_morning':  int(6 <= (dt / 3600) % 24 <= 10),

        # Categorical
        'ProductCD':      hash(str(transaction.get('ProductCD', '')))     % 5,
        'card4':          hash(str(transaction.get('card4', '')))          % 10,
        'card6':          hash(str(transaction.get('card6', '')))          % 5,
        'P_emaildomain':  hash(str(transaction.get('P_emaildomain', ''))) % 50,
        'R_emaildomain':  hash(str(transaction.get('R_emaildomain', ''))) % 50,
        'DeviceType':     hash(str(transaction.get('DeviceType', '')))    % 3,
        'DeviceInfo':     hash(str(transaction.get('DeviceInfo', '')))    % 100,

        # Card
        'card1': float(transaction.get('card1', -999) or -999),
        'card2': float(transaction.get('card2', -999) or -999),
        'card3': float(transaction.get('card3', -999) or -999),
        'card5': float(transaction.get('card5', -999) or -999),

        # Address
        'addr1': float(transaction.get('addr1', -999) or -999),
        'addr2': float(transaction.get('addr2', -999) or -999),

        # Distance
        'dist1':     float(transaction.get('dist1', -999) or -999),
        'dist2':     float(transaction.get('dist2', -999) or -999),
        'dist1_log': np.log1p(float(transaction.get('dist1', 0) or 0)),
        'dist2_log': np.log1p(float(transaction.get('dist2', 0) or 0)),
    }

    # Fill V features and id features with -999 (not available in real-time)
    feature_cols = global_stats.get('feature_cols', []) if global_stats else []
    for col in feature_cols:
        if col not in features:
            features[col] = -999

    return features
