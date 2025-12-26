import streamlit as st
# from assets.style import apply_custom_styles

# add to config DASHBOARD_URL=http://127.0.0.1:8000

# Настройка страницы
st.set_page_config(
    page_title="Анализ нагрузки серверов",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def apply_custom_styles():
    """Применение кастомных стилей"""
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Применение стилей
apply_custom_styles()

# Импорт компонентов
from components.header import show_header
from components.sidebar import show_sidebar
from components.footer import show_footer

# Отображение компонентов
show_header()

# Создание центрированных табов
tab1, tab2, tab3 = st.tabs(["📈 **Факт**", "🔮 **Прогноз**", "📊 **Общий анализ**"])

# Импорт страниц
from pages import fact, forecast, analysis

# Вкладка 1: Факт
with tab1:
    fact.show()

# Вкладка 2: Прогноз
with tab2:
    forecast.show()

# Вкладка 3: Общий анализ
with tab3:
    analysis.show()

# Боковая панель
with st.sidebar:
    show_sidebar()

# Футер
show_footer()