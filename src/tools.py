"""
tools.py - Định nghĩa các tool và hàm load dữ liệu học viên từ thư mục data/
"""

import json
import os
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Any

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Cấu hình Logging
# ─────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "tools.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentTools")

# ─────────────────────────────────────────────
# Khởi tạo LLM dùng chung
# ─────────────────────────────────────────────
def get_llm(temperature: float = 0):
    """
    Khởi tạo LLM dựa trên biến DEFAULT_LLM trong .env.
    Hỗ trợ: 'gemini' (mặc định) và 'openai'.
    """
    model_provider = os.environ.get("DEFAULT_LLM", "gemini").lower()
    
    if model_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            temperature=temperature,
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            max_retries=10, # Thử lại tối đa 10 lần khi gặp lỗi 429
            timeout=60     # Chờ tối đa 60s cho mỗi yêu cầu
        )
    else:
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=os.environ.get("OPENAI_API_KEY"),
            max_retries=3
        )

# ─────────────────────────────────────────────
# Đường dẫn thư mục data
# ─────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"


# ─────────────────────────────────────────────
# Load dữ liệu từ folder data/
# ─────────────────────────────────────────────
def load_student_data(filename: str) -> dict[str, Any]:
    """
    Đọc file JSON học viên từ thư mục data/.
    Hỗ trợ chuẩn hóa tên để tìm kiếm linh hoạt.
    """
    import unicodedata
    import re

    def normalize(s: str) -> str:
        s = s.strip().lower()
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'\s+', '', s)

    target_norm = normalize(filename.replace(".json", ""))
    
    # Duyệt qua các file thực tế để tìm file khớp sau khi chuẩn hóa
    for file in DATA_DIR.glob("*.json"):
        if normalize(file.stem) == target_norm:
            with open(file, encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError(f"Không tìm thấy file dữ liệu cho: {filename}")


def list_available_students() -> list[str]:
    """
    Liệt kê tất cả file JSON học viên trong thư mục data/.
    Trả về danh sách tên file (không có đuôi .json).
    """
    if not DATA_DIR.exists():
        return []

    return [f.stem for f in DATA_DIR.glob("*.json")]


def load_all_students() -> dict[str, dict[str, Any]]:
    """
    Đọc toàn bộ file JSON học viên trong thư mục data/.
    Trả về dict { tên_học_viên: dữ liệu }.
    """
    result = {}
    for student_name in list_available_students():
        try:
            result[student_name] = load_student_data(student_name)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Bỏ qua '{student_name}': {e}")
    return result


# ─────────────────────────────────────────────
# Dữ liệu mặc định (load từ file thay vì hardcode)
# ─────────────────────────────────────────────
def get_default_data() -> dict[str, Any]:
    """
    Lấy dữ liệu mặc định: ưu tiên file đầu tiên trong data/, fallback sang dict rỗng.
    """
    students = list_available_students()
    if students:
        return load_student_data(students[0])
    return {}


# ─────────────────────────────────────────────
# Tools LangChain
# ─────────────────────────────────────────────
@tool
def analyze_intent(question: str) -> str:
    """
    Sử dụng LLM để phân tích ý định của câu hỏi người dùng.
    Trả về một trong các nhãn: 'knowledge', 'skill', 'product', 'behavior', 'overview'.
    """
    logger.info(f"--- [Tool: analyze_intent] Gọi LLM để phân tích: '{question}' ---")
    
    # Thêm độ trễ ngắn để tránh spam API liên tục (giới hạn 5 RPM của gói Free)
    time.sleep(1) 
    
    prompt = f"""Bạn là một chuyên gia phân loại ý định. Hãy phân tích câu hỏi sau đây về dữ liệu học viên và trả về duy nhất MỘT từ khóa đại diện cho ý định.

Câu hỏi: "{question}"

Các nhãn ý định có sẵn:
- 'knowledge': Câu hỏi về kiến thức đã học, bài tập về nhà, lý thuyết.
- 'skill': Câu hỏi về kỹ năng mềm, giao tiếp, hợp tác, sáng tạo, tư duy.
- 'product': Câu hỏi về sản phẩm dự án, thiết kế, hoàn thiện dự án.
- 'behavior': Câu hỏi về thái độ, hành vi, chuyên cần, tập trung.
- 'overview': Câu hỏi chung, nhận xét tổng quát, hoặc không thuộc các loại trên.

YÊU CẦU: Chỉ trả về duy nhất từ khóa (label), không có văn bản giải thích nào khác."""

    try:
        llm = get_llm(temperature=0)
        response = llm.invoke(prompt)
        result = response.content.strip().lower()
        
        # Đảm bảo kết quả thuộc danh sách nhãn hợp lệ
        valid_intents = ["knowledge", "skill", "product", "behavior", "overview"]
        if result not in valid_intents:
            # Tìm xem có chứa từ khóa nào không (fallback)
            for v in valid_intents:
                if v in result:
                    result = v
                    break
            else:
                result = "overview"
    except Exception as e:
        logger.error(f"   => Lỗi khi gọi LLM cho analyze_intent: {e}")
        result = "overview"

    logger.info(f"   => Ý định xác định (bởi LLM): '{result}'")
    return result


@tool
def generate_query(intent: str = "overview", detail: str = "", lesson_index: int = -1) -> str:
    """
    Sinh ra truy vấn dựa trên ý định.
    - intent: kết quả từ analyze_intent
    - detail: tiêu chí cụ thể nếu cần
    - lesson_index: chỉ số bài học (-1 = bài mới nhất, 0 = bài đầu)
    
    Trả về chuỗi path theo định dạng mới hỗ trợ criteria_table:
    - 'index|Group|Criteria'
    - 'index|overview' (lấy toàn bộ bài học)
    """
    logger.info(f"--- [Tool: generate_query] Intent='{intent}', Detail='{detail}', Index={lesson_index} ---")
    intent = intent.lower().strip()

    group_map = {
        "knowledge": "Kiến thức",
        "skill": "Kĩ Năng",
        "product": "Sản phẩm",
        "behavior": "Thái độ học tập",
        "overview": "overview",
    }
    group = group_map.get(intent, "overview")

    if group == "overview":
        return f"{lesson_index}|overview"

    criteria = ""
    if detail:
        criteria_keywords = {
            "bài tập": "Bài tập về nhà", 
            "kiến thức cũ": "Kiến thức cũ", 
            "kiến thức mới": "Kiến thức mới",
            "phản biện": "Tư duy phản biện (Critical Thinking)", 
            "hợp tác": "Hợp tác nhóm (Collaboration)", 
            "sáng tạo": "Sáng tạo (Creativity)", 
            "chia sẻ": "Chia sẻ ý tưởng (Communication)",
            "ý tưởng": "Ý tưởng dự án/sản phẩm", 
            "vận dụng": "Kiến thức", 
            "hoàn thiện": "Tính hoàn thiện", 
            "thiết kế": "Thiết kế",
            "đúng giờ": "Đúng giờ", 
            "tập trung": "Mức độ tập trung", 
            "tham gia": "Tham gia hoạt động", 
            "thái độ": "Thái độ",
        }
        detail_lower = detail.lower()
        for kw, full_name in criteria_keywords.items():
            if kw in detail_lower:
                criteria = full_name
                break

    final_path = f"{lesson_index}|{group}|{criteria}".strip("|")
    logger.info(f"   => Path sinh ra: '{final_path}'")
    return final_path


@tool
def query_json(student_name: str, path: str) -> str:
    """
    Truy vấn dữ liệu học viên hỗ trợ format criteria_table.
    - student_name: tên học viên
    - path: định dạng 'index|Group|Criteria' hoặc 'index|overview'
    """
    logger.info(f"--- [Tool: query_json] Học viên: '{student_name}', Path: '{path}' ---")
    
    try:
        data = load_student_data(student_name)
    except Exception as e:
        return f"Lỗi không thể truy cập dữ liệu của {student_name}: {e}"

    # Dữ liệu portolio là một list (thường là 1 phần tử chứa thông tin học viên)
    if isinstance(data, list) and len(data) > 0:
        student_record = data[0]
    else:
        return "Dữ liệu không đúng định dạng portfolio (cần là mảng chứa danh sách bài học)."

    parts = path.split("|")
    try:
        lesson_idx = int(parts[0])
        lessons = student_record.get("lessons", [])
        if lesson_idx < 0:
            lesson_idx = len(lessons) + lesson_idx
        
        if not (0 <= lesson_idx < len(lessons)):
            return f"Không tìm thấy buổi học số {lesson_idx + 1}."
        
        target_lesson = lessons[lesson_idx]
    except (ValueError, IndexError):
        return f"Lỗi chỉ số buổi học: {parts[0]}"

    # Trường hợp overview: Trả về thông tiêu đề buổi học và toàn bộ bảng tiêu chí
    if len(parts) == 2 and parts[1] == "overview":
        return json.dumps({
            "title": target_lesson.get("title"),
            "objective": target_lesson.get("objective"),
            "evaluation": target_lesson.get("criteria_table")
        }, ensure_ascii=False, indent=2)

    # Trường hợp truy vấn sâu vào Group/Criteria
    group_name = parts[1]
    target_criteria = parts[2] if len(parts) > 2 else ""

    criteria_table = target_lesson.get("criteria_table", [])
    
    # Lọc theo Group
    group_results = [item for item in criteria_table if item.get("group") == group_name]
    
    if not group_results:
        # Fallback: Nếu không tìm thấy group chính xác, thử tìm gần đúng
        group_results = [item for item in criteria_table if group_name.lower() in item.get("group", "").lower()]

    if not group_results:
        return f"Không tìm thấy thông tin nhóm '{group_name}'."

    # Lọc theo Criteria nếu có
    if target_criteria:
        for item in group_results:
            if target_criteria.lower() in item.get("criteria", "").lower():
                return json.dumps(item, ensure_ascii=False, indent=2)
        
        # Nếu không tìm thấy tiêu chí cụ thể, trả về cả nhóm
        return json.dumps(group_results, ensure_ascii=False, indent=2)

    return json.dumps(group_results, ensure_ascii=False, indent=2)


# Danh sách tool để export
ALL_TOOLS = [analyze_intent, generate_query, query_json]
