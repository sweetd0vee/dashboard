import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Импортируем модули для загрузки данных из базы
try:
    from utils.data_loader import load_data_from_database, generate_server_data
    from utils.alert_rules import alert_system, ServerStatus, AlertSeverity
except ImportError:
    # Fallback для прямого импорта
    import importlib.util

    # Импортируем data_loader
    data_loader_path = os.path.join(parent_dir, 'utils', 'data_loader.py')
    if os.path.exists(data_loader_path):
        spec = importlib.util.spec_from_file_location("data_loader", data_loader_path)
        data_loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_loader)
        load_data_from_database = data_loader.load_data_from_database
        generate_server_data = data_loader.generate_server_data
    else:
        # Fallback на data_generator если data_loader не найден
        data_generator_path = os.path.join(parent_dir, 'utils', 'data_generator.py')
        spec = importlib.util.spec_from_file_location("data_generator", data_generator_path)
        data_generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_generator)
        generate_server_data = data_generator.generate_server_data
        load_data_from_database = None

    # Импортируем alert_rules
    alert_rules_path = os.path.join(parent_dir, 'utils', 'alert_rules.py')
    spec = importlib.util.spec_from_file_location("alert_rules", alert_rules_path)
    alert_rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alert_rules)
    alert_system = alert_rules.alert_system
    ServerStatus = alert_rules.ServerStatus
    AlertSeverity = alert_rules.AlertSeverity


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_db(start_date: datetime = None, end_date: datetime = None, vm: str = None):
    """
    Load data from database with optional date range and VM filter

    Args:
        start_date: Start date for data loading
        end_date: End date for data loading
        vm: Optional VM name to filter

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
        if vm:
            df = df[df['server'] == vm]
        return df

    try:
        vms = [vm] if vm else None
        df = load_data_from_database(
            start_date=start_date,
            end_date=end_date,
            vms=vms
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
        if vm:
            df = df[df['server'] == vm]
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


def show_alert_settings():
    """Настройка параметров алертов"""
    with st.expander("⚙️ **Настройка правил алертов**", expanded=False):
        st.markdown("### Пороговые значения")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**⚠ Загруженность**")
            cpu_high = st.number_input(
                "CPU > (%)",
                min_value=0,
                max_value=100,
                value=85,
                key="cpu_high_threshold"
            )

            mem_high = st.number_input(
                "Память > (%)",
                min_value=0,
                max_value=100,
                value=80,
                key="mem_high_threshold"
            )

            cpu_ready = st.number_input(
                "CPU Ready > (%)",
                min_value=0,
                max_value=100,
                value=10,
                key="cpu_ready_threshold"
            )

        with col2:
            st.markdown("**📉 Простой**")
            cpu_low = st.number_input(
                "CPU < (%)",
                min_value=0,
                max_value=100,
                value=15,
                key="cpu_low_threshold"
            )

            mem_low = st.number_input(
                "Память < (%)",
                min_value=0,
                max_value=100,
                value=25,
                key="mem_low_threshold"
            )

            net_low = st.number_input(
                "Сеть < (%)",
                min_value=0,
                max_value=100,
                value=5,
                key="net_low_threshold"
            )

        with col3:
            st.markdown("**🎯 Норма**")
            cpu_min = st.number_input(
                "CPU мин (%)",
                min_value=0,
                max_value=100,
                value=15,
                key="cpu_min_normal"
            )

            cpu_max = st.number_input(
                "CPU макс (%)",
                min_value=0,
                max_value=100,
                value=85,
                key="cpu_max_normal"
            )

            disk_latency = st.number_input(
                "Задержка диска > (ms)",
                min_value=0,
                max_value=100,
                value=25,
                key="disk_latency_threshold"
            )

        # Временные параметры
        st.markdown("### ⏰ Временные параметры")
        col_time1, col_time2 = st.columns(2)

        with col_time1:
            time_overload = st.slider(
                "Время для перегрузки (%)",
                min_value=0,
                max_value=100,
                value=20,
                key="time_overload"
            ) / 100

        with col_time2:
            time_underload = st.slider(
                "Время для простоя (%)",
                min_value=0,
                max_value=100,
                value=80,
                key="time_underload"
            ) / 100

        # Кнопки
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Сохранить настройки", use_container_width=True):
                try:
                    # Обновляем правила в системе
                    alert_system.update_rule("high_cpu_usage", thresholds={'high': cpu_high})
                    alert_system.update_rule("high_memory_usage", thresholds={'high': mem_high})
                    alert_system.update_rule("cpu_ready_time", thresholds={'high': cpu_ready})
                    alert_system.update_rule("low_cpu_usage", thresholds={'low': cpu_low})
                    alert_system.update_rule("low_memory_usage", thresholds={'low': mem_low})
                    alert_system.update_rule("low_network_usage", thresholds={'low': net_low})
                    alert_system.update_rule("normal_cpu_range", thresholds={'low': cpu_min, 'high': cpu_max})
                    alert_system.update_rule("high_disk_latency", thresholds={'high': disk_latency})

                    # Обновляем временные параметры
                    alert_system.update_rule("high_cpu_usage", time_percentage=time_overload)
                    alert_system.update_rule("high_memory_usage", time_percentage=time_overload)
                    alert_system.update_rule("cpu_ready_time", time_percentage=time_overload)
                    alert_system.update_rule("low_cpu_usage", time_percentage=time_underload)
                    alert_system.update_rule("low_memory_usage", time_percentage=time_underload)
                    alert_system.update_rule("low_network_usage", time_percentage=time_underload)

                    st.success("Настройки сохранены!")
                except Exception as e:
                    st.error(f"Ошибка при сохранении: {e}")

        with col_btn2:
            if st.button("🔄 Сбросить к default", use_container_width=True):
                try:
                    # Сбрасываем значения через интерфейс
                    st.session_state.cpu_high_threshold = 85
                    st.session_state.mem_high_threshold = 80
                    st.session_state.cpu_ready_threshold = 10
                    st.session_state.cpu_low_threshold = 15
                    st.session_state.mem_low_threshold = 25
                    st.session_state.net_low_threshold = 5
                    st.session_state.cpu_min_normal = 15
                    st.session_state.cpu_max_normal = 85
                    st.session_state.disk_latency_threshold = 25
                    st.session_state.time_overload = 20
                    st.session_state.time_underload = 80

                    st.success("Настройки сброшены к значениям по умолчанию!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка при сбросе: {e}")


def show_server_status(status):
    """Отображение статуса сервера"""
    status_config = {
        ServerStatus.OVERLOADED: {
            "icon": "🔴",
            "color": "#F44336",
            "text": "ПЕРЕГРУЗКА",
            "description": "Сервер перегружен"
        },
        ServerStatus.UNDERLOADED: {
            "icon": "🟡",
            "color": "#FFC107",
            "text": "ПРОСТОЙ",
            "description": "Сервер простаивает"
        },
        ServerStatus.NORMAL: {
            "icon": "🟢",
            "color": "#4CAF50",
            "text": "НОРМА",
            "description": "Сервер работает нормально"
        },
        ServerStatus.UNKNOWN: {
            "icon": "⚪",
            "color": "#9E9E9E",
            "text": "НЕТ ДАННЫХ",
            "description": "Недостаточно данных"
        }
    }

    config = status_config.get(status, status_config[ServerStatus.UNKNOWN])

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {config['color']}20 0%, {config['color']}10 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid {config['color']};
        margin: 20px 0;
    ">
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 2.5rem;">{config['icon']}</span>
            <div>
                <h3 style="margin: 0; color: {config['color']}; font-weight: bold;">{config['text']}</h3>
                <p style="margin: 5px 0 0 0; color: #666;">{config['description']}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_alerts(alerts):
    """Отображение алертов"""
    if not alerts:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #4CAF5020 0%, #4CAF5010 100%);
            padding: 20px;
            border-radius: 10px;
            border-left: 6px solid #4CAF50;
            margin: 20px 0;
        ">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 2rem;">✅</span>
                <div>
                    <h4 style="margin: 0; color: #4CAF50;">Нет активных алертов</h4>
                    <p style="margin: 5px 0 0 0; color: #666;">Все метрики в пределах нормы</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    for alert in alerts:
        severity_config = {
            AlertSeverity.CRITICAL: {"icon": "🔴", "color": "#F44336", "text": "КРИТИЧЕСКИЙ"},
            AlertSeverity.WARNING: {"icon": "🟡", "color": "#FFC107", "text": "ПРЕДУПРЕЖДЕНИЕ"},
            AlertSeverity.INFO: {"icon": "🔵", "color": "#2196F3", "text": "ИНФОРМАЦИЯ"}
        }

        config = severity_config.get(alert.rule.severity, severity_config[AlertSeverity.INFO])

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {config['color']}20 0%, {config['color']}10 100%);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {config['color']};
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">{config['icon']}</span>
                    <div>
                        <strong style="color: {config['color']};">{config['text']}: {alert.rule.name}</strong>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9rem;">
                            {alert.message}
                        </p>
                    </div>
                </div>
                <span style="color: #666; font-size: 0.9rem;">
                    {alert.timestamp.strftime('%H:%M') if hasattr(alert.timestamp, 'strftime') else str(alert.timestamp)}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def show():
    """Страница фактических данных"""
    st.markdown('<h2 class="sub-header">📈 Фактическая нагрузка серверов</h2>', unsafe_allow_html=True)

    # Показываем настройки алертов
    show_alert_settings()

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
                "**Выберите сервер:**",
                servers,
                index=0 if servers else None,
                key="fact_server"
            )

            # Загружаем данные для определения диапазона дат
            initial_df = load_data_from_db(vm=selected_server)

            if initial_df.empty:
                st.warning(f"⚠️ Нет данных для сервера '{selected_server}'")
                st.markdown('</div>', unsafe_allow_html=True)
                return

            # Выбор дат
            min_date = pd.to_datetime(initial_df['timestamp']).min().date()
            max_date = pd.to_datetime(initial_df['timestamp']).max().date()

            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input(
                    "**С:**",
                    min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="fact_start"
                )

            with col_date2:
                end_date = st.date_input(
                    "**По:**",
                    max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="fact_end"
                )

            # Кнопка обновления данных
            refresh_btn = st.button(
                "🔄 Обновить данные",
                type="primary",
                use_container_width=True,
                key="refresh_data"
            )

            # Кнопка анализа
            analyze_btn = st.button(
                "🔍 Анализировать алерты",
                type="primary",
                use_container_width=True,
                key="analyze_alerts"
            )

            st.markdown('</div>', unsafe_allow_html=True)

            # Загружаем данные для выбранного диапазона дат
            if refresh_btn or analyze_btn or 'fact_start' not in st.session_state:
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())

                # Очищаем кэш при обновлении
                if refresh_btn:
                    load_data_from_db.clear()

                filtered_df = load_data_from_db(
                    start_date=start_datetime,
                    end_date=end_datetime,
                    vm=selected_server
                )
            else:
                # Используем кэшированные данные
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                filtered_df = load_data_from_db(
                    start_date=start_datetime,
                    end_date=end_datetime,
                    vm=selected_server
                )

            # Фильтруем по серверу (на случай если загрузили все серверы)
            if not filtered_df.empty:
                filtered_df = filtered_df[filtered_df['server'] == selected_server].copy()

            # Анализ алертов
            if analyze_btn and not filtered_df.empty:
                with st.spinner("Анализируем метрики..."):
                    try:
                        analysis_result = alert_system.analyze_server_status(filtered_df, selected_server)

                        # Показываем статус сервера
                        show_server_status(analysis_result['status'])

                        # Показываем алерты
                        st.markdown("### ⚠️ Активные алерты")
                        show_alerts(analysis_result['alerts'])

                    except Exception as e:
                        st.error(f"Ошибка при анализе: {e}")
                        import traceback
                        st.code(traceback.format_exc())

            # Базовые метрики
            if not filtered_df.empty:
                st.markdown("### 📈 Основные метрики")

                col_metric1, col_metric2, col_metric3 = st.columns(3)
                with col_metric1:
                    avg_load = filtered_df['load_percentage'].mean() if 'load_percentage' in filtered_df.columns else 0
                    st.metric("Нагрузка", f"{avg_load:.1f}%")

                with col_metric2:
                    cpu_col = 'cpu.usage.average' if 'cpu.usage.average' in filtered_df.columns else 'load_percentage'
                    avg_cpu = filtered_df[cpu_col].mean() if cpu_col in filtered_df.columns else 0
                    st.metric("CPU", f"{avg_cpu:.1f}%")

                with col_metric3:
                    mem_col = 'mem.usage.average' if 'mem.usage.average' in filtered_df.columns else 'memory.usage.average'
                    avg_mem = filtered_df[mem_col].mean() if mem_col in filtered_df.columns else 0
                    st.metric("Память", f"{avg_mem:.1f}%")

        with col2:
            if not filtered_df.empty:
                # Дашборды
                st.markdown("### 📊 Мониторинг метрик")

                # График 1: Нагрузка и CPU
                fig1 = go.Figure()

                # Нагрузка
                if 'load_percentage' in filtered_df.columns:
                    fig1.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df['load_percentage'],
                        mode='lines',
                        name='Нагрузка',
                        line=dict(color='#1E88E5', width=3)
                    ))

                # CPU
                cpu_col = 'cpu.usage.average' if 'cpu.usage.average' in filtered_df.columns else None
                if cpu_col and cpu_col in filtered_df.columns:
                    fig1.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df[cpu_col],
                        mode='lines',
                        name='CPU',
                        line=dict(color='#FF5722', width=3)
                    ))

                fig1.update_layout(
                    height=300,
                    xaxis_title="Время",
                    yaxis_title="%",
                    showlegend=True,
                    margin=dict(t=30, b=30, l=50, r=30)
                )
                st.plotly_chart(fig1, use_container_width=True)

                # График 2: Память и диск
                fig2 = go.Figure()

                # Память
                mem_col = 'mem.usage.average' if 'mem.usage.average' in filtered_df.columns else 'memory.usage.average'
                if mem_col in filtered_df.columns:
                    fig2.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df[mem_col],
                        mode='lines',
                        name='Память',
                        line=dict(color='#4CAF50', width=3)
                    ))

                # Диск
                disk_col = 'disk.usage.average' if 'disk.usage.average' in filtered_df.columns else None
                if disk_col and disk_col in filtered_df.columns:
                    fig2.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df[disk_col],
                        mode='lines',
                        name='Диск',
                        line=dict(color='#9C27B0', width=3)
                    ))

                fig2.update_layout(
                    height=300,
                    xaxis_title="Время",
                    yaxis_title="%",
                    showlegend=True,
                    margin=dict(t=30, b=30, l=50, r=30)
                )
                st.plotly_chart(fig2, use_container_width=True)

                # График 3: Сеть и задержки
                col_graph1, col_graph2 = st.columns(2)

                with col_graph1:
                    fig3 = go.Figure()
                    net_col = 'net.usage.average' if 'net.usage.average' in filtered_df.columns else None
                    if net_col and net_col in filtered_df.columns:
                        fig3.add_trace(go.Scatter(
                            x=filtered_df['timestamp'],
                            y=filtered_df[net_col],
                            mode='lines',
                            name='Сеть',
                            line=dict(color='#00BCD4', width=3)
                        ))
                    fig3.update_layout(
                        height=250,
                        title="Сетевой трафик",
                        xaxis_title="Время",
                        yaxis_title="%",
                        showlegend=False,
                        margin=dict(t=50, b=30, l=50, r=30)
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with col_graph2:
                    fig4 = go.Figure()
                    # Задержка диска (если есть такая метрика)
                    latency_col = None
                    for col in filtered_df.columns:
                        if 'latency' in col.lower() or 'delay' in col.lower():
                            latency_col = col
                            break

                    if latency_col:
                        fig4.add_trace(go.Scatter(
                            x=filtered_df['timestamp'],
                            y=filtered_df[latency_col],
                            mode='lines',
                            name='Задержка',
                            line=dict(color='#FF9800', width=3)
                        ))
                    else:
                        # Если нет метрики задержки, показываем CPU ready
                        ready_col = 'cpu.ready.summation' if 'cpu.ready.summation' in filtered_df.columns else None
                        if ready_col:
                            fig4.add_trace(go.Scatter(
                                x=filtered_df['timestamp'],
                                y=filtered_df[ready_col],
                                mode='lines',
                                name='CPU Ready',
                                line=dict(color='#FF9800', width=3)
                            ))

                    fig4.update_layout(
                        height=250,
                        title="Задержка / CPU Ready",
                        xaxis_title="Время",
                        yaxis_title="Значение",
                        showlegend=False,
                        margin=dict(t=50, b=30, l=50, r=30)
                    )
                    st.plotly_chart(fig4, use_container_width=True)

                # Таблица с данными
                st.markdown("### 📋 Детальные данные")
                display_df = filtered_df[[
                    'timestamp', 'load_percentage',
                    cpu_col if cpu_col else 'load_percentage',
                    mem_col if mem_col in filtered_df.columns else 'load_percentage'
                ]].copy()

                # Переименовываем колонки для отображения
                display_df.columns = ['Время', 'Нагрузка', 'CPU', 'Память']
                st.dataframe(
                    display_df.tail(100),  # Показываем последние 100 записей
                    use_container_width=True,
                    height=300
                )
            else:
                st.info(f"📭 Нет данных для сервера '{selected_server}' за выбранный период.")

    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        import traceback
        with st.expander("Детали ошибки"):
            st.code(traceback.format_exc())
        st.info("💡 Убедитесь, что база данных доступна и содержит данные.")
