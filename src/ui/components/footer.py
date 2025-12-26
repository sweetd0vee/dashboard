import streamlit as st
from datetime import datetime


def show_footer():
    """Отображение футера"""
    current_year = datetime.now().year

    st.divider()
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>📊 Система мониторинга нагрузки серверов | Версия 1.0</p>
        <p>© {current_year} Все права защищены. Данные обновляются в реальном времени.</p>
        <p style="font-size: 0.8rem; margin-top: 10px;">
            <a href="#" style="color: #1E88E5; text-decoration: none;">Политика конфиденциальности</a> • 
            <a href="#" style="color: #1E88E5; text-decoration: none;">Условия использования</a> • 
            <a href="#" style="color: #1E88E5; text-decoration: none;">Техническая поддержка</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
