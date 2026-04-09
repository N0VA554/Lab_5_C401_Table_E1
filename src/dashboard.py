"""
dashboard.py - Plotly chart components cho Streamlit dashboard
Hiển thị trực quan dữ liệu học tập: 4C radar, progress line, category bar, score table.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from scoring import compute_course_average


# ─────────────────────────────────────────────
# Color palette
# ─────────────────────────────────────────────
COLORS = {
    "Critical Thinking": "#FF6B6B",
    "Collaboration": "#4ECDC4",
    "Creativity": "#FFE66D",
    "Communication": "#A78BFA",
    "Kiến thức": "#3B82F6",
    "Kĩ Năng": "#10B981",
    "Sản phẩm": "#F59E0B",
    "Thái độ học tập": "#EF4444",
}

C4_LABELS_VN = {
    "Critical Thinking": "Tư duy phản biện",
    "Collaboration": "Hợp tác",
    "Creativity": "Sáng tạo",
    "Communication": "Giao tiếp",
}


def render_student_summary(student_info: dict, total_lessons: int):
    """Hiển thị thông tin tổng quan học sinh."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Học sinh", student_info.get("name", "N/A"))
    with col2:
        st.metric("Khóa học", student_info.get("course", "N/A"))
    with col3:
        st.metric("Số buổi học", total_lessons)


def render_4c_radar_chart(c4_scores: dict, lesson_title: str = "Buổi mới nhất",
                          c4_compare: dict = None, compare_title: str = ""):
    """
    Radar chart kĩ năng 4C, hỗ trợ so sánh 2 buổi.
    c4_scores: {"Critical Thinking": 3.0, "Collaboration": 2.5, ...}
    c4_compare: (optional) scores buổi trước để so sánh
    """
    if not c4_scores:
        st.info("Chưa có dữ liệu 4C để hiển thị.")
        return

    # Đảm bảo thứ tự cố định
    skill_order = ["Critical Thinking", "Collaboration", "Creativity", "Communication"]
    labels_vn = [C4_LABELS_VN.get(c, c) for c in skill_order]
    values = [c4_scores.get(c, 0) for c in skill_order]

    # Đóng radar
    values_closed = values + [values[0]]
    labels_closed = labels_vn + [labels_vn[0]]

    fig = go.Figure()

    # So sánh buổi trước (nếu có)
    if c4_compare:
        compare_values = [c4_compare.get(c, 0) for c in skill_order]
        compare_closed = compare_values + [compare_values[0]]
        fig.add_trace(go.Scatterpolar(
            r=compare_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor="rgba(200, 200, 200, 0.2)",
            line=dict(color="#aaa", width=1, dash="dash"),
            marker=dict(size=5, color="#aaa"),
            name=compare_title or "Buổi trước",
        ))

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(78, 205, 196, 0.3)",
        line=dict(color="#4ECDC4", width=2),
        marker=dict(size=8, color="#4ECDC4"),
        name=lesson_title,
        text=[f"{v:.1f}/4" for v in values_closed],
        hovertemplate="%{theta}: %{r:.1f}/4<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 4.2],
                tickvals=[1, 2, 3, 4],
                ticktext=["1", "2", "3", "4"],
                gridcolor="rgba(0,0,0,0.1)",
            ),
            angularaxis=dict(gridcolor="rgba(0,0,0,0.1)"),
        ),
        title=dict(text=f"Kĩ năng 4C - {lesson_title}", x=0.5),
        showlegend=bool(c4_compare),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=420,
        margin=dict(t=60, b=60),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_progress_line_chart(c4_progress: list):
    """
    Line chart tiến bộ 4C qua các buổi học.
    c4_progress: [{"lesson": 1, "title": "...", "scores": {"Critical Thinking": 1.0, ...}}, ...]
    """
    if not c4_progress:
        st.info("Chưa có dữ liệu tiến bộ.")
        return

    rows = []
    for entry in c4_progress:
        lesson = entry["lesson"]
        for skill, score in entry["scores"].items():
            rows.append({
                "Buổi": f"Buổi {lesson}",
                "Kĩ năng": C4_LABELS_VN.get(skill, skill),
                "Điểm": score,
                "skill_key": skill,
            })

    df = pd.DataFrame(rows)
    color_map = {C4_LABELS_VN.get(k, k): v for k, v in COLORS.items()}

    fig = px.line(
        df,
        x="Buổi",
        y="Điểm",
        color="Kĩ năng",
        markers=True,
        color_discrete_map=color_map,
        title="Tiến bộ kĩ năng 4C qua các buổi học",
    )
    fig.update_yaxes(range=[0, 4.2], dtick=1)
    fig.update_layout(height=400, margin=dict(t=60, b=40))

    st.plotly_chart(fig, use_container_width=True)


