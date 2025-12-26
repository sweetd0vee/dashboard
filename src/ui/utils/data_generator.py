import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_server_data():
    """Генерация тестовых данных серверов"""
    servers = [
        "Web-Server-01", "Web-Server-02", "API-Server-01",
        "API-Server-02", "Database-01", "Database-02",
        "Cache-Server-01", "Load-Balancer-01", "File-Server-01",
        "Analytics-Server-01"
    ]

    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='H')
    data = []

    for server in servers:
        server_type = server.split('-')[0]

        for date in dates:
            base_load = np.random.normal(50, 15)

            # Сезонность
            hour = date.hour
            if 9 <= hour <= 17:
                base_load += np.random.normal(20, 5)
            elif 18 <= hour <= 22:
                base_load += np.random.normal(10, 3)
            else:
                base_load -= np.random.normal(15, 5)

            noise = np.random.normal(0, 5)
            load = max(5, min(100, base_load + noise))

            # Метрики
            cpu_usage = load * 0.8 + np.random.normal(10, 5)
            memory_usage = load * 0.6 + np.random.normal(20, 10)
            network_in = load * 10 + np.random.normal(100, 30)

            # Дополнительные метрики для алертов
            cpu_ready_summation = np.random.uniform(0, 20)  # 0-20%
            disk_latency = np.random.uniform(5, 35)  # 5-35 ms
            disk_usage = load * 0.7 + np.random.normal(15, 8)

            data.append({
                'server': server,
                'timestamp': date,
                'load_percentage': load,
                'cpu_usage': min(100, cpu_usage),
                'memory_usage': min(100, memory_usage),
                'network_in_mbps': max(0, network_in),
                'cpu_ready_summation': cpu_ready_summation,
                'disk_latency': disk_latency,
                'disk_usage': min(100, disk_usage),
                'errors': np.random.poisson(0.1),
                'server_type': server_type
            })

    return pd.DataFrame(data)


def generate_forecast(historical_data, hours=48):
    """Генерация прогноза"""
    if historical_data.empty:
        return pd.DataFrame()

    last_date = historical_data['timestamp'].max()
    forecast_dates = [last_date + timedelta(hours=i) for i in range(1, hours + 1)]

    last_values = historical_data['load_percentage'].tail(24).values
    base_forecast = np.mean(last_values)

    forecast_values = []
    for i, date in enumerate(forecast_dates):
        hour = date.hour
        if 9 <= hour <= 17:
            seasonality = np.random.normal(15, 3)
        elif 18 <= hour <= 22:
            seasonality = np.random.normal(8, 2)
        else:
            seasonality = np.random.normal(-10, 3)

        trend = i * 0.02
        forecast_val = base_forecast + seasonality + trend
        forecast_val = max(5, min(100, forecast_val))
        forecast_values.append(forecast_val)

    return pd.DataFrame({
        'timestamp': forecast_dates,
        'load_percentage': forecast_values
    })