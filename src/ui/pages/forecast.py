import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Добавляем путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Импортируем модули для загрузки данных из базы
try:
    from utils.data_loader import load_data_from_database, generate_server_data
except ImportError:
    # Fallback для прямого импорта
    import importlib.util

    data_loader_path = os.path.join(parent_dir, 'utils', 'data_loader.py')
    if os.path.exists(data_loader_path):
        spec = importlib.util.spec_from_file_location("data_loader", data_loader_path)
        data_loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_loader)
        load_data_from_database = data_loader.load_data_from_database
        generate_server_data = data_loader.generate_server_data
    else:
        data_generator_path = os.path.join(parent_dir, 'utils', 'data_generator.py')
        spec = importlib.util.spec_from_file_location("data_generator", data_generator_path)
        data_generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_generator)
        generate_server_data = data_generator.generate_server_data
        load_data_from_database = None

# Импортируем модули для работы с базой данных
app_dir = os.path.join(parent_dir, '..', 'app')
sys.path.insert(0, app_dir)

try:
    from connection import SessionLocal
    from preds_crud import PredsCRUD
    from facts_crud import FactsCRUD
    from dbcrud import DBCRUD
except ImportError as e:
    st.warning(f"Не удалось импортировать модули базы данных: {e}")
    SessionLocal = None


def get_db_session():
    """Get database session"""
    if SessionLocal is None:
        return None
    return SessionLocal()


@st.cache_data(ttl=300)
def load_predictions_from_db(vm: str, metric: str, start_date: datetime = None, end_date: datetime = None):
    """
    Load predictions from database

    Args:
        vm: Virtual machine name
        metric: Metric name
        start_date: Start date (optional)
        end_date: End date (optional)

    Returns:
        DataFrame with predictions
    """
    if SessionLocal is None:
        return pd.DataFrame()

    db = get_db_session()
    if db is None:
        return pd.DataFrame()

    try:
        crud = PredsCRUD(db)
        predictions = crud.get_predictions(vm, metric, start_date, end_date)

        if not predictions:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for pred in predictions:
            data.append({
                'timestamp': pred.timestamp,
                'value_predicted': float(pred.value_predicted),
                'lower_bound': float(pred.lower_bound) if pred.lower_bound else None,
                'upper_bound': float(pred.upper_bound) if pred.upper_bound else None,
                'created_at': pred.created_at
            })

        df = pd.DataFrame(data)
        if not df.empty:
            # Add load_percentage for compatibility
            df['load_percentage'] = df['value_predicted']

        return df

    except Exception as e:
        st.warning(f"Ошибка загрузки предсказаний: {e}")
        return pd.DataFrame()
    finally:
        if db:
            db.close()


