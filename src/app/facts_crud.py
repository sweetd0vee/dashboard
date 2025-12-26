from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import models as db_models
import schemas as pydantic_models


class FactsCRUD:
    def __init__(self, db: Session):
        self.db = db

    # =================================== ФАКТИЧЕСКИЕ МЕТРИКИ =====================================

    def create_metric_fact(self, metric: pydantic_models.MetricFact) -> db_models.ServerMetricsFact:
        """
        Создание записи фактического значения исторической метрики

        Args:
            metric: Данные метрики

        Returns:
            Созданная запись
        """
        # Проверка на дубликаты
        existing = self.db.query(db_models.ServerMetricsFact).filter(
            db_models.ServerMetricsFact.vm == metric.vm,
            db_models.ServerMetricsFact.metric == metric.metric,
            db_models.ServerMetricsFact.timestamp == metric.timestamp
        ).first()

        if existing:
            # Обновляем существующую запись
            existing.value = metric.value
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Создаем новую запись
        db_metric = db_models.ServerMetricsFact(
            vm=metric.vm,
            timestamp=metric.timestamp,
            metric=metric.metric,
            value=metric.value
        )
        self.db.add(db_metric)
        self.db.commit()
        self.db.refresh(db_metric)
        return db_metric

    def create_metrics_fact_batch(self, metrics: List[pydantic_models.MetricFact]) -> int:
        """
        Пакетное создание фактических исторических метрик

        Args:
            metrics: Список метрик

        Returns:
            Количество созданных записей
        """
        created_count = 0
        for metric in metrics:
            try:
                self.create_metric_fact(metric)
                created_count += 1
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку
                print(f"Error creating metric {metric}: {e}")

        return created_count

    def get_metrics_fact(
            self,
            vm: str,
            metric: str,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: int = 5000
    ) -> List[db_models.ServerMetricsFact]:
        """
        Получение исторических метрик с фильтрацией

        Args:
            vm: Имя виртуальной машины
            metric: Тип метрики
            start_date: Начальная дата
            end_date: Конечная дата
            limit: Максимальное количество записей

        Returns:
            Список метрик
        """
        query = self.db.query(db_models.ServerMetricsFact).filter(
            db_models.ServerMetricsFact.vm == vm,
            db_models.ServerMetricsFact.metric == metric
        )

        if start_date:
            query = query.filter(db_models.ServerMetricsFact.timestamp >= start_date)
        if end_date:
            query = query.filter(db_models.ServerMetricsFact.timestamp <= end_date)

        return query.order_by(db_models.ServerMetricsFact.timestamp).limit(limit).all()

    def get_latest_metrics(self, vm: str, metric: str, hours: int = 24) -> List[db_models.ServerMetricsFact]:
        """
        Получить последние N часов данных

        Args:
            vm: Имя виртуальной машины
            metric: Тип метрики
            hours: Количество часов

        Returns:
            Список метрик
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return self.db.query(db_models.ServerMetricsFact).filter(
            db_models.ServerMetricsFact.vm == vm,
            db_models.ServerMetricsFact.metric == metric,
            db_models.ServerMetricsFact.timestamp >= cutoff_time
        ).order_by(db_models.ServerMetricsFact.timestamp).all()

    def get_metrics_as_dataframe(self,
                                 vm: str,
                                 metric: str,
                                 start_date: datetime,
                                 end_date: datetime) -> Optional[Dict]:
        """
        Получение метрик в удобном для Prophet формате

        Args:
            vm: Имя виртуальной машины
            metric: Тип метрики
            hours: Количество часов

        Returns:
            Словарь с данными или None
        """
        # metrics = self.get_latest_metrics(vm, metric, hours)

        if not metrics:
            return None

        data = {
            'ds': [],  # timestamps
            'y': []  # values
        }

        for metric_record in metrics:
            data['ds'].append(metric_record.timestamp)
            data['y'].append(metric_record.value)

        return data

    def get_metrics_facat_statistics(
            self,
            vm: str,
            metric: str,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Получение статистики по историческим метрикам

        Returns:
            Словарь со статистикой
        """
        query = self.db.query(
            func.count(db_models.ServerMetricsFact.id).label('count'),
            func.min(db_models.ServerMetricsFact.value).label('min'),
            func.max(db_models.ServerMetricsFact.value).label('max'),
            func.avg(db_models.ServerMetricsFact.value).label('avg'),
            func.stddev(db_models.ServerMetricsFact.value).label('stddev')
        ).filter(
            db_models.ServerMetricsFact.vm == vm,
            db_models.ServerMetricsFact.metric == metric
        )

        if start_date:
            query = query.filter(db_models.ServerMetricsFact.timestamp >= start_date)
        if end_date:
            query = query.filter(db_models.ServerMetricsFact.timestamp <= end_date)

        result = query.first()

        if not result:
            return {}

        return {
            'count': result.count or 0,
            'min': float(result.min) if result.min else 0.0,
            'max': float(result.max) if result.max else 0.0,
            'avg': float(result.avg) if result.avg else 0.0,
            'stddev': float(result.stddev) if result.stddev else 0.0,
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }