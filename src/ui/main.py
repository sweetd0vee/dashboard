import streamlit as st
# from assets.style import apply_custom_styles

from auth import require_auth, get_current_user, has_role

# import os
# from dotenv import load_dotenv
# add to config DASHBOARD_URL=http://127.0.0.1:8000

# Настройка страницы
st.set_page_config(
    page_title="Анализ нагрузки серверов",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния сессии для аутентификации
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'role' not in st.session_state:
    st.session_state.role = None


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


@require_auth
def main():

    # Информация о пользователе в заголовке
    user = get_current_user()

    # Заголовок с информацией о пользователе
    col_header1, col_header2, col_header3  = st.columns([5, 1, 1])
    with col_header2:
        if user:
            role_badge = {
                "admin": "Админ",
                "user": "Пользователь",
                "viewer": "Наблюдатель"
            }.get(user.get("role", ""), "Гость")

            st.markdown(f"""
                <div class="user-info">
                    <strong>{user.get('name', 'Пользователь')}</strong><br>
                    <small>{role_badge}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_header3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Выход", use_container_width=True):
            from auth import logout_user
            logout_user()
            return

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


if __name__ == "__main__":
    main()
