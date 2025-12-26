from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class MetricType(str, Enum):
    CPU_USAGE = "cpu.usage.average"
    CPU_SUMMATION = "cpu.ready.summation"
    MEMORY_USAGE = "memory.usage.average"
    DISK_USAGE = "disk.usage.average"
    NETWORK_IO = "net.usage.average"


class LoadLevel(str, Enum):
    IDLE = "idle"
    NORMAL = "normal"
    HIGH = "high"


class MetricFact(BaseModel):
    vm: str
    timestamp: datetime
    metric: str
    value: float = Field(..., ge=0, le=100)
    created_at: datetime


class MetricPrediction(BaseModel):
    vm: str
    timestamp: datetime
    metric: str
    value: float = Field(..., ge=0, le=100)
    created_at: datetime


class PredictionRequest(BaseModel):
    vm: str
    metric: str
    periods: int = Field(48, ge=1, le=168)  # 1-168 периодов (до 7 дней) # 336 периодов (до 14 дней, за 2 недели)
    frequency: str = "30min"  # 30min, 1h, 4h, 1d


# class PredictionResponse(BaseModel):
#     vm: str
#     metric: str
#     predictions: List[dict]
#     model_accuracy: Optional[float] # чем заполняется это поле
#     created_at: datetime


# Сделать класс алертов по метрикам переданным
class AnomalyAlert(BaseModel):
    vm: str
    timestamp: datetime
    metric: str
    actual_value: float
    predicted_value: float
    anomaly_score: float
    load: LoadLevel
    message: str


class TrainingRequest(BaseModel):
    vm: str
    metric: str
    days_of_history: int = 14 # здесь поправить на число дней истории
    retrain: bool = False


# class TrainingResponse(BaseModel):
#     vm: str
#     metric: str
#     model_id: str
#     accuracy: float
#     training_time: float
#     status: str


class HealthCheck(BaseModel):
    status: str
    database: bool
    models_loaded: int
    uptime: float