def render_category_bar_chart(category_latest: dict):
    """
    Bar chart so sánh 4 nhóm tiêu chí (buổi mới nhất).
    category_latest: {"Kiến thức": 3.5, "Kĩ Năng": 2.8, ...}
    """
    if not category_latest:
        st.info("Chưa có dữ liệu nhóm tiêu chí.")
        return

    categories = list(category_latest.keys())
    scores = list(category_latest.values())
    colors = [COLORS.get(c, "#888") for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=scores,
        marker_color=colors,
        text=[f"{s:.1f}" for s in scores],
        textposition="outside",
    ))
    fig.update_yaxes(range=[0, 4.5], dtick=1)
    fig.update_layout(
        title=dict(text="Điểm trung bình theo nhóm tiêu chí (Buổi mới nhất)", x=0.5),
        xaxis_title="Nhóm tiêu chí",
        yaxis_title="Điểm (hệ 4)",
        height=400,
        margin=dict(t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_category_progress_chart(category_progress: list):
    """
    Line chart tiến bộ theo 4 nhóm tiêu chí qua các buổi.
    """
    if not category_progress:
        return

    rows = []
    for entry in category_progress:
        lesson = entry["lesson"]
        for cat, score in entry["scores"].items():
            rows.append({
                "Buổi": f"Buổi {lesson}",
                "Nhóm": cat,
                "Điểm": score,
            })

    df = pd.DataFrame(rows)
    color_map = {k: v for k, v in COLORS.items() if k in df["Nhóm"].unique()}

    fig = px.line(
        df,
        x="Buổi",
        y="Điểm",
        color="Nhóm",
        markers=True,
        color_discrete_map=color_map,
        title="Tiến bộ theo nhóm tiêu chí qua các buổi học",
    )
    fig.update_yaxes(range=[0, 4.2], dtick=1)
    fig.update_layout(height=400, margin=dict(t=60, b=40))

    st.plotly_chart(fig, use_container_width=True)


def render_score_table(lesson_scores: list):
    """
    Bảng chi tiết điểm từng tiêu chí cho mỗi buổi học.
    Dùng st.expander để collapsible.
    """
    if not lesson_scores:
        st.info("Chưa có dữ liệu chi tiết.")
        return

    for ls in reversed(lesson_scores):  # Mới nhất trước
        with st.expander(f"Buổi {ls['lesson_number']} - {ls['title']}", expanded=False):
            rows = []
            for cat_name, cat_data in ls["categories"].items():
                for detail in cat_data["details"]:
                    score = detail["score"]
                    # Emoji indicator
                    if score >= 3.5:
                        indicator = "🟢"
                    elif score >= 2.5:
                        indicator = "🟡"
                    elif score >= 1.5:
                        indicator = "🟠"
                    else:
                        indicator = "🔴"

                    rows.append({
                        "Nhóm": cat_name,
                        "Tiêu chí": detail["criteria"],
                        "Nhận xét": detail["comment"],
                        "Điểm": f"{indicator} {score:.1f}/4",
                    })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Điểm TB: Kiến thức={ls['categories'].get('Kiến thức', {}).get('avg', 'N/A')} | "
                       f"Kĩ năng={ls['categories'].get('Kĩ Năng', {}).get('avg', 'N/A')} | "
                       f"Sản phẩm={ls['categories'].get('Sản phẩm', {}).get('avg', 'N/A')} | "
                       f"Thái độ={ls['categories'].get('Thái độ học tập', {}).get('avg', 'N/A')}")


def render_course_average_radar(c4_avg: dict):
    """
    Radar chart kĩ năng 4C trung bình TOÀN KHÓA.
    c4_avg: {"Critical Thinking": float, "Collaboration": float, ...}
    """
    if not c4_avg:
        st.info("Chưa có dữ liệu 4C trung bình toàn khóa.")
        return

    skill_order = ["Critical Thinking", "Collaboration", "Creativity", "Communication"]
    labels_vn = [C4_LABELS_VN.get(c, c) for c in skill_order]
    values = [c4_avg.get(c, 0) for c in skill_order]
    values_closed = values + [values[0]]
    labels_closed = labels_vn + [labels_vn[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(167, 139, 250, 0.3)",
        line=dict(color="#A78BFA", width=2.5),
        marker=dict(size=9, color="#A78BFA"),
        name="Trung bình cả khóa",
        text=[f"{v:.2f}/4" for v in values_closed],
        hovertemplate="%{theta}: %{r:.2f}/4<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 4.2],
                tickvals=[1, 2, 3, 4],
                ticktext=["1", "2", "3", "4"],
                gridcolor="rgba(0,0,0,0.1)",
            ),
            angularaxis=dict(gridcolor="rgba(0,0,0,0.1)"),
        ),
        title=dict(text="Kĩ năng 4C — Trung bình toàn khóa", x=0.5),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=420,
        margin=dict(t=60, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_course_category_bar_chart(category_avg: dict):
    """
    Bar chart 4 nhóm tiêu chí trung bình TOÀN KHÓA.
    category_avg: {"Kiến thức": float, "Kĩ Năng": float, "Sản phẩm": float, "Thái độ học tập": float}
    """
    if not category_avg:
        st.info("Chưa có dữ liệu nhóm tiêu chí toàn khóa.")
        return

    categories = list(category_avg.keys())
    scores = list(category_avg.values())
    colors = [COLORS.get(c, "#888") for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=scores,
        marker_color=colors,
        marker=dict(
            color=colors,
            line=dict(color="rgba(0,0,0,0.15)", width=1),
        ),
        text=[f"{s:.2f}" for s in scores],
        textposition="outside",
    ))
    # Đường tham chiếu 3.0 (mức khá)
    fig.add_hline(
        y=3.0,
        line_dash="dash",
        line_color="rgba(100,100,100,0.5)",
        annotation_text="Mức Khá (3.0)",
        annotation_position="top right",
    )
    fig.update_yaxes(range=[0, 4.6], dtick=1)
    fig.update_layout(
        title=dict(text="Điểm trung bình toàn khóa theo nhóm tiêu chí", x=0.5),
        xaxis_title="Nhóm tiêu chí",
        yaxis_title="Điểm (hệ 4)",
        height=400,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_full_dashboard(all_scores: dict, student_data: list = None):
    """
    Render toàn bộ dashboard từ kết quả compute_all_scores.
    - all_scores: kết quả từ compute_all_scores()
    - student_data: dữ liệu gốc (để tính trung bình toàn khóa), nếu None sẽ bỏ qua section này.
    """
    if "error" in all_scores:
        st.error(all_scores["error"])
        return

    summary = all_scores["summary"]
    student = all_scores["student"]
    lessons = all_scores["lessons"]

    # Header
    render_student_summary(student, summary["total_lessons"])
    st.divider()

    # ─── SECTION 1: TỔNG KẾT TOÀN KHÓA ───
    st.subheader("🎯 Tổng kết toàn khóa học")
    if student_data is not None:
        try:
            course_avg = compute_course_average(student_data)
            if "error" not in course_avg:
                # Metrics nhanh
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                c4_avg = course_avg["4c_avg"]
                cat_avg = course_avg["category_avg"]

                # 4C avg metrics
                c4_items = [
                    ("Tư duy phản biện", c4_avg.get("Critical Thinking", 0)),
                    ("Hợp tác", c4_avg.get("Collaboration", 0)),
                    ("Sáng tạo", c4_avg.get("Creativity", 0)),
                    ("Giao tiếp", c4_avg.get("Communication", 0)),
                ]
                for col, (label, val) in zip(
                    [col_m1, col_m2, col_m3, col_m4], c4_items
                ):
                    with col:
                        delta = None
                        if val >= 3.0:
                            delta_color = "normal"
                        elif val >= 2.0:
                            delta_color = "off"
                        else:
                            delta_color = "inverse"
                        st.metric(label=label, value=f"{val:.2f}/4")

                st.caption(
                    "💡 **Thành tích**: 0–1 = Cần cố gắng | 1–2 = Đang tiến bộ | 2–3 = Khá | 3–4 = Tốt/Xuất sắc"
                )

                st.divider()

                # Biểu đồ toàn khóa
                col_a, col_b = st.columns(2)
                with col_a:
                    render_course_average_radar(c4_avg)
                with col_b:
                    render_course_category_bar_chart(cat_avg)
        except Exception as e:
            st.warning(f"Không thể hiển thị biểu đồ toàn khóa: {e}")
    else:
        st.info("Dữ liệu gốc chưa được cung cấp. Không thể tính trung bình toàn khóa.")

    st.divider()

    # ─── SECTION 2: THÔNG TIN TỪ̀NG BUỔ̉I HỌC ───
    st.subheader("📊 Chi tiết từng buổi học")

    # Lesson selector cho radar chart
    lesson_options = [f"Buổi {ls['lesson_number']} - {ls['title']}" for ls in lessons]
    selected_idx = st.selectbox(
        "Chọn buổi học để xem chi tiết 4C:",
        range(len(lesson_options)),
        index=len(lesson_options) - 1,  # Default buổi mới nhất
        format_func=lambda i: lesson_options[i],
        key="lesson_selector",
    )

    selected_lesson = lessons[selected_idx]
    compare_lesson = lessons[selected_idx - 1] if selected_idx > 0 else None

    # Row 1: Radar + Category Bar
    col1, col2 = st.columns(2)
    with col1:
        render_4c_radar_chart(
            selected_lesson["4c"],
            lesson_title=f"Buổi {selected_lesson['lesson_number']}",
            c4_compare=compare_lesson["4c"] if compare_lesson else None,
            compare_title=f"Buổi {compare_lesson['lesson_number']}" if compare_lesson else "",
        )
    with col2:
        cat_scores = {cat: data["avg"] for cat, data in selected_lesson["categories"].items()}
        render_category_bar_chart(cat_scores)

    # Row 2: Progress charts
    col3, col4 = st.columns(2)
    with col3:
        render_progress_line_chart(summary["4c_progress"])
    with col4:
        render_category_progress_chart(summary["category_progress"])

    # Row 3: Detail table
    st.subheader("Chi tiết điểm từng buổi học")
    render_score_table(all_scores["lessons"])
