import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Добавляем путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Теперь импортируем
try:
    from utils.data_generator import generate_server_data
    from utils.alert_rules import alert_system, ServerStatus, AlertSeverity
except ImportError:
    # Fallback для прямого импорта
    import importlib.util
    import pathlib

    # Импортируем data_generator
    data_generator_path = os.path.join(parent_dir, 'utils', 'data_generator.py')
    spec = importlib.util.spec_from_file_location("data_generator", data_generator_path)
    data_generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_generator)
    generate_server_data = data_generator.generate_server_data

    # Импортируем alert_rules
    alert_rules_path = os.path.join(parent_dir, 'utils', 'alert_rules.py')
    spec = importlib.util.spec_from_file_location("alert_rules", alert_rules_path)
    alert_rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alert_rules)
    alert_system = alert_rules.alert_system
    ServerStatus = alert_rules.ServerStatus
    AlertSeverity = alert_rules.AlertSeverity


@st.cache_data
def load_data():
    return generate_server_data()


def show_alert_settings():
    """Настройка параметров алертов"""
    with st.expander("⚙️ **Настройка правил алертов**", expanded=False):
        st.markdown("### Пороговые значения")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📊 Загруженность**")
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
        # Загрузка данных
        df = load_data()
        servers = sorted(df['server'].unique())

        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown('<div class="server-selector fade-in">', unsafe_allow_html=True)

            # Выбор сервера
            selected_server = st.selectbox(
                "**Выберите сервер:**",
                servers,
                index=0,
                key="fact_server"
            )

            # Выбор дат
            min_date = df['timestamp'].min().date()
            max_date = df['timestamp'].max().date()

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

            # Кнопка анализа
            analyze_btn = st.button(
                "🔍 Анализировать алерты",
                type="primary",
                use_container_width=True,
                key="analyze_alerts"
            )

            st.markdown('</div>', unsafe_allow_html=True)

            # Фильтрация данных
            start_datetime = pd.Timestamp(start_date)
            end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1)

            filtered_df = df[
                (df['server'] == selected_server) &
                (df['timestamp'] >= start_datetime) &
                (df['timestamp'] <= end_datetime)
                ].copy()

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

                        # Сводка метрик
                        if analysis_result.get('metrics_summary'):
                            st.markdown("### 📊 Сводка метрик")
                            metrics_df = pd.DataFrame(analysis_result['metrics_summary']).T
                            st.dataframe(
                                metrics_df.style.format("{:.1f}"),
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Ошибка при анализе: {e}")

            # Базовые метрики
            if not filtered_df.empty:
                st.markdown("### 📈 Основные метрики")

                col_metric1, col_metric2, col_metric3 = st.columns(3)
                with col_metric1:
                    avg_load = filtered_df['load_percentage'].mean()
                    st.metric("Нагрузка", f"{avg_load:.1f}%")

                with col_metric2:
                    avg_cpu = filtered_df['cpu_usage'].mean()
                    st.metric("CPU", f"{avg_cpu:.1f}%")

                with col_metric3:
                    avg_mem = filtered_df['memory_usage'].mean()
                    st.metric("Память", f"{avg_mem:.1f}%")

        with col2:
            if not filtered_df.empty:
                # Дашборды
                st.markdown("### 📊 Мониторинг метрик")

                # График 1: Нагрузка и CPU
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=filtered_df['load_percentage'],
                    mode='lines',
                    name='Нагрузка',
                    line=dict(color='#1E88E5', width=3)
                ))
                fig1.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=filtered_df['cpu_usage'],
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
                fig2.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=filtered_df['memory_usage'],
                    mode='lines',
                    name='Память',
                    line=dict(color='#4CAF50', width=3)
                ))
                fig2.add_trace(go.Scatter(
                    x=filtered_df['timestamp'],
                    y=filtered_df['disk_usage'],
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
                    fig3.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df['network_in_mbps'],
                        mode='lines',
                        name='Трафик',
                        line=dict(color='#00BCD4', width=3)
                    ))
                    fig3.update_layout(
                        height=250,
                        title="Сетевой трафик",
                        xaxis_title="Время",
                        yaxis_title="Mbps",
                        showlegend=False,
                        margin=dict(t=50, b=30, l=50, r=30)
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                with col_graph2:
                    fig4 = go.Figure()
                    fig4.add_trace(go.Scatter(
                        x=filtered_df['timestamp'],
                        y=filtered_df['disk_latency'],
                        mode='lines',
                        name='Задержка',
                        line=dict(color='#FF9800', width=3)
                    ))
                    fig4.update_layout(
                        height=250,
                        title="Задержка диска",
                        xaxis_title="Время",
                        yaxis_title="ms",
                        showlegend=False,
                        margin=dict(t=50, b=30, l=50, r=30)
                    )
                    st.plotly_chart(fig4, use_container_width=True)

    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        st.info("Пожалуйста, проверьте наличие файлов данных")