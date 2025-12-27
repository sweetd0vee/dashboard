from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from ..connection import get_db
from ..dbcrud import DBCRUD
from ..facts_crud import FactsCRUD
from ..preds_crud import PredsCRUD
import ..schemas as pydantic_models
from base_logger import logger

router = APIRouter()


# ===========================================
# DBCRUD ENDPOINTS (General Database Operations)
# ===========================================

@router.get("/vms", response_model=List[str], tags=["Database"])
async def get_all_vms(db: Session = Depends(get_db)):
    """
    Get list of all virtual machines in the database

    Returns:
        List of VM names
    """
    try:
        crud = DBCRUD(db)
        vms = crud.get_all_vms()
        return vms
    except Exception as e:
        logger.error(f"Error getting VMs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving VMs: {str(e)}")


@router.get("/vms/{vm}/metrics", response_model=List[str], tags=["Database"])
async def get_metrics_for_vm(vm: str, db: Session = Depends(get_db)):
    """
    Get list of available metrics for a specific VM

    Args:
        vm: Virtual machine name

    Returns:
        List of metric names
    """
    try:
        crud = DBCRUD(db)
        metrics = crud.get_metrics_for_vm(vm)
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics for VM {vm}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/vms/{vm}/metrics/{metric}/time-range", response_model=pydantic_models.TimeRangeResponse,
            tags=["Database"])
async def get_data_time_range(
        vm: str,
        metric: str,
        db: Session = Depends(get_db)
):
    """
    Get time range of available data for a VM and metric

    Args:
        vm: Virtual machine name
        metric: Metric name

    Returns:
        Time range information including first/last timestamp and total records
    """
    try:
        crud = DBCRUD(db)
        time_range = crud.get_data_time_range(vm, metric)

        if not time_range:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for VM '{vm}' and metric '{metric}'"
            )

        return pydantic_models.TimeRangeResponse(**time_range)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting time range for {vm}/{metric}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving time range: {str(e)}")


