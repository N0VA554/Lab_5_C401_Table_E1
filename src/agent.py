"""
LangGraph Agent - Phân tích dữ liệu học viên từ JSON
Tools: analyze_intent → generate_query → query_json
Dữ liệu được load tự động từ thư mục data/
"""

import json
import os
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Import tools và data loader từ tools.py
# ─────────────────────────────────────────────
from tools import (
    ALL_TOOLS,
    analyze_intent,
    generate_query,
    query_json,
    get_default_data,
    load_student_data,
    list_available_students,
    get_llm,
)

load_dotenv()

# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    json_data: dict[str, Any]          # dữ liệu JSON gốc
    student_name: str                   # Tên học sinh đang truy vấn
    intent: str                         # ý định đã phân tích
    query: str                          # query path được generate
    query_result: Any                   # kết quả sau query


# ─────────────────────────────────────────────
# LLM + Tools binding
# ─────────────────────────────────────────────
llm = get_llm(temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là trợ lý phân tích dữ liệu học viên thông minh.

Quy trình BẮt BUỘC (3 bước):

BƯỚC 1: Gọi analyze_intent(question=<câu_hỏi>)
- Kết quả trả về: một trong ['knowledge','skill','product','behavior','overview']
- Đặt tên biến kết quả là INTENT_RESULT

BƯỚC 2: Gọi generate_query(intent=INTENT_RESULT, lesson_index=-1)
- PHẢI truyền INTENT_RESULT vào tham số intent (KHÔNG bỏ trống)
- Kết quả trả về: một chuỗi path, đặt tên là PATH_RESULT
- Định dạng PATH_RESULT mới: 'index|Group|Criteria'

BƯỚC 3: Gọi query_json(student_name='{student_name}', path=PATH_RESULT)
- PHẢI sử dụng đúng student_name='{student_name}' được cung cấp.
- TRUYỀN NGUYÊN XI PATH_RESULT vào path, KHÔNG SẮA ĐỔI, KHÔNG THÊM gì.
- Sau khi nhận kết quả, tổng hợp và trả lời người dùng bằng tiếng Việt."""


def agent_node(state: AgentState) -> AgentState:
    student_name = state.get("student_name", "unknown")
    num_lessons = 0
    if isinstance(state["json_data"], list) and len(state["json_data"]) > 0:
        num_lessons = len(state["json_data"][0].get("lessons", []))
    
    formatted_prompt = SYSTEM_PROMPT.format(student_name=student_name)
    
    system_msg = SystemMessage(
        content=(
            f"{formatted_prompt}\n\n"
            f"Thông tin hiện tại:\n"
            f"- Đang phân tích học viên: {student_name}\n"
            f"- Số lượng bài học: {num_lessons}\n"
        )
    )

    # Luôn đặt SystemMessage ở đầu
    messages = [system_msg] + state["messages"]

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: AgentState) -> AgentState:
    """Node thực thi tool calls."""
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
# Router: tiếp tục hay kết thúc?
# ─────────────────────────────────────────────
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# ─────────────────────────────────────────────
# Xây dựng Graph
# ─────────────────────────────────────────────
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
def run_agent(question: str, student_name: str, data: Any) -> str:
    """
    Chạy agent với câu hỏi, tên học sinh và dữ liệu đã load.
    """
    graph = build_graph()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "json_data": data,
        "student_name": student_name,
        "intent": "",
        "query": "",
        "query_result": None,
    }

    final_state = graph.invoke(initial_state)
    last_msg = final_state["messages"][-1]
    return last_msg.content


# ─────────────────────────────────────────────
# Demo Interactive CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("   VINCARE AI - TRỢ LÝ PHÂN TÍCH HỌC TẬP (INTERACTIVE)")
    print("=" * 60)

    # BƯỚC 1: Hỏi tên học sinh
    available_students = list_available_students()
    print(f"📂 Danh sách học sinh sẵn có: {available_students}")
    
    def normalize_name(name: str) -> str:
        """Chuẩn hóa tên để so sánh (không dấu, viết thường, xóa khoảng trắng thừa)."""
        import unicodedata
        import re
        n = name.strip().lower()
        n = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'\s+', '', n)

    student_input = ""
    target_student = ""
    while True:
        student_input = input("\n👉 Phụ huynh vui lòng nhập Tên Học Sinh để bắt đầu: ").strip()
        if not student_input: continue
        
        # 1. Thử tìm khớp hoàn toàn hoặc chuẩn hóa khớp
        norm_input = normalize_name(student_input)
        
        for s in available_students:
            if normalize_name(s) == norm_input or s.lower() == student_input.lower():
                target_student = s
                break
        
        if target_student: break

        # 2. Thử tìm kiếm gần đúng (chứa trong tên)
        matches = [s for s in available_students if norm_input in normalize_name(s)]
        if len(matches) == 1:
            confirm = input(f"❓ Có phải bạn muốn tìm học sinh '{matches[0]}'? (y/n): ").strip().lower()
            if confirm in ['y', 'yes', '']:
                target_student = matches[0]
                break
        elif len(matches) > 1:
            print(f"🤔 Tìm thấy nhiều kết quả: {matches}. Vui lòng nhập chính xác hơn.")
            continue

        print(f"❌ Không tìm thấy dữ liệu cho học sinh '{student_input}'.")
        print(f"💡 Gợi ý: {available_students}")

    # Load dữ liệu
    try:
        student_data = load_student_data(target_student)
        print(f"✅ Đã xác nhận học sinh: {target_student}")
        print("💡 Bạn có thể hỏi về kiến thức, kỹ năng, sản phẩm hoặc thái độ của con.")
        print("🚪 Gõ 'exit' hoặc 'quit' để kết thúc.")
    except Exception as e:
        print(f"❌ Lỗi khi load dữ liệu: {e}")
        exit(1)

    # BƯỚC 2: Vòng lặp hỏi đáp
    while True:
        question = input(f"\n❓ [Phụ huynh {target_student}]: ").strip()
        
        if question.lower() in ["exit", "quit", "thoát"]:
            print("👋 Tạm biệt phụ huynh!")
            break
        
        if not question:
            continue

        print("🤖 Bot đang suy nghĩ...")
        try:
            answer = run_agent(question, student_input, student_data)
            print(f"🤖 Trả lời:\n{answer}")
        except Exception as e:
            print(f"⚠️ Có lỗi xảy ra trong quá trình xử lý: {e}")
            print("Vui lòng thử hỏi lại câu khác.")