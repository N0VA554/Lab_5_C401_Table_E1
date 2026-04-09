"""
agent.py - LangGraph agent cho chatbot Teky hỗ trợ phụ huynh.
Hỗ trợ 2 mode: advisor (tư vấn khóa học) và analyst (phân tích học tập).
Tích hợp fallback escalation khi không thể giải đáp.
"""

import json
import os
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from tools import (
    ALL_TOOLS,
    analyze_intent,
    generate_query,
    query_json,
    get_student_scores,
    answer_lesson_question,
    get_course_summary_scores,
    get_lesson_group_comments,
    get_specific_criteria_comment,
    load_student_data,
    list_available_students,
    get_llm,
    DATA_DIR,
)
from logger import log_token_usage

load_dotenv()


# ─────────────────────────────────────────────
# Load contact info cho fallback
# ─────────────────────────────────────────────
CONTACT_FILE = DATA_DIR / "contact.json"
if CONTACT_FILE.exists():
    with open(CONTACT_FILE, encoding="utf-8") as f:
        CONTACT_INFO = json.load(f)
else:
    CONTACT_INFO = {
        "hotline": "1900-6232",
        "email": "support@teky.edu.vn",
        "fallback_message": "Vui lòng liên hệ tổng đài để được hỗ trợ.",
    }

FALLBACK_TEXT = (
    f"\n\n---\n"
    f"📞 **Tổng đài Teky**: {CONTACT_INFO.get('hotline', '1900-6232')}\n"
    f"💬 **Zalo OA**: {CONTACT_INFO.get('zalo_oa', 'Teky')}\n"
    f"📧 **Email**: {CONTACT_INFO.get('email', 'support@teky.edu.vn')}\n"
    f"🕐 **Giờ làm việc**: {CONTACT_INFO.get('working_hours', '8:00 - 21:00')}\n"
)


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    json_data: Any
    student_name: str
    mode: str  # 'advisor' hoặc 'analyst'
    intent: str
    query: str
    query_result: Any
    fallback_count: int  # Đếm số lần không trả lời được


