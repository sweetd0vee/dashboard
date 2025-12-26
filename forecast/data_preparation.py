import pandas as pd
import logging
from typing import List, Dict
from .utils import add_time_features, now_utc


logger = logging.getLogger(__name__)


def prepare_data(data: List[Dict]) -> pd.DataFrame:
    if not data:
        raise ValueError("No data provided for preparation")

    df = pd.DataFrame(data)
    df = df.rename(columns={'timestamp': 'ds', 'value': 'y'})
    df['ds'] = pd.to_datetime(df['ds'], utc=True)

    df['ds'] = df['ds'].dt.tz_localize(None)

    df = df.sort_values('ds').reset_index(drop=True)

    if df['y'].isnull().any():
        logger.warning(f"Found {df['y'].isnull().sum()} missing values, filling with interpolation")
        df['y'] = df['y'].interpolate(method='linear').bfill().ffill()

    df = add_time_features(df)

    if len(df) > 1:
        time_diff = df['ds'].diff().mode()[0]
        logger.info(f"Main time interval: {time_diff}")

    return df