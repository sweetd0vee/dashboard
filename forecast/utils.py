from datetime import datetime, timezone
import pandas as pd


def now_utc():
    return datetime.now(timezone.utc)


def safe_mape(y_true, y_pred, epsilon=1e-10):
    y_true_safe = y_true.copy()
    y_true_safe = y_true_safe.where(y_true_safe != 0, epsilon)
    return (abs((y_true - y_pred) / y_true_safe)).mean() * 100


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['hour'] = df['ds'].dt.hour
    df['is_work_hours'] = df['hour'].between(9, 18).astype(float)
    df['is_night'] = df['hour'].between(0, 6).astype(float)
    df['day_of_week'] = df['ds'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(float)
    return df