# ─────────────────────────────────────────────
# LLM + Tools binding
# ─────────────────────────────────────────────
llm = get_llm(temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────
SCOPE_INSTRUCTION = """
PHẠM VI HOẠT ĐỘNG (BẮT BUỘC):
- Bạn CHỈ trả lời các câu hỏi liên quan đến Teky: khóa học lập trình, kết quả học tập, kĩ năng 4C, portfolio học viên.
- Nếu câu hỏi NGOÀI phạm vi (thời tiết, tin tức, toán học, v.v.), từ chối lịch sự và gợi ý câu hỏi phù hợp.
- Nếu không chắc chắn hoặc không đủ thông tin, hướng dẫn phụ huynh liên hệ tổng đài.

CÁCH TRẢ LỜI:
- Thân thiện, chuyên nghiệp, dùng tiếng Việt.
- Giải thích đơn giản, tránh thuật ngữ kĩ thuật.
- Nếu phụ huynh không hiểu, tự phân tích dữ liệu và giải thích bằng ví dụ cụ thể.
"""

SYSTEM_PROMPT_ADVISOR = f"""Bạn là chuyên gia tư vấn giáo dục tại Teky - Học viện Công nghệ Sáng tạo Teky.

NHIỆM VỤ: Giải đáp thắc mắc của phụ huynh về các khóa học lập trình cho trẻ em.
- Trả lời thân thiện, chuyên nghiệp, truyền cảm hứng.
- Nhấn mạnh lợi ích: phát triển tư duy logic, sáng tạo, kỹ năng giải quyết vấn đề, kĩ năng 4C.
- Nếu được hỏi về lộ trình, đưa ra gợi ý từ cơ bản đến nâng cao.
- Chủ động hỏi thêm thông tin (tuổi con, mục tiêu) nếu cần để tư vấn chính xác hơn.
- KHÔNG gọi các tool truy vấn dữ liệu học sinh trong chế độ này.
- Nếu phụ huynh hỏi về học phí cụ thể, lịch học, đăng ký, chính sách hoàn tiền → hướng dẫn liên hệ tổng đài.

THÔNG TIN LIÊN HỆ TEKY:
{json.dumps(CONTACT_INFO, ensure_ascii=False, indent=2)}

{SCOPE_INSTRUCTION}"""

CONTACT_INFO_TEXT = (
    f"Hotline: {CONTACT_INFO.get('hotline', '1900-6232')}, "
    f"Email: {CONTACT_INFO.get('email', 'support@teky.edu.vn')}, "
    f"Zalo OA: {CONTACT_INFO.get('zalo_oa', 'Teky')}, "
    f"Giờ LV: {CONTACT_INFO.get('working_hours', '8:00-21:00')}"
)

SYSTEM_PROMPT_ANALYST = """Bạn là trợ lý phân tích dữ liệu học viên Teky - chuyên phân tích quá trình học tập của học sinh.

DỮ LIỆU ĐIỂM SỐ CÓ SẴN (hệ 4, tối đa 4.0):
{scoring_summary}

CÁCH TRẢ LỜI:
- Dùng dữ liệu điểm số ở trên để trả lời TRỰC TIẾP, KHÔNG cần gọi tool nếu dữ liệu đã đủ.
- Giải thích ý nghĩa kĩ năng 4C cho phụ huynh:
  + Critical Thinking (Tư duy phản biện): khả năng lập luận, đặt câu hỏi, giải quyết vấn đề
  + Collaboration (Hợp tác): khả năng làm việc nhóm, điều phối
  + Creativity (Sáng tạo): khả năng đưa ra ý tưởng mới, thử nghiệm
  + Communication (Giao tiếp): khả năng trình bày, chia sẻ ý tưởng
- So sánh tiến bộ giữa các buổi khi có thể.
- Khi phụ huynh không hiểu, giải thích bằng ngôn ngữ đơn giản, có ví dụ cụ thể.
- Thang điểm: 0-1 = Cần cố gắng, 1-2 = Đang tiến bộ, 2-3 = Khá, 3-4 = Tốt/Xuất sắc.

QUYẾT ĐỊNH GỌI TOOL:

1. Phụ huynh hỏi TỔNG KẾT TOÀN KHÓA / điểm trung bình cả khóa:
   → Gọi: get_course_summary_scores(student_name='{student_name}')

2. Phụ huynh hỏi về MỘT BUỔI HỌC CỤ THỂ mà không chỉ định chi tiết (ví dụ: "buổi 3", "buổi học đầu tiên"):
   → Gọi: answer_lesson_question(student_name='{student_name}', lesson_number=<số_buổi>, question=<câu_hỏi>)
   → lesson_number là số thứ tự buổi (1, 2, 3...), dùng -1 cho buổi mới nhất.

3. Phụ huynh hỏi CỤ THỂ về TOÀN BỘ MỘT NHÓM đánh giá ("thái độ của con thế nào", "kỹ năng của con", "mức độ tập trung"):
   → Gọi: get_lesson_group_comments(student_name='{student_name}', lesson_number=<số>, group="Thái độ học tập" hoặc "Kiến thức"...)

4. Phụ huynh hỏi CHÍNH XÁC MỘT TIÊU CHÍ (ví dụ: "bài tập về nhà có làm không", "tư duy logic", "thái độ giao tiếp"):
   → Gọi: get_specific_criteria_comment(student_name='{student_name}', lesson_number=<số>, criteria=<từ khóa>)

5. Phụ huynh hỏi các khía cạnh phức tạp hơn không thuộc các loại trên:
   → BƯỚC 1: Gọi analyze_intent(question=<câu_hỏi>)
   → BƯỚC 2: Gọi generate_query(intent=INTENT_RESULT, lesson_index=-1)
   → BƯỚC 3: Gọi query_json(student_name='{student_name}', path=PATH_RESULT)

QUY TẮC:
- PHẢI sử dụng đúng student_name='{student_name}'.
- Trả lời bằng tiếng Việt, thân thiện, dùng ngôn ngữ phụ huynh dễ hiểu.
- Nếu không đủ thông tin, hướng dẫn liên hệ tổng đài: """ + CONTACT_INFO_TEXT + """

""" + SCOPE_INSTRUCTION


# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────
def _build_scoring_summary(student_data, student_name: str) -> str:
    """Tạo bản tóm tắt scoring data cho system prompt."""
    try:
        from scoring import compute_all_scores
        scores = compute_all_scores(student_data)
        if "error" in scores:
            return "Chưa có dữ liệu điểm."

        summary = scores["summary"]
        student = scores["student"]
        lines = []
        lines.append(f"Học sinh: {student.get('name', student_name)}")
        lines.append(f"Khóa học: {student.get('course', 'N/A')}")
        lines.append(f"Tổng số buổi: {summary['total_lessons']}")

        # 4C latest
        lines.append(f"\nĐiểm 4C buổi mới nhất:")
        for skill, score in summary["4c_latest"].items():
            lines.append(f"  - {skill}: {score}/4")

        # Category latest
        lines.append(f"\nĐiểm trung bình theo nhóm (buổi mới nhất):")
        for cat, avg in summary["category_latest"].items():
            lines.append(f"  - {cat}: {avg}/4")

        # Progress
        lines.append(f"\nTiến bộ 4C qua các buổi:")
        for entry in summary["4c_progress"]:
            scores_str = ", ".join(f"{k}: {v}" for k, v in entry["scores"].items())
            lines.append(f"  Buổi {entry['lesson']}: {scores_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"Lỗi tính điểm: {e}"


def agent_node(state: AgentState) -> AgentState:
    """Node chính: LLM quyết định nội dung phản hồi hoặc gọi tool."""
    mode = state.get("mode", "advisor")
    student_name = state.get("student_name", "unknown")

    if mode == "analyst":
        scoring_summary = _build_scoring_summary(state["json_data"], student_name)

        formatted_prompt = SYSTEM_PROMPT_ANALYST.format(
            student_name=student_name,
            scoring_summary=scoring_summary,
        )
        content = formatted_prompt
    else:
        course_data = state.get("json_data", {})
        content = (
            f"{SYSTEM_PROMPT_ADVISOR}\n\n"
            f"DỮ LIỆU KHÓA HỌC THỰC TẾ ĐỂ TƯ VẤN:\n"
            f"{json.dumps(course_data, ensure_ascii=False, indent=2)}"
        )

    system_msg = SystemMessage(content=content)
    messages = [system_msg] + state["messages"]

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: AgentState) -> AgentState:
    """Node thực thi các tool call."""
    last_message = state["messages"][-1]
    tool_results = []

    tool_fn_map = {
        "analyze_intent": analyze_intent,
        "generate_query": generate_query,
        "query_json": query_json,
        "get_student_scores": get_student_scores,
        "answer_lesson_question": answer_lesson_question,
        "get_course_summary_scores": get_course_summary_scores,
        "get_lesson_group_comments": get_lesson_group_comments,
        "get_specific_criteria_comment": get_specific_criteria_comment,
    }

    for tool_call in last_message.tool_calls:
        fn_name = tool_call["name"]
        fn_args = tool_call["args"]
        tool_id = tool_call["id"]

        fn = tool_fn_map.get(fn_name)
        if fn:
            try:
                result = fn.invoke(fn_args)
            except Exception as e:
                result = f"Lỗi khi gọi tool {fn_name}: {e}"
        else:
            result = f"Tool '{fn_name}' không tồn tại."

        tool_results.append(
            ToolMessage(content=str(result), tool_call_id=tool_id)
        )

    return {"messages": tool_results}


# ─────────────────────────────────────────────
# Graph Logic
# ─────────────────────────────────────────────
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


# ─────────────────────────────────────────────
# API cho Streamlit (multi-turn support)
# ─────────────────────────────────────────────
def run_agent_web(
    question: str,
    mode: str,
    student_name: str = "",
    data: Any = None,
    history: list = None,
    fallback_count: int = 0,
) -> dict:
    """
    Chạy agent cho web UI, hỗ trợ multi-turn.
    Returns: {
        "answer": str,
        "fallback_triggered": bool,
        "fallback_count": int,
        "messages": list (updated history),
    }
    """
    graph = build_graph()

    # Build message history
    messages = []
    if history:
        messages.extend(history)
    messages.append(HumanMessage(content=question))

    initial_state: AgentState = {
        "messages": messages,
        "json_data": data if data else {},
        "student_name": student_name,
        "mode": mode,
        "intent": "",
        "query": "",
        "query_result": None,
        "fallback_count": fallback_count,
    }

    try:
        final_state = graph.invoke(initial_state)
        answer = final_state["messages"][-1].content

        # Log token usage
        log_token_usage(final_state["messages"][-1], mode)

        # Check if fallback needed
        fallback_keywords = [
            "không thể", "liên hệ", "tổng đài", "xin lỗi", "ngoài phạm vi",
            "không có thông tin", "không tìm thấy",
        ]
        fallback_triggered = any(kw in answer.lower() for kw in fallback_keywords)

        if fallback_triggered:
            fallback_count += 1
            if fallback_count >= 2:
                # Append contact info
                answer += FALLBACK_TEXT

        return {
            "answer": answer,
            "fallback_triggered": fallback_triggered,
            "fallback_count": fallback_count,
            "messages": final_state["messages"],
        }

    except Exception as e:
        # System error → fallback immediately
        error_msg = (
            f"Xin lỗi, hệ thống đang gặp sự cố. "
            f"Phụ huynh vui lòng thử lại sau hoặc liên hệ trực tiếp."
            f"{FALLBACK_TEXT}"
        )
        return {
            "answer": error_msg,
            "fallback_triggered": True,
            "fallback_count": fallback_count + 1,
            "messages": messages + [AIMessage(content=error_msg)],
        }


def run_agent(question: str, mode: str, student_name: str = "", data: Any = None) -> str:
    """Backward-compatible wrapper cho CLI."""
    result = run_agent_web(question, mode, student_name, data)
    return result["answer"]


# ─────────────────────────────────────────────
# Interactive CLI (giữ cho backward compatibility)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import unicodedata
    import re

    def normalize_name(name: str) -> str:
        n = name.strip().lower()
        n = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'\s+', '', n)

    print("\n" + "🌟" * 30)
    print("   TEKY - TRỢ LÝ PHỤ HUYNH THÔNG MINH")
    print("\nChào mừng phụ huynh! Vui lòng chọn tính năng:")
    print("1️⃣. Tư vấn khóa học")
    print("2️⃣. Kiểm tra lộ trình học của con")

    selected_mode = ""
    while True:
        choice = input("\n👉 Nhập lựa chọn (1/2): ").strip()
        if choice == "1":
            selected_mode = "advisor"
            print("\n✅ Chế độ: TƯ VẤN KHÓA HỌC")
            break
        elif choice == "2":
            selected_mode = "analyst"
            print("\n✅ Chế độ: KIỂM TRA LỘ TRÌNH HỌC")
            break
        print("❌ Lựa chọn không hợp lệ.")

    student_input = ""
    student_data = None

    if selected_mode == "advisor":
        try:
            course_file = DATA_DIR / "courses.json"
            if course_file.exists():
                with open(course_file, encoding="utf-8") as f:
                    student_data = json.load(f)
            else:
                student_data = {"info": "Dữ liệu khóa học đang được cập nhật."}
        except Exception as e:
            print(f"⚠️ Không thể load dữ liệu khóa học: {e}")
            student_data = {}

    elif selected_mode == "analyst":
        available_students = list_available_students()
        print(f"📂 Học sinh sẵn có: {available_students}")

        while True:
            student_raw = input("\n👉 Vui lòng nhập Tên Học Sinh: ").strip()
            if not student_raw:
                continue

            norm_input = normalize_name(student_raw)
            target_found = ""
            for s in available_students:
                if normalize_name(s) == norm_input or s.lower() == student_raw.lower():
                    target_found = s
                    break

            if target_found:
                student_input = target_found
                student_data = load_student_data(student_input)
                print(f"✅ Đã xác nhận học sinh: {student_input}")
                break

            matches = [s for s in available_students if norm_input in normalize_name(s)]
            if len(matches) == 1:
                confirm = input(f"❓ Có phải bạn muốn tìm '{matches[0]}'? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    student_input = matches[0]
                    student_data = load_student_data(student_input)
                    break

            print(f"❌ Không tìm thấy. Thử lại hoặc gõ 'exit' để thoát.")
            if student_raw.lower() == 'exit':
                exit()

    print("\n💡 Chatbot đã sẵn sàng. Gõ 'exit' để dừng.")

    conversation_history = []
    fc = 0

    while True:
        prefix = "[Tư vấn]" if selected_mode == "advisor" else f"[{student_input}]"
        question = input(f"\n❓ {prefix}: ").strip()

        if question.lower() in ["exit", "quit", "thoát"]:
            print("👋 Tạm biệt phụ huynh!")
            break

        if not question:
            continue

        print("🤖 Bot đang suy nghĩ...")
        try:
            result = run_agent_web(
                question=question,
                mode=selected_mode,
                student_name=student_input,
                data=student_data,
                history=conversation_history,
                fallback_count=fc,
            )
            answer = result["answer"]
            fc = result["fallback_count"]
            # Keep only HumanMessage and AIMessage for history
            conversation_history = [
                m for m in result["messages"]
                if isinstance(m, (HumanMessage, AIMessage))
            ]
            print(f"🤖 Trả lời:\n{answer}")
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
