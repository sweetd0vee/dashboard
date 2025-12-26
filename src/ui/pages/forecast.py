import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import sys
import os

# Добавляем путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Теперь импортируем
try:
    from utils.data_generator import generate_server_data, generate_forecast
    from utils.alert_rules import alert_system, ServerStatus, AlertSeverity
except ImportError:
    # Fallback для прямого импорта
    import importlib.util
    import pathlib


@st.cache_data
def load_data():
    return generate_server_data()


def show():
    """Страница прогнозирования"""
    st.markdown('<h2 class="sub-header">🔮 Прогноз нагрузки на 48 часов</h2>', unsafe_allow_html=True)

    # Загрузка данных
    df = load_data()
    servers = sorted(df['server'].unique())

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown('<div class="server-selector fade-in">', unsafe_allow_html=True)

        # Выбор сервера
        selected_server = st.selectbox(
            "**Выберите сервер для прогноза:**",
            servers,
            index=0,
            key="forecast_server_select"
        )

        # Параметры прогноза
        st.markdown("### ⚙️ Параметры")

        forecast_hours = st.slider(
            "**Период прогноза (часов):**",
            min_value=12,
            max_value=72,
            value=48,
            step=12,
            key="forecast_hours"
        )

        confidence_level = st.slider(
            "**Уровень доверия (%):**",
            min_value=80,
            max_value=95,
            value=90,
            step=5,
            key="confidence_level"
        )

        # Кнопка генерации
        generate_btn = st.button(
            "🚀 Сгенерировать прогноз",
            type="primary",
            use_container_width=True,
            key="generate_forecast_btn"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if generate_btn or st.session_state.get('forecast_generated', False):
            st.session_state.forecast_generated = True

            # Получение исторических данных
            server_data = df[df['server'] == selected_server].copy()

            if not server_data.empty:
                # Генерация прогноза
                forecast_df = generate_forecast(server_data, forecast_hours)

                # Исторические данные (последние 3 дня)
                last_date = server_data['timestamp'].max()
                history_start = last_date - timedelta(days=3)
                history_df = server_data[server_data['timestamp'] >= history_start].copy()

                # Расчет доверительного интервала
                confidence_factor = (100 - confidence_level) / 100
                forecast_df['upper'] = forecast_df['load_percentage'] * (1 + confidence_factor)
                forecast_df['lower'] = forecast_df['load_percentage'] * (1 - confidence_factor)

                # Создание графика
                fig = go.Figure()

                # Исторические данные
                fig.add_trace(go.Scatter(
                    x=history_df['timestamp'],
                    y=history_df['load_percentage'],
                    mode='lines',
                    name='Исторические данные',
                    line=dict(color='#1E88E5', width=2.5),
                    hovertemplate='<b>%{x}</b><br>Нагрузка: %{y:.1f}%<extra></extra>'
                ))

                # Прогноз
                fig.add_trace(go.Scatter(
                    x=forecast_df['timestamp'],
                    y=forecast_df['load_percentage'],
                    mode='lines',
                    name='Прогноз',
                    line=dict(color='#FF5722', width=3, dash='dash'),
                    hovertemplate='<b>%{x}</b><br>Прогноз: %{y:.1f}%<extra></extra>'
                ))

                # Доверительный интервал
                fig.add_trace(go.Scatter(
                    x=forecast_df['timestamp'].tolist() + forecast_df['timestamp'].tolist()[::-1],
                    y=forecast_df['upper'].tolist() + forecast_df['lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor=f'rgba(255, 87, 34, {confidence_level / 200})',
                    line=dict(color='rgba(255,255,255,0)'),
                    hoverinfo='skip',
                    showlegend=True,
                    name=f'Доверительный интервал ({confidence_level}%)'
                ))

                # Линия разделения
                fig.add_vline(
                    x=last_date,
                    line_width=2,
                    line_dash="dot",
                    line_color="grey",
                    annotation_text="Начало прогноза",
                    annotation_position="top right"
                )

                # Настройка layout
                fig.update_layout(
                    title=f'<b>Прогноз нагрузки для {selected_server}</b>',
                    xaxis_title='<b>Дата и время</b>',
                    yaxis_title='<b>Нагрузка (%)</b>',
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

                col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                with col_metric1:
                    avg_forecast = forecast_df['load_percentage'].mean()
                    st.metric("Средняя", f"{avg_forecast:.1f}%")

                with col_metric2:
                    peak_forecast = forecast_df['load_percentage'].max()
                    st.metric("Пиковая", f"{peak_forecast:.1f}%")

                with col_metric3:
                    peak_time = forecast_df.loc[forecast_df['load_percentage'].idxmax(), 'timestamp']
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
                forecast_df['date'] = forecast_df['timestamp'].dt.date
                forecast_df['hour'] = forecast_df['timestamp'].dt.hour

                # Создание таблицы
                forecast_table = forecast_df.pivot_table(
                    values='load_percentage',
                    index='hour',
                    columns='date',
                    aggfunc='mean'
                ).round(1)

                # Переименование колонок
                forecast_table.columns = [col.strftime('%d.%m') for col in forecast_table.columns]
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

            else:
                st.warning("Нет данных для выбранного сервера")
        else:
            # Инструкция при первом заходе с использованием нативных компонентов
            st.markdown('<div class="info-card">', unsafe_allow_html=True)

            # Заголовок с эмодзи
            st.markdown("## 👋 Добро пожаловать в модуль прогнозирования!")

            # Первая секция в колонках
            col_info1, col_info2 = st.columns(2)

            with col_info1:
                st.info("**Для получения прогноза:**")
                st.write("1. Выберите сервер из списка слева")
                st.write("2. Выберите метрику для анализа")
                st.write("3. Настройте параметры прогноза")
                st.write("4. Нажмите кнопку 'Сгенерировать прогноз'")

            with col_info2:
                st.success("**Что вы получите:**")
                st.write("📈 **Интерактивный график** с историей и прогнозом")
                st.write("📊 **Ключевые метрики** нагрузки")
                st.write("📋 **Детальную таблицу** прогнозов по времени")
                st.write("💡 **Автоматические рекомендации** на основе прогноза")
                st.write("📈 **Оценку качества** модели Prophet")

            st.divider()

            # Методология
            with st.expander("📚 **Методология прогнозирования**", expanded=True):
                st.write("""
                Прогноз строится с использованием библиотеки Prophet (разработанной Facebook) 
                на основе анализа исторических данных с учётом:
                """)

                col_method1, col_method2 = st.columns(2)

                with col_method1:
                    st.write("• 📅 Сезонности (суточной, недельной)")
                    st.write("• 📈 Трендов")
                    st.write("• 🕒 Влияния рабочих часов")

                with col_method2:
                    st.write("• 🌙 Ночных периодов")
                    st.write("• 🎯 Праздников и выходных")
                    st.write("• 🔄 Автокорреляции данных")

            st.divider()

            # Важное предупреждение
            st.warning("""
            **⚠️ Важно:** Качество прогноза зависит от количества и качества 
            исторических данных. Рекомендуется иметь данные как минимум за 2-4 недели 
            для получения точных прогнозов.
            """)

            # Быстрые подсказки
            st.caption("💡 **Подсказка:** Для начала выберите сервер из списка слева и нажмите 'Сгенерировать прогноз'")

            st.markdown('</div>', unsafe_allow_html=True)