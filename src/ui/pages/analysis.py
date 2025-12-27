import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys
import requests
import numpy as np

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


@st.cache_data(ttl=300)
def load_data_from_db(start_date: datetime = None, end_date: datetime = None):
    """
    Load data from database with optional date range

    Args:
        start_date: Start date for data loading
        end_date: End date for data loading

    Returns:
        DataFrame with server metrics
    """
    if load_data_from_database is None:
        # Fallback to generate_server_data if database loader not available
        df = generate_server_data()
        if start_date or end_date:
            if start_date:
                df = df[df['timestamp'] >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df['timestamp'] <= pd.Timestamp(end_date)]
        return df

    try:
        df = load_data_from_database(
            start_date=start_date,
            end_date=end_date
        )
        return df
    except Exception as e:
        st.warning(f"Ошибка загрузки из базы данных: {e}. Используются данные по умолчанию.")
        # Fallback
        df = generate_server_data()
        if start_date or end_date:
            if start_date:
                df = df[df['timestamp'] >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df['timestamp'] <= pd.Timestamp(end_date)]
        return df


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


def show():
    """Страница общего анализа"""
    st.markdown('<h2 class="sub-header">📊 Общий анализ нагрузки серверов</h2>', unsafe_allow_html=True)

    try:
        # Загружаем данные для определения диапазона дат
        initial_df = load_data_from_db()

        if initial_df.empty:
            st.warning("⚠️ Данные не найдены в базе данных. Пожалуйста, убедитесь, что данные загружены.")
            st.info("💡 Используйте API или утилиты для загрузки данных в базу.")
            return

        # Выбор даты для анализа
        col_date1, col_date2 = st.columns([1, 3])

        with col_date1:
            st.markdown('<div class="server-selector fade-in">', unsafe_allow_html=True)

            # Выбор диапазона дат
            min_date = pd.to_datetime(initial_df['timestamp']).min().date()
            max_date = pd.to_datetime(initial_df['timestamp']).max().date()

            date_range_type = st.radio(
                "**Тип анализа:**",
                ["Одна дата", "Диапазон дат"],
                key="date_range_type"
            )

            if date_range_type == "Одна дата":
                analysis_date = st.date_input(
                    "**Выберите дату:**",
                    max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="analysis_date_picker"
                )
                start_date = datetime.combine(analysis_date, datetime.min.time())
                end_date = datetime.combine(analysis_date, datetime.max.time())
            else:
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date_input = st.date_input(
                        "**С:**",
                        min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="analysis_start_date"
                    )
                with col_end:
                    end_date_input = st.date_input(
                        "**По:**",
                        max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="analysis_end_date"
                    )
                start_date = datetime.combine(start_date_input, datetime.min.time())
                end_date = datetime.combine(end_date_input, datetime.max.time())

            st.markdown("### 🎛️ Фильтры")

            # Получаем список серверов
            servers = load_all_servers()

            # Фильтр по серверам
            selected_servers = st.multiselect(
                "**Серверы:**",
                servers,
                default=servers[:5] if len(servers) > 5 else servers,
                key="analysis_servers"
            )

            # Фильтр по типу сервера (если есть колонка server_type)
            if 'server_type' in initial_df.columns:
                server_types = initial_df['server_type'].unique().tolist()
                selected_types = st.multiselect(
                    "**Типы серверов:**",
                    ["Все"] + server_types,
                    default=["Все"],
                    key="analysis_server_types"
                )
            else:
                selected_types = ["Все"]

            # Фильтр по нагрузке
            min_load, max_load = st.slider(
                "**Диапазон нагрузки (%):**",
                0, 100, (0, 100),
                key="load_range"
            )

            # Кнопка обновления
            refresh_btn = st.button(
                "🔄 Обновить данные",
                type="primary",
                use_container_width=True,
                key="refresh_analysis"
            )

            st.markdown('</div>', unsafe_allow_html=True)

        with col_date2:
            # Загружаем данные за выбранный период
            if refresh_btn:
                load_data_from_db.clear()

            analysis_df = load_data_from_db(start_date=start_date, end_date=end_date)

            if analysis_df.empty:
                st.warning(f"⚠️ Нет данных за выбранный период ({start_date.date()} - {end_date.date()})")
                return

            # Применение фильтров
            if selected_servers:
                analysis_df = analysis_df[analysis_df['server'].isin(selected_servers)].copy()

            if "Все" not in selected_types and 'server_type' in analysis_df.columns:
                analysis_df = analysis_df[analysis_df['server_type'].isin(selected_types)].copy()

            if 'load_percentage' in analysis_df.columns:
                analysis_df = analysis_df[
                    (analysis_df['load_percentage'] >= min_load) &
                    (analysis_df['load_percentage'] <= max_load)
                    ].copy()

            if analysis_df.empty:
                st.warning("⚠️ Нет данных, соответствующих выбранным фильтрам")
                return

            # Общая статистика
            st.markdown("### 📈 Общая статистика")

            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

            with col_stat1:
                total_servers = analysis_df['server'].nunique()
                st.metric("Серверов", total_servers)

            with col_stat2:
                total_records = len(analysis_df)
                st.metric("Записей", f"{total_records:,}")

            with col_stat3:
                if 'load_percentage' in analysis_df.columns:
                    avg_load = analysis_df['load_percentage'].mean()
                    st.metric("Средняя нагрузка", f"{avg_load:.1f}%")
                else:
                    st.metric("Средняя нагрузка", "N/A")

            with col_stat4:
                if 'load_percentage' in analysis_df.columns:
                    max_load = analysis_df['load_percentage'].max()
                    st.metric("Пиковая нагрузка", f"{max_load:.1f}%")
                else:
                    st.metric("Пиковая нагрузка", "N/A")

            st.divider()

            # График 1: Нагрузка по серверам (heatmap по времени)
            st.markdown("### 📊 Нагрузка по серверам (Heatmap)")

            if 'load_percentage' in analysis_df.columns and 'server' in analysis_df.columns:
                # Подготовка данных для heatmap
                analysis_df['hour'] = pd.to_datetime(analysis_df['timestamp']).dt.hour
                analysis_df['date'] = pd.to_datetime(analysis_df['timestamp']).dt.date

                heatmap_data = analysis_df.pivot_table(
                    values='load_percentage',
                    index='server',
                    columns='hour',
                    aggfunc='mean'
                )

                if not heatmap_data.empty:
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=heatmap_data.values,
                        x=[f"{h:02d}:00" for h in heatmap_data.columns],
                        y=heatmap_data.index,
                        colorscale='RdYlGn_r',
                        text=heatmap_data.values.round(1),
                        texttemplate='%{text}%',
                        textfont={"size": 10},
                        colorbar=dict(title="Нагрузка (%)")
                    ))

                    fig_heatmap.update_layout(
                        height=400,
                        xaxis_title="Час дня",
                        yaxis_title="Сервер",
                        title="Распределение нагрузки по серверам и времени"
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)

            st.divider()

            # График 2: Сравнение серверов
            st.markdown("### 📊 Сравнение серверов")

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                # Средняя нагрузка по серверам
                if 'load_percentage' in analysis_df.columns:
                    server_stats = analysis_df.groupby('server')['load_percentage'].agg(
                        ['mean', 'max', 'min']).reset_index()
                    server_stats = server_stats.sort_values('mean', ascending=False)

                    fig_bar = go.Figure()
                    fig_bar.add_trace(go.Bar(
                        x=server_stats['server'],
                        y=server_stats['mean'],
                        name='Средняя нагрузка',
                        marker_color='#1E88E5',
                        text=server_stats['mean'].round(1),
                        textposition='outside'
                    ))

                    fig_bar.update_layout(
                        height=400,
                        xaxis_title="Сервер",
                        yaxis_title="Нагрузка (%)",
                        title="Средняя нагрузка по серверам",
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            with col_chart2:
                # Распределение нагрузки
                if 'load_percentage' in analysis_df.columns:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=analysis_df['load_percentage'],
                        nbinsx=30,
                        marker_color='#4CAF50',
                        name='Распределение нагрузки'
                    ))

                    fig_hist.update_layout(
                        height=400,
                        xaxis_title="Нагрузка (%)",
                        yaxis_title="Количество записей",
                        title="Распределение нагрузки"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

            st.divider()

            # График 3: Временные ряды по серверам
            st.markdown("### 📈 Временные ряды нагрузки")

            # Выбор метрики для отображения
            metric_options = []
            if 'load_percentage' in analysis_df.columns:
                metric_options.append('load_percentage')
            if 'cpu.usage.average' in analysis_df.columns:
                metric_options.append('cpu.usage.average')
            if 'mem.usage.average' in analysis_df.columns:
                metric_options.append('mem.usage.average')
            if 'memory.usage.average' in analysis_df.columns:
                metric_options.append('memory.usage.average')

            selected_metric = st.selectbox(
                "**Выберите метрику для отображения:**",
                metric_options,
                index=0,
                key="analysis_metric"
            )

            if selected_metric and selected_metric in analysis_df.columns:
                # Ограничиваем количество серверов для читаемости
                top_servers = analysis_df.groupby('server')[selected_metric].mean().nlargest(10).index.tolist()
                plot_df = analysis_df[analysis_df['server'].isin(top_servers)].copy()

                fig_lines = go.Figure()

                for server in plot_df['server'].unique():
                    server_data = plot_df[plot_df['server'] == server].sort_values('timestamp')
                    fig_lines.add_trace(go.Scatter(
                        x=pd.to_datetime(server_data['timestamp']),
                        y=server_data[selected_metric],
                        mode='lines',
                        name=server,
                        line=dict(width=2),
                        hovertemplate=f'<b>{server}</b><br>%{{x}}<br>Значение: %{{y:.1f}}%<extra></extra>'
                    ))

                fig_lines.update_layout(
                    height=500,
                    xaxis_title="Время",
                    yaxis_title="Значение (%)",
                    title=f"Временные ряды {selected_metric}",
                    hovermode='x unified',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    )
                )
                st.plotly_chart(fig_lines, use_container_width=True)

            st.divider()

            # График 4: Корреляция метрик
            st.markdown("### 🔗 Корреляция метрик")

            # Выбираем метрики для корреляции
            correlation_metrics = []
            for col in ['load_percentage', 'cpu.usage.average', 'mem.usage.average',
                        'memory.usage.average', 'disk.usage.average', 'net.usage.average']:
                if col in analysis_df.columns:
                    correlation_metrics.append(col)

            if len(correlation_metrics) >= 2:
                # Вычисляем корреляцию
                corr_df = analysis_df[correlation_metrics].corr()

                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_df.values,
                    x=corr_df.columns,
                    y=corr_df.index,
                    colorscale='RdBu',
                    zmid=0,
                    text=corr_df.values.round(2),
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    colorbar=dict(title="Корреляция")
                ))

                fig_corr.update_layout(
                    height=400,
                    title="Корреляционная матрица метрик"
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Недостаточно метрик для анализа корреляции")

            st.divider()

            # Таблица с детальной статистикой
            st.markdown("### 📋 Детальная статистика по серверам")

            if 'load_percentage' in analysis_df.columns:
                stats_df = analysis_df.groupby('server').agg({
                    'load_percentage': ['mean', 'std', 'min', 'max', 'count']
                }).round(2)

                stats_df.columns = ['Среднее', 'Стд. откл.', 'Мин', 'Макс', 'Кол-во']
                stats_df = stats_df.sort_values('Среднее', ascending=False)

                st.dataframe(
                    stats_df.style.background_gradient(
                        cmap='RdYlGn_r',
                        subset=['Среднее', 'Макс']
                    ),
                    use_container_width=True,
                    height=400
                )

            # Дополнительные метрики, если доступны
            if 'cpu.usage.average' in analysis_df.columns or 'mem.usage.average' in analysis_df.columns:
                st.markdown("### 📊 Дополнительные метрики")

                metric_cols = []
                if 'cpu.usage.average' in analysis_df.columns:
                    metric_cols.append('cpu.usage.average')
                if 'mem.usage.average' in analysis_df.columns:
                    metric_cols.append('mem.usage.average')
                elif 'memory.usage.average' in analysis_df.columns:
                    metric_cols.append('memory.usage.average')
                if 'disk.usage.average' in analysis_df.columns:
                    metric_cols.append('disk.usage.average')

                if metric_cols:
                    additional_stats = analysis_df.groupby('server')[metric_cols].mean().round(2)
                    additional_stats.columns = [col.replace('.', ' ').title() for col in additional_stats.columns]
                    st.dataframe(additional_stats, use_container_width=True)

            # Экспорт данных
            st.divider()
            st.markdown("### 💾 Экспорт данных")

            col_export1, col_export2 = st.columns(2)

            with col_export1:
                csv = analysis_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv,
                    file_name=f"analysis_{start_date.date()}_{end_date.date()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col_export2:
                if st.button("🔄 Обновить все данные", use_container_width=True):
                    load_data_from_db.clear()
                    st.rerun()

    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        import traceback
        with st.expander("Детали ошибки"):
            st.code(traceback.format_exc())
        st.info("💡 Убедитесь, что база данных доступна и содержит данные.")

    # Добавляем кнопку для перехода в LLM UI в конце страницы
    st.divider()
    st.markdown("### 🤖 Переход в LLM интерфейс")

    # Проверяем доступность контейнера Llama
    LLAMA_UI_URL_HEALTH = "http://llama-server:8080"
    LLAMA_UI_URL = "http://localhost:8080"  # Уточнен порт

    # Функция для проверки доступности (выполняется на сервере)
    @st.cache_data(ttl=30)  # Кэшируем результат на 30 секунд
    def check_llama_availability():
        try:
            response = requests.get(f"{LLAMA_UI_URL_HEALTH}/health", timeout=5)
            return response.status_code == 200, LLAMA_UI_URL_HEALTH
        except requests.exceptions.RequestException:
            try:
                response = requests.get(f"{LLAMA_UI_URL}", timeout=5)
                return response.status_code == 200, LLAMA_UI_URL
            except:
                return False, LLAMA_UI_URL

    # Проверяем доступность
    is_available, llama_url = check_llama_availability()

    # Создаем кнопку
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if is_available:
            if st.button(
                    "🚀 Перейти в LLM UI",
                    type="primary",
                    use_container_width=True,
                    help="Откроет интерфейс LLM в новой вкладке"
            ):
                # Используем markdown с ссылкой для открытия в новой вкладке
                st.markdown(f'<a href="{llama_url}" target="_blank" style="display: none;" id="llama-link"></a>',
                            unsafe_allow_html=True)
                st.success(f"✅ LLM UI доступен по адресу: {llama_url}")
                # Добавляем JavaScript для открытия ссылки
                st.components.v1.html(f"""
                    <script>
                        window.open("{llama_url}", "_blank");
                    </script>
                """, height=0)
        else:
            st.warning("⚠️ LLM UI временно недоступен")

            if st.button("🔄 Проверить доступность снова", use_container_width=True):
                st.cache_data.clear()  # Очищаем кэш
                st.rerun()

            st.info("""
            **Возможные причины:**
            - Сервер LLM не запущен
            - Контейнер llama-server не активен
            - Порт 8080 занят другим приложением
            ```
            """)