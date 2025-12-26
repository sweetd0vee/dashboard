from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from facts_crud import DBCRUD

# Создание сессии
engine = create_engine('postgresql://postgres:postgres@localhost:5432/server_metrics')
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# Создание CRUD объекта
crud = DBCRUD(session)

# 1. Получение последних 24 часов данных
vm = "DataLake-DBN1"
metric = "cpu.usage.average"

latest_data = crud.get_latest_metrics(vm, metric, hours=2000)
print(f"Получено {len(latest_data)} записей за последние 2000 часов")

# 2. Получение статистики
stats = crud.get_historical_metrics_statistics(vm, metric)
print(f"Статистика: среднее={stats['avg']:.2f}, минимум={stats['min']:.2f}, максимум={stats['max']:.2f}")

# 3. Сохранение предсказаний
future_time = datetime.now() + timedelta(hours=1)
crud.save_prediction(
    vm=vm,
    metric=metric,
    timestamp=future_time,
    value=45.6,
    lower_bound=40.1,
    upper_bound=50.2
)

# 4. Получение всех VM в базе
all_vms = crud.get_all_vms()
print(f"Все VM в базе: {all_vms}")

# 5. Проверка полноты данных
completeness = crud.calculate_data_completeness(
    vm=vm,
    metric=metric,
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    expected_interval_minutes=30
)
print(f"Полнота данных: {completeness['completeness_percentage']}%")

# 6. Очистка старых данных
cleanup_stats = crud.cleanup_old_data(days_to_keep=30)
print(f"Удалено записей: {cleanup_stats}")

# 7. Получение статистики базы
db_stats = crud.get_database_stats()
print(f"Статистика БД: {db_stats}")

# 8. Сравнение фактических значений с предсказанными
comparison = crud.get_actual_vs_predicted(vm, metric, hours=48)
for item in comparison[:5]:
    print(f"Время: {item['timestamp']}, Факт: {item['actual_value']}, Прогноз: {item['predicted_value']}, Ошибка: {item['error']:.2f}")

# Закрытие сессии
session.close()