from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class ServerStatus(Enum):
    """Статус сервера"""
    OVERLOADED = "overloaded"  # Загружен
    UNDERLOADED = "underloaded"  # Простаивает
    NORMAL = "normal"  # Норма
    UNKNOWN = "unknown"  # Неизвестно


class AlertSeverity(Enum):
    """Уровень серьезности алерта"""
    CRITICAL = "critical"  # Критический
    WARNING = "warning"  # Предупреждение
    INFO = "info"  # Информационный


@dataclass
class AlertRule:
    """Правило для алерта"""
    name: str
    metric: str
    condition: str  # 'gt' (greater than), 'lt' (less than), 'range'
    thresholds: Dict
    severity: AlertSeverity
    description: str
    time_percentage: float = 0.2  # Процент времени для анализа (20% по умолчанию)


@dataclass
class Alert:
    """Алерт"""
    rule: AlertRule
    value: float
    timestamp: pd.Timestamp
    server: str
    message: str

    def to_dict(self):
        return {
            'server': self.server,
            'rule': self.rule.name,
            'value': self.value,
            'threshold': self.rule.thresholds,
            'severity': self.rule.severity.value,
            'timestamp': self.timestamp,
            'message': self.message
        }


class AlertSystem:
    """Система алертов"""

    def __init__(self):
        self.rules = self._get_default_rules()
        self.alerts_history = []

    def _get_default_rules(self) -> List[AlertRule]:
        """Получение правил по умолчанию"""
        return [
            # Правила для загруженного сервера
            AlertRule(
                name="high_cpu_usage",
                metric="cpu_usage",
                condition="gt",
                thresholds={'high': 85},
                severity=AlertSeverity.CRITICAL,
                description="Среднее использование CPU >85%",
                time_percentage=0.2
            ),
            AlertRule(
                name="high_memory_usage",
                metric="memory_usage",
                condition="gt",
                thresholds={'high': 80},
                severity=AlertSeverity.CRITICAL,
                description="Среднее использование памяти >80%",
                time_percentage=0.2
            ),
            AlertRule(
                name="cpu_ready_time",
                metric="cpu_ready_summation",
                condition="gt",
                thresholds={'high': 10},
                severity=AlertSeverity.CRITICAL,
                description="Сумма времени ожидания CPU >10% (в топ-20% пиковых интервалов)",
                time_percentage=0.2
            ),

            # Правила для простаивающего сервера
            AlertRule(
                name="low_cpu_usage",
                metric="cpu_usage",
                condition="lt",
                thresholds={'low': 15},
                severity=AlertSeverity.WARNING,
                description="Среднее использование CPU <15%",
                time_percentage=0.8
            ),
            AlertRule(
                name="low_memory_usage",
                metric="memory_usage",
                condition="lt",
                thresholds={'low': 25},
                severity=AlertSeverity.WARNING,
                description="Среднее использование памяти <25%",
                time_percentage=0.8
            ),
            AlertRule(
                name="low_network_usage",
                metric="network_usage_percent",
                condition="lt",
                thresholds={'low': 5},
                severity=AlertSeverity.WARNING,
                description="Среднее использование сети <5% от ёмкости",
                time_percentage=0.8
            ),

            # Правила для нормальной работы
            AlertRule(
                name="normal_cpu_range",
                metric="cpu_usage",
                condition="range",
                thresholds={'low': 15, 'high': 85},
                severity=AlertSeverity.INFO,
                description="Нормальный диапазон CPU: 15-85%",
                time_percentage=1.0
            ),
            AlertRule(
                name="normal_memory_range",
                metric="memory_usage",
                condition="range",
                thresholds={'low': 25, 'high': 85},
                severity=AlertSeverity.INFO,
                description="Нормальный диапазон памяти: 25-85%",
                time_percentage=1.0
            ),
            AlertRule(
                name="normal_network_range",
                metric="network_usage_percent",
                condition="range",
                thresholds={'low': 6, 'high': 85},
                severity=AlertSeverity.INFO,
                description="Нормальный диапазон сети: 6-85%",
                time_percentage=1.0
            ),

            # Дополнительные правила
            AlertRule(
                name="high_disk_latency",
                metric="disk_latency",
                condition="gt",
                thresholds={'high': 25},
                severity=AlertSeverity.CRITICAL,
                description="Высокая задержка диска >25ms",
                time_percentage=0.2
            )
        ]

    def analyze_server_status(self, server_data: pd.DataFrame, server_name: str) -> Dict:
        """Анализ статуса сервера"""
        if server_data.empty:
            return {'status': ServerStatus.UNKNOWN, 'alerts': []}

        # Добавляем метрику использования сети в процентах
        if 'network_in_mbps' in server_data.columns:
            # Предполагаем, что емкость сети = 1000 Mbps
            network_capacity = 1000
            server_data['network_usage_percent'] = (server_data['network_in_mbps'] / network_capacity) * 100

        # Добавляем фиктивные метрики для примера
        if 'cpu_ready_summation' not in server_data.columns:
            server_data['cpu_ready_summation'] = np.random.uniform(0, 15, len(server_data))

        if 'disk_latency' not in server_data.columns:
            server_data['disk_latency'] = np.random.uniform(5, 30, len(server_data))

        alerts = []

        # Проверяем каждое правило
        for rule in self.rules:
            if rule.metric not in server_data.columns:
                continue

            metric_data = server_data[rule.metric]
            total_intervals = len(metric_data)
            required_intervals = int(total_intervals * rule.time_percentage)

            if rule.condition == "gt":
                # Больше порога
                exceeding_count = (metric_data > rule.thresholds['high']).sum()
                if exceeding_count >= required_intervals:
                    avg_value = metric_data[metric_data > rule.thresholds['high']].mean()
                    alert = Alert(
                        rule=rule,
                        value=avg_value,
                        timestamp=server_data['timestamp'].iloc[-1],
                        server=server_name,
                        message=f"{rule.description}: {avg_value:.1f}% (порог: {rule.thresholds['high']}%)"
                    )
                    alerts.append(alert)

            elif rule.condition == "lt":
                # Меньше порога
                below_count = (metric_data < rule.thresholds['low']).sum()
                if below_count >= required_intervals:
                    avg_value = metric_data[metric_data < rule.thresholds['low']].mean()
                    alert = Alert(
                        rule=rule,
                        value=avg_value,
                        timestamp=server_data['timestamp'].iloc[-1],
                        server=server_name,
                        message=f"{rule.description}: {avg_value:.1f}% (порог: {rule.thresholds['low']}%)"
                    )
                    alerts.append(alert)

            elif rule.condition == "range":
                # В диапазоне
                in_range_count = (
                        (metric_data >= rule.thresholds['low']) &
                        (metric_data <= rule.thresholds['high'])
                ).sum()
                if in_range_count == total_intervals:
                    avg_value = metric_data.mean()
                    alert = Alert(
                        rule=rule,
                        value=avg_value,
                        timestamp=server_data['timestamp'].iloc[-1],
                        server=server_name,
                        message=f"{rule.description}: {avg_value:.1f}% (диапазон: {rule.thresholds['low']}-{rule.thresholds['high']}%)"
                    )
                    alerts.append(alert)

        # Определяем общий статус сервера
        status = self._determine_server_status(alerts, server_data)

        # Сохраняем алерты в историю
        for alert in alerts:
            self.alerts_history.append(alert.to_dict())

        return {
            'status': status,
            'alerts': alerts,
            'metrics_summary': self._get_metrics_summary(server_data)
        }

    def _determine_server_status(self, alerts: List[Alert], server_data: pd.DataFrame) -> ServerStatus:
        """Определение общего статуса сервера"""
        if not alerts:
            return ServerStatus.NORMAL

        # Проверяем на перегрузку
        overload_alerts = [a for a in alerts if a.rule.severity == AlertSeverity.CRITICAL]
        overload_metrics = ['cpu_usage', 'memory_usage', 'cpu_ready_summation']
        overload_count = sum(1 for alert in overload_alerts if alert.rule.metric in overload_metrics)

        if overload_count >= 1:  # Хотя бы одно правило перегрузки
            return ServerStatus.OVERLOADED

        # Проверяем на простой
        underload_alerts = [a for a in alerts if a.rule.severity == AlertSeverity.WARNING]
        underload_metrics = ['cpu_usage', 'memory_usage', 'network_usage_percent']
        underload_count = sum(1 for alert in underload_alerts if alert.rule.metric in underload_metrics)

        if underload_count >= 3:  # Все три правила простоя
            return ServerStatus.UNDERLOADED

        return ServerStatus.NORMAL

    def _get_metrics_summary(self, server_data: pd.DataFrame) -> Dict:
        """Получение сводки по метрикам"""
        summary = {}

        metrics_to_check = ['cpu_usage', 'memory_usage', 'network_in_mbps']
        for metric in metrics_to_check:
            if metric in server_data.columns:
                summary[metric] = {
                    'mean': server_data[metric].mean(),
                    'max': server_data[metric].max(),
                    'min': server_data[metric].min(),
                    'std': server_data[metric].std()
                }

        return summary

    def get_alerts_history(self, limit: int = 100) -> pd.DataFrame:
        """Получение истории алертов"""
        return pd.DataFrame(self.alerts_history[-limit:])

    def update_rule(self, rule_name: str, **kwargs):
        """Обновление правила"""
        for rule in self.rules:
            if rule.name == rule_name:
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                break


# Синглтон инстанс
alert_system = AlertSystem()