@st.cache_data(ttl=300)
def load_future_predictions(vm: str, metric: str):
    """Load future predictions (timestamp > now)"""
    if SessionLocal is None:
        return pd.DataFrame()

    db = get_db_session()
    if db is None:
        return pd.DataFrame()

    try:
        crud = PredsCRUD(db)
        predictions = crud.get_future_predictions(vm, metric)

        if not predictions:
            return pd.DataFrame()

        data = []
        for pred in predictions:
            data.append({
                'timestamp': pred.timestamp,
                'value_predicted': float(pred.value_predicted),
                'lower_bound': float(pred.lower_bound) if pred.lower_bound else None,
                'upper_bound': float(pred.upper_bound) if pred.upper_bound else None
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df['load_percentage'] = df['value_predicted']

        return df

    except Exception as e:
        st.warning(f"Ошибка загрузки будущих предсказаний: {e}")
        return pd.DataFrame()
    finally:
        if db:
            db.close()


@st.cache_data(ttl=300)
def load_all_servers():
    """Load list of all servers from database"""
    try:
        df = generate_server_data()
        if df.empty:
            return []
        return sorted(df['server'].unique().tolist())
    except Exception as e:
        st.warning(f"Ошибка загрузки списка серверов: {e}")
        return []


@st.cache_data(ttl=300)
def load_metrics_for_server(vm: str):
    """Load available metrics for a server"""
    if SessionLocal is None:
        return ['cpu.usage.average']

    db = get_db_session()
    if db is None:
        return ['cpu.usage.average']

    try:
        crud = DBCRUD(db)
        metrics = crud.get_metrics_for_vm(vm)
        return metrics if metrics else ['cpu.usage.average']
    except Exception as e:
        st.warning(f"Ошибка загрузки метрик: {e}")
        return ['cpu.usage.average']
    finally:
        if db:
            db.close()


def show():
    """Страница прогнозирования"""
    st.markdown('<h2 class="sub-header">🔮 Прогноз нагрузки серверов</h2>', unsafe_allow_html=True)

    try:
        # Загружаем список серверов
        servers = load_all_servers()

        if not servers:
            st.warning("⚠️ Серверы не найдены в базе данных. Пожалуйста, убедитесь, что данные загружены.")
            st.info("💡 Используйте API или утилиты для загрузки данных в базу.")
            return

        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown('<div class="server-selector fade-in">', unsafe_allow_html=True)

            # Выбор сервера
            selected_server = st.selectbox(
                "**Выберите сервер для прогноза:**",
                servers,
                index=0 if servers else None,
                key="forecast_server_select"
            )

            # Загружаем доступные метрики для выбранного сервера
            available_metrics = load_metrics_for_server(selected_server)

            # Выбор метрики
            selected_metric = st.selectbox(
                "**Выберите метрику:**",
                available_metrics,
                index=0 if available_metrics else None,
                key="forecast_metric_select"
            )

            # Параметры прогноза
            st.markdown("### ⚙️ Параметры")

            forecast_hours = st.slider(
                "**Период прогноза (часов):**",
                min_value=12,
                max_value=168,  # До 7 дней
                value=48,
                step=12,
                key="forecast_hours"
            )

            # Выбор источника данных
            data_source = st.radio(
                "**Источник прогноза:**",
                ["Из базы данных", "Сгенерировать новый"],
                index=0,
                key="forecast_data_source"
            )

            # Кнопка загрузки/генерации
            if data_source == "Из базы данных":
                load_btn = st.button(
                    "📥 Загрузить прогноз из базы",
                    type="primary",
                    use_container_width=True,
                    key="load_forecast_btn"
                )
                generate_btn = False
            else:
                generate_btn = st.button(
                    "🚀 Сгенерировать новый прогноз",
                    type="primary",
                    use_container_width=True,
                    key="generate_forecast_btn"
                )
                load_btn = False

            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            if load_btn or generate_btn or st.session_state.get('forecast_loaded', False):
                st.session_state.forecast_loaded = True

                # Загружаем исторические данные
                history_days = 7  # Последние 7 дней для истории
                history_start = datetime.now() - timedelta(days=history_days)

                historical_df = load_data_from_database(
                    start_date=history_start,
                    end_date=datetime.now(),
                    vms=[selected_server]
                )

                if not historical_df.empty:
                    historical_df = historical_df[historical_df['server'] == selected_server].copy()

                # Загружаем или генерируем прогноз
                if data_source == "Из базы данных" and load_btn:
                    # Загружаем предсказания из базы
                    future_start = datetime.now()
                    future_end = datetime.now() + timedelta(hours=forecast_hours)

                    forecast_df = load_predictions_from_db(
                        vm=selected_server,
                        metric=selected_metric,
                        start_date=future_start,
                        end_date=future_end
                    )

                    # Если нет предсказаний в базе, пробуем загрузить будущие
                    if forecast_df.empty:
                        forecast_df = load_future_predictions(selected_server, selected_metric)
                        # Фильтруем по нужному периоду
                        if not forecast_df.empty:
                            forecast_df = forecast_df[
                                (forecast_df['timestamp'] >= future_start) &
                                (forecast_df['timestamp'] <= future_end)
                                ]

                    if forecast_df.empty:
                        st.warning(f"⚠️ Нет предсказаний в базе данных для {selected_server}/{selected_metric}")
                        st.info("💡 Используйте API для генерации прогнозов или выберите 'Сгенерировать новый'")
                        return
                else:
                    # Генерируем простой прогноз (fallback)
                    if historical_df.empty:
                        st.warning("Нет исторических данных для генерации прогноза")
                        return

                    # Простой прогноз на основе исторических данных
                    last_date = pd.to_datetime(historical_df['timestamp']).max()
                    forecast_dates = [last_date + timedelta(hours=i) for i in range(1, forecast_hours + 1)]

                    # Используем последние значения для прогноза
                    metric_col = selected_metric if selected_metric in historical_df.columns else 'load_percentage'
                    if metric_col in historical_df.columns:
                        last_values = historical_df[metric_col].tail(24).values
                        base_forecast = pd.Series(last_values).mean() if len(last_values) > 0 else 50.0
                    else:
                        base_forecast = 50.0

                    import numpy as np
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

                    forecast_df = pd.DataFrame({
                        'timestamp': forecast_dates,
                        'load_percentage': forecast_values,
                        'value_predicted': forecast_values,
                        'lower_bound': [v * 0.9 for v in forecast_values],
                        'upper_bound': [v * 1.1 for v in forecast_values]
                    })

                if not forecast_df.empty and not historical_df.empty:
                    # Подготовка исторических данных для отображения
                    metric_col = selected_metric if selected_metric in historical_df.columns else 'load_percentage'
                    if metric_col not in historical_df.columns:
                        metric_col = 'load_percentage'

                    # Последние 3 дня истории
                    last_date = pd.to_datetime(historical_df['timestamp']).max()
                    history_start = last_date - timedelta(days=3)
                    history_df = historical_df[
                        pd.to_datetime(historical_df['timestamp']) >= history_start
                        ].copy()

                    # Создание графика
                    fig = go.Figure()

                    # Исторические данные
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(history_df['timestamp']),
                        y=history_df[metric_col],
                        mode='lines',
                        name='Исторические данные',
                        line=dict(color='#1E88E5', width=2.5),
                        hovertemplate='<b>%{x}</b><br>Значение: %{y:.1f}%<extra></extra>'
                    ))

                    # Прогноз
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(forecast_df['timestamp']),
                        y=forecast_df['value_predicted'] if 'value_predicted' in forecast_df.columns else forecast_df[
                            'load_percentage'],
                        mode='lines',
                        name='Прогноз',
                        line=dict(color='#FF5722', width=3, dash='dash'),
                        hovertemplate='<b>%{x}</b><br>Прогноз: %{y:.1f}%<extra></extra>'
                    ))

                    # Доверительный интервал (если есть)
                    if 'lower_bound' in forecast_df.columns and 'upper_bound' in forecast_df.columns:
                        lower = forecast_df['lower_bound'].fillna(forecast_df['value_predicted'] * 0.9)
                        upper = forecast_df['upper_bound'].fillna(forecast_df['value_predicted'] * 1.1)

                        fig.add_trace(go.Scatter(
                            x=pd.to_datetime(forecast_df['timestamp']).tolist() + pd.to_datetime(
                                forecast_df['timestamp']).tolist()[::-1],
                            y=upper.tolist() + lower.tolist()[::-1],
                            fill='toself',
                            fillcolor='rgba(255, 87, 34, 0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            hoverinfo='skip',
                            showlegend=True,
                            name='Доверительный интервал'
                        ))

                    # Линия разделения
                    if not history_df.empty:
                        last_hist_date = pd.to_datetime(history_df['timestamp']).max()
                        fig.add_vline(
                            x=last_hist_date,
                            line_width=2,
                            line_dash="dot",
                            line_color="grey",
                            annotation_text="Начало прогноза",
                            annotation_position="top right"
                        )

                    # Настройка layout
                    fig.update_layout(
                        title=f'<b>Прогноз {selected_metric} для {selected_server}</b>',
                        xaxis_title='<b>Дата и время</b>',
                        yaxis_title='<b>Значение (%)</b>',
                        height=500,
                        hovermode='x unified',
                        plot_bgcolor='rgba(240, 242, 246, 1)',
                        paper_bgcolor='rgba(255, 255, 255, 1)',
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01,
                            bgcolor='rgba(255, 255, 255, 0.9)'
                        )
                    )

                    # Отображение метрик прогноза
                    st.markdown("### 📊 Ключевые показатели прогноза")

                    forecast_values = forecast_df['value_predicted'] if 'value_predicted' in forecast_df.columns else \
                    forecast_df['load_percentage']

                    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                    with col_metric1:
                        avg_forecast = forecast_values.mean()
                        st.metric("Средняя", f"{avg_forecast:.1f}%")

                    with col_metric2:
                        peak_forecast = forecast_values.max()
                        st.metric("Пиковая", f"{peak_forecast:.1f}%")

                    with col_metric3:
                        peak_idx = forecast_values.idxmax()
                        peak_time = pd.to_datetime(forecast_df.iloc[peak_idx]['timestamp'])
                        st.metric("Время пика", peak_time.strftime("%H:%M"))

                    with col_metric4:
                        if peak_forecast > 80:
                            risk = "Высокий 🔴"
                        elif peak_forecast > 60:
                            risk = "Средний 🟡"
                        else:
                            risk = "Низкий 🟢"
                        st.metric("Риск", risk)

                    st.plotly_chart(fig, use_container_width=True)

                    # Детальный прогноз
                    st.markdown("### 📋 Детальный прогноз по часам")

                    # Группировка по дням
                    forecast_df['date'] = pd.to_datetime(forecast_df['timestamp']).dt.date
                    forecast_df['hour'] = pd.to_datetime(forecast_df['timestamp']).dt.hour

                    # Создание таблицы
                    forecast_table = forecast_df.pivot_table(
                        values='value_predicted' if 'value_predicted' in forecast_df.columns else 'load_percentage',
                        index='hour',
                        columns='date',
                        aggfunc='mean'
                    ).round(1)

                    # Переименование колонок
                    forecast_table.columns = [col.strftime('%d.%m') if hasattr(col, 'strftime') else str(col) for col in
                                              forecast_table.columns]
                    forecast_table.index = [f"{hour:02d}:00" for hour in forecast_table.index]

                    # Отображение таблицы с цветовым кодированием
                    st.dataframe(
                        forecast_table.style.background_gradient(
                            cmap='RdYlGn_r',
                            subset=forecast_table.columns
                        ),
                        use_container_width=True,
                        height=400
                    )

                    # Рекомендации
                    st.markdown("### 💡 Рекомендации")

                    if peak_forecast > 80:
                        st.error("""
                    **⚠️ Требуются срочные меры:**
                    - Увеличить ресурсы сервера
                    - Рассмотреть горизонтальное масштабирование
                    - Оптимизировать запросы к базе данных
                    - Настроить кэширование
                    """)
                    elif peak_forecast > 60:
                        st.warning("""
                    **🟡 Рекомендуется мониторинг:**
                    - Наблюдать за тенденцией
                    - Подготовить план масштабирования
                    - Проверить оптимизацию приложения
                    """)
                    else:
                        st.success("""
                    **🟢 Система стабильна:**
                    - Текущие ресурсы достаточны
                    - Продолжать мониторинг
                    - Плановое обслуживание
                    """)

                    # Информация о прогнозе
                    if data_source == "Из базы данных":
                        st.info(f"📊 Прогноз загружен из базы данных. Метрика: {selected_metric}")
                        if 'created_at' in forecast_df.columns:
                            latest_pred = forecast_df['created_at'].max()
                            st.caption(f"Последнее обновление прогноза: {latest_pred}")

                elif forecast_df.empty:
                    st.warning("⚠️ Не удалось загрузить или сгенерировать прогноз")
                else:
                    st.warning("⚠️ Нет исторических данных для отображения")

            else:
                # Инструкция при первом заходе
                st.markdown('<div class="info-card">', unsafe_allow_html=True)

                st.markdown("## 👋 Добро пожаловать в модуль прогнозирования!")

                col_info1, col_info2 = st.columns(2)

                with col_info1:
                    st.info("**Для получения прогноза:**")
                    st.write("1. Выберите сервер из списка слева")
                    st.write("2. Выберите метрику для анализа")
                    st.write("3. Выберите источник данных")
                    st.write("4. Нажмите кнопку загрузки/генерации")

                with col_info2:
                    st.success("**Что вы получите:**")
                    st.write("📈 **Интерактивный график** с историей и прогнозом")
                    st.write("📊 **Ключевые метрики** нагрузки")
                    st.write("📋 **Детальную таблицу** прогнозов по времени")
                    st.write("💡 **Автоматические рекомендации** на основе прогноза")
                    st.write("📈 **Доверительные интервалы** из базы данных")

                st.divider()

                with st.expander("📚 **Источники прогноза**", expanded=True):
                    st.write("""
                    **Из базы данных:**
                    - Загружает сохраненные прогнозы из таблицы predictions
                    - Использует реальные доверительные интервалы
                    - Требует предварительной генерации прогнозов через API

                    **Сгенерировать новый:**
                    - Создает простой прогноз на основе исторических данных
                    - Используется как fallback, если нет данных в базе
                    - Для точных прогнозов используйте Prophet через API
                    """)

                st.divider()

                st.warning("""
                **⚠️ Важно:** 
                - Для загрузки из базы данных необходимо предварительно сгенерировать прогнозы через API
                - Качество прогноза зависит от количества и качества исторических данных
                - Рекомендуется иметь данные как минимум за 2-4 недели
                """)

                st.caption(
                    "💡 **Подсказка:** Выберите сервер и метрику слева, затем нажмите 'Загрузить прогноз из базы'")

                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        import traceback
        with st.expander("Детали ошибки"):
            st.code(traceback.format_exc())
        st.info("💡 Убедитесь, что база данных доступна и содержит данные.")
