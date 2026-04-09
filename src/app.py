"""
app.py - Streamlit Web UI cho Teky Parent Chatbot.
Chạy: cd src && streamlit run app.py
"""

import json
import streamlit as st
from pathlib import Path

from tools import list_available_students, load_student_data, DATA_DIR
from scoring import compute_all_scores
from dashboard import render_full_dashboard
from agent import run_agent_web, CONTACT_INFO, FALLBACK_TEXT

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Teky - Trợ lý Phụ huynh",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .mode-button {
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .mode-button:hover {
        transform: scale(1.02);
    }
    .contact-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .stChatMessage {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────
def init_session():
    defaults = {
        "mode": None,           # None, "advisor", "analyst"
        "student_name": None,
        "student_data": None,
        "all_scores": None,
        "chat_history": [],     # List of {"role": "user"/"assistant", "content": str}
        "agent_history": [],    # LangChain message objects for multi-turn
        "fallback_count": 0,
        "show_dashboard": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()


# ─────────────────────────────────────────────
# Helper: Load course data
# ─────────────────────────────────────────────
@st.cache_data
def load_courses():
    course_file = DATA_DIR / "courses.json"
    if course_file.exists():
        with open(course_file, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.image("https://teky.edu.vn/wp-content/uploads/2021/08/teky-logo.png", width=150)
        st.markdown("### 🎓 Teky - Trợ lý Phụ huynh")
        st.divider()

        if st.session_state.mode:
            mode_label = "📚 Tư vấn khóa học" if st.session_state.mode == "advisor" else "📊 Kiểm tra lộ trình"
            st.info(f"Chế độ: **{mode_label}**")

            if st.session_state.student_name:
                st.success(f"Học sinh: **{st.session_state.student_name}**")

            if st.button("🔄 Quay lại menu chính", use_container_width=True):
                for key in ["mode", "student_name", "student_data", "all_scores",
                            "chat_history", "agent_history", "show_dashboard"]:
                    st.session_state[key] = None if key != "chat_history" else []
                    if key == "agent_history":
                        st.session_state[key] = []
                st.session_state.fallback_count = 0
                st.session_state.show_dashboard = False
                st.rerun()

        st.divider()
        st.markdown("#### 📞 Liên hệ hỗ trợ")
        st.markdown(f"**Hotline**: {CONTACT_INFO.get('hotline', '1900-6232')}")
        st.markdown(f"**Email**: {CONTACT_INFO.get('email', 'support@teky.edu.vn')}")
        st.markdown(f"**Giờ LV**: {CONTACT_INFO.get('working_hours', '8:00-21:00')}")


# ─────────────────────────────────────────────
# Mode Selection Screen
# ─────────────────────────────────────────────
def render_mode_selection():
    st.markdown("<div class='main-header'>", unsafe_allow_html=True)
    st.markdown("# 🎓 Teky - Trợ lý Phụ huynh")
    st.markdown("Xin chào! Tôi có thể hỗ trợ phụ huynh những gì?")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### 📊 Kiểm tra lộ trình học")
        st.markdown("Xem kết quả học tập, điểm kĩ năng 4C, tiến bộ qua từng buổi học của con.")
        if st.button("Kiểm tra lộ trình học của con", key="btn_analyst",
                     use_container_width=True, type="primary"):
            st.session_state.mode = "analyst"
            st.rerun()

    with col2:
        st.markdown("### 📚 Tư vấn khóa học")
        st.markdown("Tìm hiểu về các khóa học lập trình, lộ trình phù hợp cho con.")
        if st.button("Tư vấn khóa học", key="btn_advisor",
                     use_container_width=True, type="secondary"):
            st.session_state.mode = "advisor"
            st.rerun()


# ─────────────────────────────────────────────
# Student Selection Screen
# ─────────────────────────────────────────────
def render_student_selection():
    st.markdown("### 📊 Kiểm tra lộ trình học")
    st.markdown("Vui lòng cho biết **tên con** để tôi tra cứu kết quả học tập.")

    available = list_available_students()
    # Filter out non-student files like courses, contact, rubric
    student_files = [s for s in available if s.lower() not in ["courses", "contact", "rubric"]]

    if not student_files:
        st.warning("Chưa có dữ liệu học sinh nào trong hệ thống.")
        return

    # Dropdown selection
    selected = st.selectbox(
        "Chọn học sinh:",
        options=["-- Chọn tên con --"] + student_files,
        index=0,
    )

    if selected != "-- Chọn tên con --":
        if st.button("✅ Xác nhận", type="primary"):
            try:
                data = load_student_data(selected)
                st.session_state.student_name = selected
                st.session_state.student_data = data
                st.session_state.all_scores = compute_all_scores(data)
                st.session_state.show_dashboard = True
                st.session_state.chat_history = [{
                    "role": "assistant",
                    "content": f"Đã tìm thấy dữ liệu của **{selected}**! "
                               f"Phụ huynh có thể xem dashboard bên trên hoặc hỏi tôi bất kỳ câu hỏi nào về quá trình học của con."
                }]
                st.rerun()
            except FileNotFoundError:
                st.error(f"Không tìm thấy dữ liệu cho '{selected}'.")


# ─────────────────────────────────────────────
# Fallback Contact Card
# ─────────────────────────────────────────────
def render_fallback_card(key: str = None):
    import uuid
    if key is None:
        key = f"fallback_btn_{uuid.uuid4().hex}"
        
    st.markdown(f"""
    <div class="contact-card">
        <h3>📞 Liên hệ Teky để được hỗ trợ trực tiếp</h3>
        <p>{CONTACT_INFO.get('fallback_message', '')}</p>
        <p><strong>Hotline</strong>: {CONTACT_INFO.get('hotline', '1900-6232')}</p>
        <p><strong>Zalo OA</strong>: {CONTACT_INFO.get('zalo_oa', 'Teky')}</p>
        <p><strong>Email</strong>: {CONTACT_INFO.get('email', 'support@teky.edu.vn')}</p>
        <p><strong>Giờ làm việc</strong>: {CONTACT_INFO.get('working_hours', '8:00 - 21:00')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            "📞 Gọi tổng đài",
            f"tel:{CONTACT_INFO.get('hotline', '19006232')}",
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 Thử lại", use_container_width=True, key=key):
            st.session_state.fallback_count = 0
            st.rerun()


# ─────────────────────────────────────────────
# Chat Interface
# ─────────────────────────────────────────────
def render_chat(mode: str):
    # Show dashboard for analyst mode
    if mode == "analyst" and st.session_state.show_dashboard and st.session_state.all_scores:
        with st.expander("📊 Dashboard học tập", expanded=True):
            render_full_dashboard(
                st.session_state.all_scores,
                student_data=st.session_state.student_data,
            )

    st.divider()

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Check if fallback limit reached
    if st.session_state.fallback_count >= 2:
        render_fallback_card()

    # Chat input
    if prompt := st.chat_input("Nhập câu hỏi của phụ huynh..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Đang xử lý..."):
                # Prepare data
                if mode == "advisor":
                    data = load_courses()
                else:
                    data = st.session_state.student_data

                result = run_agent_web(
                    question=prompt,
                    mode=mode,
                    student_name=st.session_state.student_name or "",
                    data=data,
                    history=st.session_state.agent_history,
                    fallback_count=st.session_state.fallback_count,
                )

                answer = result["answer"]
                st.session_state.fallback_count = result["fallback_count"]

                # Update agent history (keep only Human/AI messages, limit to last 10)
                from langchain_core.messages import HumanMessage, AIMessage
                st.session_state.agent_history = []
                for m in result["messages"][-15:]:
                    if isinstance(m, HumanMessage):
                        st.session_state.agent_history.append(m)
                    elif isinstance(m, AIMessage) and m.content:
                        # Chỉ giữ lại văn bản, loại bỏ các tool_calls để tránh lỗi LLM ở lượt sau
                        st.session_state.agent_history.append(AIMessage(content=m.content))

                st.markdown(answer)

                # Show fallback card if triggered multiple times
                if result["fallback_triggered"] and st.session_state.fallback_count >= 2:
                    render_fallback_card()

        st.session_state.chat_history.append({"role": "assistant", "content": answer})


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────
def main():
    render_sidebar()

    if st.session_state.mode is None:
        render_mode_selection()
    elif st.session_state.mode == "analyst" and st.session_state.student_name is None:
        render_student_selection()
    elif st.session_state.mode == "advisor":
        st.markdown("### 📚 Tư vấn khóa học Teky")
        if not st.session_state.chat_history:
            st.session_state.chat_history = [{
                "role": "assistant",
                "content": "Xin chào phụ huynh! Tôi là trợ lý tư vấn khóa học Teky. "
                           "Phụ huynh muốn tìm hiểu khóa học nào cho con ạ? "
                           "Cho tôi biết **tuổi** và **sở thích** của con để tư vấn chính xác nhất nhé!"
            }]
        render_chat("advisor")
    elif st.session_state.mode == "analyst":
        st.markdown(f"### 📊 Lộ trình học của **{st.session_state.student_name}**")
        render_chat("analyst")


if __name__ == "__main__":
    main()
