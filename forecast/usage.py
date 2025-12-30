from forecaster import ProphetForecaster
from src.app.dbcrud import DBCRUD
from src.app.connection import SessionLocal

forecaster = ProphetForecaster()
result = forecaster.generate_forecast(SessionLocal, DBCRUD, "DataLake-DBN1", "cpu_usage_average")