@router.get("/stats", response_model=pydantic_models.DatabaseStatsResponse, tags=["Database"])
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Get database statistics

    Returns:
        Database statistics including record counts, unique VMs/metrics, data volume
    """
    try:
        crud = DBCRUD(db)
        stats = crud.get_database_stats()
        return pydantic_models.DatabaseStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@router.post("/cleanup", response_model=Dict, tags=["Database"])
async def cleanup_old_data(
        days_to_keep: int = Body(90, ge=1, le=365, description="Number of days to keep"),
        db: Session = Depends(get_db)
):
    """
    Clean up old data from database

    Args:
        days_to_keep: Number of days of data to keep (default: 90)

    Returns:
        Statistics about deleted records
    """
    try:
        crud = DBCRUD(db)
        result = crud.cleanup_old_data(days_to_keep)
        return result
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up data: {str(e)}")


@router.get("/vms/{vm}/metrics/{metric}/completeness", response_model=pydantic_models.DataCompletenessResponse,
            tags=["Database"])
async def get_data_completeness(
        vm: str,
        metric: str,
        start_date: datetime = Query(..., description="Start date"),
        end_date: datetime = Query(..., description="End date"),
        expected_interval_minutes: int = Query(30, ge=1, le=1440, description="Expected interval in minutes"),
        db: Session = Depends(get_db)
):
    """
    Calculate data completeness for a VM and metric

    Args:
        vm: Virtual machine name
        metric: Metric name
        start_date: Start date for analysis
        end_date: End date for analysis
        expected_interval_minutes: Expected interval between data points (default: 30)

    Returns:
        Data completeness metrics including missing intervals
    """
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")

        crud = DBCRUD(db)
        completeness = crud.calculate_data_completeness(
            vm, metric, start_date, end_date, expected_interval_minutes
        )
        return pydantic_models.DataCompletenessResponse(**completeness)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating completeness for {vm}/{metric}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating completeness: {str(e)}")


@router.get("/vms/{vm}/metrics/{metric}/missing-data", response_model=List[Dict], tags=["Database"])
async def get_missing_data(
        vm: str,
        metric: str,
        start_date: datetime = Query(..., description="Start date"),
        end_date: datetime = Query(..., description="End date"),
        expected_interval_minutes: int = Query(30, ge=1, le=1440, description="Expected interval in minutes"),
        db: Session = Depends(get_db)
):
    """
    Detect missing data intervals for a VM and metric

    Args:
        vm: Virtual machine name
        metric: Metric name
        start_date: Start date for analysis
        end_date: End date for analysis
        expected_interval_minutes: Expected interval between data points

    Returns:
        List of missing data intervals
    """
    try:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")

        crud = DBCRUD(db)
        missing = crud.detect_missing_data(vm, metric, start_date, end_date, expected_interval_minutes)
        return missing
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting missing data for {vm}/{metric}: {e}")
        raise HTTPException(status_code=500, detail=f"Error detecting missing data: {str(e)}")


# ===========================================
# FACTS CRUD ENDPOINTS (Fact Metrics)
# ===========================================

@router.post("/facts", response_model=pydantic_models.MetricFact, status_code=201, tags=["Facts"])
async def create_metric_fact(
        metric: pydantic_models.MetricFactCreate,
        db: Session = Depends(get_db),
        background_tasks: Optional[BackgroundTasks] = None
):
    """
    Create or update a metric fact (upsert operation)

    Args:
        metric: Metric fact data
        background_tasks: Optional background tasks for anomaly detection

    Returns:
        Created or updated metric fact
    """
    try:
        crud = FactsCRUD(db)
        # Create a MetricFact with created_at for the CRUD method
        fact_data = pydantic_models.MetricFact(
            vm=metric.vm,
            timestamp=metric.timestamp,
            metric=metric.metric,
            value=metric.value,
            created_at=datetime.now()
        )
        db_metric = crud.create_metric_fact(fact_data)

        # TODO: Add background task for anomaly detection if needed
        # if background_tasks:
        #     background_tasks.add_task(check_for_anomalies, metric.vm, metric.metric, db)

        return pydantic_models.MetricFact(
            id=str(db_metric.id),
            vm=db_metric.vm,
            timestamp=db_metric.timestamp,
            metric=db_metric.metric,
            value=float(db_metric.value) if db_metric.value else 0.0,
            created_at=db_metric.created_at
        )
    except Exception as e:
        logger.error(f"Error creating metric fact: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating metric: {str(e)}")


@router.post("/facts/batch", response_model=pydantic_models.BatchCreateResponse, tags=["Facts"])
async def create_metrics_fact_batch(
        metrics: List[pydantic_models.MetricFactCreate],
        db: Session = Depends(get_db)
):
    """
    Batch create or update metric facts

    Args:
        metrics: List of metric facts to create

    Returns:
        Batch creation statistics
    """
    try:
        crud = FactsCRUD(db)

        # Convert create schemas to fact schemas
        fact_metrics = []
        for metric in metrics:
            fact_data = pydantic_models.MetricFact(
                vm=metric.vm,
                timestamp=metric.timestamp,
                metric=metric.metric,
                value=metric.value,
                created_at=datetime.now()
            )
            fact_metrics.append(fact_data)

        created_count = crud.create_metrics_fact_batch(fact_metrics)
        failed_count = len(metrics) - created_count

        return pydantic_models.BatchCreateResponse(
            created=created_count,
            failed=failed_count,
            total=len(metrics)
        )
    except Exception as e:
        logger.error(f"Error creating metrics batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating metrics batch: {str(e)}")


@router.get("/facts", response_model=List[pydantic_models.MetricFact], tags=["Facts"])
async def get_metrics_fact(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        start_date: Optional[datetime] = Query(None, description="Start date (inclusive)"),
        end_date: Optional[datetime] = Query(None, description="End date (inclusive)"),
        limit: int = Query(5000, ge=1, le=10000, description="Maximum number of records"),
        db: Session = Depends(get_db)
):
    """
    Get historical metric facts with optional date filtering

    Args:
        vm: Virtual machine name
        metric: Metric name
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of records to return

    Returns:
        List of metric facts
    """
    try:
        crud = FactsCRUD(db)
        records = crud.get_metrics_fact(vm, metric, start_date, end_date, limit)

        return [
            pydantic_models.MetricFact(
                id=str(record.id),
                vm=record.vm,
                timestamp=record.timestamp,
                metric=record.metric,
                value=float(record.value) if record.value else 0.0,
                created_at=record.created_at
            )
            for record in records
        ]
    except Exception as e:
        logger.error(f"Error getting metrics fact: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/facts/latest", response_model=List[pydantic_models.MetricFact], tags=["Facts"])
async def get_latest_metrics_fact(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        hours: int = Query(24, ge=1, le=720, description="Number of hours to retrieve"),
        db: Session = Depends(get_db)
):
    """
    Get latest metric facts for the last N hours

    Args:
        vm: Virtual machine name
        metric: Metric name
        hours: Number of hours to retrieve (default: 24, max: 720)

    Returns:
        List of metric facts
    """
    try:
        crud = FactsCRUD(db)
        records = crud.get_latest_metrics(vm, metric, hours)

        return [
            pydantic_models.MetricFact(
                id=str(record.id),
                vm=record.vm,
                timestamp=record.timestamp,
                metric=record.metric,
                value=float(record.value) if record.value else 0.0,
                created_at=record.created_at
            )
            for record in records
        ]
    except Exception as e:
        logger.error(f"Error getting latest metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving latest metrics: {str(e)}")


@router.get("/facts/statistics", response_model=Dict, tags=["Facts"])
async def get_metrics_fact_statistics(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        start_date: Optional[datetime] = Query(None, description="Start date (inclusive)"),
        end_date: Optional[datetime] = Query(None, description="End date (inclusive)"),
        db: Session = Depends(get_db)
):
    """
    Get aggregated statistics for a metric

    Args:
        vm: Virtual machine name
        metric: Metric name
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Statistics including count, min, max, avg, stddev
    """
    try:
        crud = FactsCRUD(db)
        stats = crud.get_metrics_fact_statistics(vm, metric, start_date, end_date)
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


# ===========================================
# PREDICTIONS CRUD ENDPOINTS
# ===========================================

@router.post("/predictions", response_model=pydantic_models.MetricPrediction, status_code=201, tags=["Predictions"])
async def save_prediction(
        prediction: pydantic_models.MetricPredictionCreate,
        db: Session = Depends(get_db)
):
    """
    Save a prediction (upsert operation)

    Args:
        prediction: Prediction data

    Returns:
        Created or updated prediction
    """
    try:
        crud = PredsCRUD(db)
        db_pred = crud.save_prediction(
            vm=prediction.vm,
            metric=prediction.metric,
            timestamp=prediction.timestamp,
            value=prediction.value_predicted,
            lower_bound=prediction.lower_bound,
            upper_bound=prediction.upper_bound
        )

        return pydantic_models.MetricPrediction(
            id=str(db_pred.id),
            vm=db_pred.vm,
            timestamp=db_pred.timestamp,
            metric=db_pred.metric,
            value_predicted=float(db_pred.value_predicted),
            lower_bound=float(db_pred.lower_bound) if db_pred.lower_bound else None,
            upper_bound=float(db_pred.upper_bound) if db_pred.upper_bound else None,
            created_at=db_pred.created_at
        )
    except Exception as e:
        logger.error(f"Error saving prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving prediction: {str(e)}")


@router.post("/predictions/batch", response_model=pydantic_models.BatchCreateResponse, tags=["Predictions"])
async def save_predictions_batch(
        predictions: List[pydantic_models.MetricPredictionCreate],
        db: Session = Depends(get_db)
):
    """
    Batch save predictions

    Args:
        predictions: List of predictions to save

    Returns:
        Batch save statistics
    """
    try:
        crud = PredsCRUD(db)

        # Convert to dict format expected by save_predictions_batch
        # Note: PredsCRUD.save_predictions_batch expects 'lower' and 'upper' keys
        pred_dicts = []
        for pred in predictions:
            pred_dicts.append({
                'vm': pred.vm,
                'metric': pred.metric,
                'timestamp': pred.timestamp,
                'value': pred.value_predicted,
                'lower': pred.lower_bound,
                'upper': pred.upper_bound
            })

        saved_count = crud.save_predictions_batch(pred_dicts)
        failed_count = len(predictions) - saved_count

        return pydantic_models.BatchCreateResponse(
            created=saved_count,
            failed=failed_count,
            total=len(predictions)
        )
    except Exception as e:
        logger.error(f"Error saving predictions batch: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving predictions batch: {str(e)}")


@router.get("/predictions", response_model=List[pydantic_models.MetricPrediction], tags=["Predictions"])
async def get_predictions(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        start_date: Optional[datetime] = Query(None, description="Start date (inclusive)"),
        end_date: Optional[datetime] = Query(None, description="End date (inclusive)"),
        db: Session = Depends(get_db)
):
    """
    Get predictions for a VM and metric

    Args:
        vm: Virtual machine name
        metric: Metric name
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of predictions
    """
    try:
        crud = PredsCRUD(db)
        predictions = crud.get_predictions(vm, metric, start_date, end_date)

        return [
            pydantic_models.MetricPrediction(
                id=str(pred.id),
                vm=pred.vm,
                timestamp=pred.timestamp,
                metric=pred.metric,
                value_predicted=float(pred.value_predicted),
                lower_bound=float(pred.lower_bound) if pred.lower_bound else None,
                upper_bound=float(pred.upper_bound) if pred.upper_bound else None,
                created_at=pred.created_at
            )
            for pred in predictions
        ]
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving predictions: {str(e)}")


@router.get("/predictions/future", response_model=List[pydantic_models.MetricPrediction], tags=["Predictions"])
async def get_future_predictions(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        db: Session = Depends(get_db)
):
    """
    Get future predictions (timestamp > now) for a VM and metric

    Args:
        vm: Virtual machine name
        metric: Metric name

    Returns:
        List of future predictions
    """
    try:
        crud = PredsCRUD(db)
        predictions = crud.get_future_predictions(vm, metric)

        return [
            pydantic_models.MetricPrediction(
                id=str(pred.id),
                vm=pred.vm,
                timestamp=pred.timestamp,
                metric=pred.metric,
                value_predicted=float(pred.value_predicted),
                lower_bound=float(pred.lower_bound) if pred.lower_bound else None,
                upper_bound=float(pred.upper_bound) if pred.upper_bound else None,
                created_at=pred.created_at
            )
            for pred in predictions
        ]
    except Exception as e:
        logger.error(f"Error getting future predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving future predictions: {str(e)}")


@router.get("/predictions/compare", response_model=List[pydantic_models.ActualVsPredictedResponse],
            tags=["Predictions"])
async def get_actual_vs_predicted(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        hours: int = Query(24, ge=1, le=720, description="Number of hours to compare"),
        db: Session = Depends(get_db)
):
    """
    Compare actual values with predictions for a VM and metric

    Args:
        vm: Virtual machine name
        metric: Metric name
        hours: Number of hours to compare (default: 24, max: 720)

    Returns:
        List of comparisons with actual vs predicted values and error metrics
    """
    try:
        crud = PredsCRUD(db)
        comparisons = crud.get_actual_vs_predicted(vm, metric, hours)

        return [
            pydantic_models.ActualVsPredictedResponse(**comp)
            for comp in comparisons
        ]
    except Exception as e:
        logger.error(f"Error comparing actual vs predicted: {e}")
        raise HTTPException(status_code=500, detail=f"Error comparing values: {str(e)}")


# ===========================================
# LEGACY ENDPOINTS (for backward compatibility)
# ===========================================

@router.get("/latest_metrics", response_model=List[dict], tags=["Legacy"])
async def get_latest_metrics_legacy(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        db: Session = Depends(get_db)
):
    """
    [Legacy] Get latest metrics for the last 24 hours

    This endpoint is kept for backward compatibility.
    Use /facts/latest instead.
    """
    try:
        crud = FactsCRUD(db)
        data = crud.get_latest_metrics(vm, metric, 24)

        return [
            {
                "timestamp": record.timestamp,
                "value": float(record.value) if record.value else 0.0,
                "created_at": record.created_at
            }
            for record in data
        ]
    except Exception as e:
        logger.error(f"Error getting latest metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.get("/metrics", response_model=List[dict], tags=["Legacy"])
async def get_metrics_legacy(
        vm: str = Query(..., description="Virtual machine name"),
        metric: str = Query(..., description="Metric name"),
        days: Optional[int] = Query(1, ge=1, le=30, description="Number of days"),
        start_date: Optional[datetime] = Query(None, description="Start date"),
        end_date: Optional[datetime] = Query(None, description="End date"),
        db: Session = Depends(get_db)
):
    """
    [Legacy] Get metrics with flexible date range

    This endpoint is kept for backward compatibility.
    Use /facts instead.

    You can specify either days or start_date/end_date, but not both.
    """
    try:
        if days and (start_date or end_date):
            raise HTTPException(
                status_code=400,
                detail="Specify either days or start_date/end_date, not both"
            )

        crud = FactsCRUD(db)

        if start_date and end_date:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="start_date must be before end_date")
            data = crud.get_metrics_fact(vm, metric, start_date, end_date)
        else:
            hours = days * 24
            data = crud.get_latest_metrics(vm, metric, hours)

        return [
            {
                "timestamp": record.timestamp,
                "value": float(record.value) if record.value else 0.0,
                "created_at": record.created_at
            }
            for record in data
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")
