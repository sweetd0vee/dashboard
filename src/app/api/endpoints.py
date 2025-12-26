from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from connection import get_db
# from ... import schemas as pydantic_models
from dbcrud import DBCRUD
# from ...prophet_service import ProphetForecaster
# from ...anomaly_detector import AnomalyDetector

router = APIRouter()

# Глобальные сервисы (будут инжектится)
# forecaster = ProphetForecaster()
# anomaly_detector = AnomalyDetector()
#
#
# @router.post("/metrics/", response_model=pydantic_models.MetricData)
# async def create_metric(
#         metric: pydantic_models.MetricData,
#         db: Session = Depends(get_db),
#         background_tasks: BackgroundTasks = None
# ):
#     """Добавление новой метрики"""
#     crud = DBCRUD(db)
#
#     # Сохранение метрики
#     db_metric = crud.create_historical_metric(metric)
#
#     # Проверка на аномалии в фоне
#     if background_tasks:
#         background_tasks.add_task(
#             #check_for_anomalies,
#             metric.vm,
#             metric.metric,
#             db
#         )
#
#     return db_metric
#
#
# @router.post("/metrics/batch/", response_model=dict)
# async def create_metrics_batch(
#         metrics: List[pydantic_models.MetricData],
#         db: Session = Depends(get_db)
# ):
#     """Пакетное добавление метрик"""
#     crud = DBCRUD(db)
#     created = []
#
#     for metric in metrics:
#         db_metric = crud.create_historical_metric(metric)
#         created.append({
#             "id": db_metric.id,
#             "vm": db_metric.vm,
#             "timestamp": db_metric.timestamp,
#             "metric": db_metric.metric
#         })
#
#     return {"created": len(created), "metrics": created}
#
# API с Query параметрами
@router.get("/latest_metrics", response_model=List[dict]) # {vm}/{metric}/{days}
async def get_metrics(
        vm: str = Query(..., description="Название сервера"),
        metric: str = Query(..., description="Название метрики (cpu, memory, disk, network)"),
        db: Session = Depends(get_db)
):
    """Получение значений метрик за последние 24 часа"""
    crud = DBCRUD(db)
    data = crud.get_latest_metrics(vm, metric, 24)

    return [
        {
            "timestamp": record.timestamp,
            "value": record.value,
            "created_at": record.created_at
        }
        for record in data
    ]


@router.get("/metrics", response_model=List[dict])
async def get_metrics(
        vm: str = Query(..., description="Название сервера"),
        metric: str = Query(..., description="Название метрики (cpu, memory, disk, network)"),
        days: Optional[int] = Query(1, ge=1, le=30, description="Количество дней (опциоанльно)"),
        start_date: Optional[datetime] = Query(None, description="Дата старта (опционально)"),
        end_date: Optional[datetime] = Query(None, description="Дата окончания (опционально)"),
        db: Session = Depends(get_db)
):
    """
    Получение метрик виртуального сервера.

    Можно указать либо количество последних дней, либо start_date/end_date.
    """
    if days and (start_date or end_date):
        raise HTTPException(
            status_code=400,
            detail="Укажите либо days, либо start_date/end_date"
        )

    crud = DBCRUD(db)

    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date должен быть раньше end_date")
        data = crud.get_metrics_by_date_range(vm, metric, start_date, end_date)
    else:
        hours = days * 24
        data = crud.get_latest_metrics(vm, metric, hours)

    return [
        {
            "timestamp": record.timestamp,
            "value": record.value,
            "created_at": record.created_at
        }
        for record in data
    ]

#
#
# @router.post("/predict/", response_model=pydantic_models.PredictionResponse)
# async def predict_metrics(
#         request: pydantic_models.PredictionRequest,
#         db: Session = Depends(get_db)
# ):
#     """Прогнозирование метрик"""
#     crud = DBCRUD(db)
#
#     # Получение или обучение модели
#     model = forecaster.train_or_load_model(db, crud, request.vm, request.metric)
#
#     if not model:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Не удалось получить модель для {request.vm} - {request.metric}"
#         )
#
#     # Прогнозирование
#     forecast = forecaster.predict(model, request.periods, request.frequency)
#
#     # Сохранение прогнозов в БД
#     predictions = []
#     for _, row in forecast.iterrows():
#         prediction = crud.save_prediction(
#             vm=request.vm,
#             metric=request.metric,
#             timestamp=row['ds'],
#             value=row['yhat'],
#             lower=row['yhat_lower'],
#             upper=row['yhat_upper']
#         )
#
#         predictions.append({
#             "timestamp": row['ds'],
#             "prediction": row['yhat'],
#             "confidence_lower": row['yhat_lower'],
#             "confidence_upper": row['yhat_upper']
#         })
#
#     # Получение точности модели
#     model_info = crud.get_active_model(request.vm, request.metric)
#     accuracy = model_info.accuracy_score if model_info else None
#
#     return pydantic_models.PredictionResponse(
#         vm=request.vm,
#         metric=request.metric,
#         predictions=predictions,
#         model_accuracy=accuracy,
#         generated_at=datetime.now()
#     )
#
#
# @router.post("/train/", response_model=pydantic_models.TrainingResponse)
# async def train_model(
#         request: pydantic_models.TrainingRequest,
#         db: Session = Depends(get_db)
# ):
#     """Обучение модели"""
#     crud = DBCRUD(db)
#
#     start_time = datetime.now()
#
#     # Получение данных
#     cutoff_date = datetime.now() - timedelta(days=request.days_of_history)
#     data = crud.get_historical_metrics(
#         request.vm,
#         request.metric,
#         start_date=cutoff_date
#     )
#
#     if len(data) < 48:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Недостаточно данных для обучения: {len(data)} записей"
#         )
#
#     # Подготовка данных
#     data_dicts = [
#         {
#             'timestamp': record.timestamp,
#             'value': float(record.value)
#         }
#         for record in data
#     ]
#
#     df = forecaster.prepare_data(data_dicts)
#
#     # Обучение
#     model, metrics, model_path = forecaster.train_model(
#         df, request.vm, request.metric
#     )
#
#     # Сохранение информации о модели
#     model_info = crud.save_model_info(
#         request.vm,
#         request.metric,
#         model_path,
#         metrics.get('mape') if metrics else None
#     )
#
#     training_time = (datetime.now() - start_time).total_seconds()
#
#     return pydantic_models.TrainingResponse(
#         vm=request.vm,
#         metric=request.metric,
#         model_id=str(model_info.id),
#         accuracy=metrics.get('mape', 0.0) if metrics else 0.0,
#         training_time=training_time,
#         status="success"
#     )
