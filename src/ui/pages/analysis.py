import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# Добавляем путь для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Теперь импортируем
try:
    from utils.data_generator import generate_server_data
except ImportError:
    # Fallback для прямого импорта
    import importlib.util
    import pathlib



@st.cache_data
def load_data():
    return generate_server_data()


def show():
    """Страница общего анализа"""
    st.markdown('<h2 class="sub-header">📊 Общий анализ нагрузки серверов</h2>', unsafe_allow_html=True)

    # Загрузка данных
    df = load_data()

    # Выбор даты для анализа
    col_date1, col_date2 = st.columns([1, 3])

    with col_date1:
        st.markdown('<div class="server-selector fade-in">', unsafe_allow_html=True)

        analysis_date = st.date_input(
            "**Выберите дату:**",
            df['timestamp'].max().date(),
            min_value=df['timestamp'].min().date(),
            max_value=df['timestamp'].max().date(),
            key="analysis_date_picker"
        )

        st.markdown("### 🎛️ Фильтры")

        # Фильтр по типу сервера
        server_types = st.multiselect(
            "**Типы серверов:**",
            ["Все", "Web", "API", "Database", "Cache", "Analytics"],
            default=["Все"]
        )

        # Фильтр по нагрузке
        min_load, max_load = st.slider(
            "**Диапазон нагрузки (%):**",
            0, 100, (0, 100),
            key="load_range"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with col_date2:
        # Фильтрация данных
        analysis_df = df[df['timestamp'].dt.date == analysis_date].copy()

        if not analysis_df.empty:
            # Применение фильтров
            if "Все" not in server_types:
                analysis_df = analysis_df[
                    analysis_df['server'].str.contains('|'.join(server_types), case=False)
                ]

            analysis_df = analysis_df[
                (analysis_df['load_percentage'] >= min_load) &
                (analysis_df['load_percentage'] <= max_load)
                ]
