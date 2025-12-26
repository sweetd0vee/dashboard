import streamlit as st

def show_header():
    """Отображение заголовка"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-header">📊 Система мониторинга нагрузки серверов</h1>
        <div style="text-align: center; margin-bottom: 2rem; color: #666;">
            <p>Мониторинг в реальном времени • Прогнозирование • Аналитика</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
