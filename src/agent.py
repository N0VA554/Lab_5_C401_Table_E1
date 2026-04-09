"""
LangGraph Agent - Phân tích dữ liệu học viên từ JSON
Tools: analyze_intent → generate_query → query_json
Hỗ trợ 2 chế độ: Tư vấn khóa học và Phân tích học tập
"""

import json
import os
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

# ─────────────────────────────────────────────
from tools import (
    ALL_TOOLS,
    analyze_intent,
    generate_query,
    query_json,
    load_student_data,
    list_available_students,
    get_llm,
)
from logger import log_token_usage

load_dotenv()

# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    json_data: Any                      # dữ liệu JSON gốc
    student_name: str                   # Tên học sinh đang truy vấn
    mode: str                           # 'advisor' (tư vấn) hoặc 'analyst' (phân tích)
    intent: str                         # ý định đã phân tích
    query: str                          # query path được generate
    query_result: Any                   # kết quả sau query


# ─────────────────────────────────────────────
# LLM + Tools binding
# ─────────────────────────────────────────────
llm = get_llm(temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────
SYSTEM_PROMPT_ADVISOR = """Bạn là chuyên gia tư vấn giáo dục tại VinCare. 

NHIỆM VỤ: Giải đáp thắc mắc của phụ huynh về các khóa học lập trình (Python, Web, AI) cho trẻ em.
- Trả lời thân thiện, chuyên nghiệp, truyền cảm hứng.
- Nhấn mạnh vào lợi ích: phát triển tư duy logic, sáng tạo, và kỹ năng giải quyết vấn đề.
- Nếu được hỏi về lộ trình, hãy đưa ra gợi ý từ cơ bản (Python) đến nâng cao (Web/AI).
- KHÔNG gọi các tool truy vấn dữ liệu học sinh trong chế độ này."""

SYSTEM_PROMPT_ANALYST = """Bạn là trợ lý phân tích dữ liệu học viên thông minh.

Quy trình BẮt BUỘC (3 bước):
BƯỚC 1: Gọi analyze_intent(question=<câu_hỏi>)
BƯỚC 2: Gọi generate_query(intent=INTENT_RESULT, lesson_index=-1)
BƯỚC 3: Gọi query_json(student_name='{student_name}', path=PATH_RESULT)

QUY TẮC:
- PHẢI sử dụng đúng student_name='{student_name}'.
- TRUYỀN NGUYÊN XI PATH_RESULT vào path.
- Sau khi nhận kết quả, tổng hợp và trả lời người dùng bằng tiếng Việt."""


# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────
def agent_node(state: AgentState) -> AgentState:
    """Node chính: LLM quyết định nội dung phản hồi hoặc gọi tool."""
    mode = state.get("mode", "advisor")
    student_name = state.get("student_name", "unknown")
    
    if mode == "analyst":
        num_lessons = 0
        if isinstance(state["json_data"], list) and len(state["json_data"]) > 0:
            num_lessons = len(state["json_data"][0].get("lessons", []))
        
        formatted_prompt = SYSTEM_PROMPT_ANALYST.format(student_name=student_name)
        content = (
            f"{formatted_prompt}\n\n"
            f"Thông tin học học viên hiện tại: {student_name} ({num_lessons} bài học)."
        )
    else:
        # Chế độ tư vấn: Đưa dữ liệu khóa học vào context
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
    }

    for tool_call in last_message.tool_calls:
        fn_name = tool_call["name"]
        fn_args = tool_call["args"]
        tool_id = tool_call["id"]

        fn = tool_fn_map.get(fn_name)
        if fn:
            result = fn.invoke(fn_args)
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
# Helper: chạy agent
# ─────────────────────────────────────────────
def run_agent(question: str, mode: str, student_name: str = "", data: Any = None) -> str:
    graph = build_graph()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "json_data": data if data else {},
        "student_name": student_name,
        "mode": mode,
        "intent": "",
        "query": "",
        "query_result": None,
    }

    final_state = graph.invoke(initial_state)
    last_msg = final_state["messages"][-1]
    return last_msg.content


# ─────────────────────────────────────────────
# Interactive CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import unicodedata
    import re

    def normalize_name(name: str) -> str:
        """Chuẩn hóa tên để so sánh."""
        n = name.strip().lower()
        n = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'\s+', '', n)

    print("\n" + "🌟" * 30)
    print("   VINCARE AI - TRỢ LÝ GIÁO DỤC THÔNG MINH")
    # CHỌN CHẾ ĐỘ
    print("\nChào mừng phụ huynh! Vui lòng chọn tính năng bạn cần:")
    print("1️⃣. Tư vấn khóa học (Lộ trình, học phí, nội dung...)")
    print("2️⃣. Tra cứu kết quả học tập của con (Cần tên học sinh)")
    
    selected_mode = ""
    while True:
        choice = input("\n👉 Nhập lựa chọn (1/2): ").strip()
        if choice == "1":
            selected_mode = "advisor"
            print("\n✅ Chế độ: TƯ VẤN KHÓA HỌC")
            break
        elif choice == "2":
            selected_mode = "analyst"
            print("\n✅ Chế độ: PHÂN TÍCH HỌC TẬP")
            break
        print("❌ Lựa chọn không hợp lệ, vui lòng nhập 1 hoặc 2.")

    student_input = ""
    student_data = None

    # Load dữ liệu tương ứng
    if selected_mode == "advisor":
        try:
            # Tự động load file courses.json cho chế độ tư vấn
            from tools import DATA_DIR
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
            if not student_raw: continue
            
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

            # Gợi ý nếu chỉ có 1 kết quả gần đúng
            matches = [s for s in available_students if norm_input in normalize_name(s)]
            if len(matches) == 1:
                confirm = input(f"❓ Có phải bạn muốn tìm '{matches[0]}'? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    student_input = matches[0]
                    student_data = load_student_data(student_input)
                    break
            
            print(f"❌ Không tìm thấy. Thử lại hoặc gõ 'exit' để thoát.")
            if student_raw.lower() == 'exit': exit()

    print("\n💡 Chatbot đã sẵn sàng. Gõ 'exit' để dừng.")

    while True:
        prefix = "[Tư vấn]" if selected_mode == "advisor" else f"[{student_input}]"
        question = input(f"\n❓ {prefix}: ").strip()
        
        if question.lower() in ["exit", "quit", "thoát"]:
            print("👋 Tạm biệt phụ huynh!")
            break
        
        if not question: continue

        print("🤖 Bot đang suy nghĩ...")
        try:
            # Chạy agent và lấy state cuối cùng để xem token usage
            graph = build_graph()
            initial_state: AgentState = {
                "messages": [HumanMessage(content=question)],
                "json_data": student_data if student_data else {},
                "student_name": student_input,
                "mode": selected_mode,
                "intent": "",
                "query": "",
                "query_result": None,
            }
            final_state = graph.invoke(initial_state)
            answer = final_state["messages"][-1].content
            
            # Ghi log token usage bằng logger module mới
            log_token_usage(final_state["messages"][-1], selected_mode)
            
            print(f"🤖 Trả lời:\n{answer}")
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")