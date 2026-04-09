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

    if not isinstance(data, list) or not data:
        return "Dữ liệu không đúng định dạng portfolio (cần là mảng chứa danh sách bài học)."

    lessons = []
    for record in data:
        lessons.extend(record.get("lessons", []))

    parts = path.split("|")
    try:
        lesson_idx = int(parts[0])
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


@tool
def get_student_scores(student_name: str) -> str:
    """
    Tính điểm hệ 4 cho học viên dựa trên rubric.
    Trả về điểm 4C (Critical Thinking, Collaboration, Creativity, Communication)
    và điểm theo 4 nhóm (Kiến thức, Kĩ Năng, Sản phẩm, Thái độ) cho tất cả buổi học.
    """
    logger.info(f"--- [Tool: get_student_scores] Học viên: '{student_name}' ---")
    try:
        from scoring import compute_all_scores
        data = load_student_data(student_name)
        scores = compute_all_scores(data)
        if "error" in scores:
            return json.dumps(scores, ensure_ascii=False)
        # Trả về summary (không cần toàn bộ details cho LLM)
        return json.dumps({
            "student": scores["student"],
            "total_lessons": scores["summary"]["total_lessons"],
            "4c_latest": scores["summary"]["4c_latest"],
            "category_latest": scores["summary"]["category_latest"],
            "4c_progress": scores["summary"]["4c_progress"],
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"   => Lỗi get_student_scores: {e}")
        return f"Lỗi khi tính điểm cho {student_name}: {e}"


@tool
def answer_lesson_question(student_name: str, lesson_number: int, question: str) -> str:
    """
    Trả lời câu hỏi của phụ huynh về một buổi học cụ thể của con.
    - student_name: tên học viên
    - lesson_number: số thứ tự buổi học (1-indexed). Dùng -1 để lấy buổi mới nhất.
    - question: câu hỏi của phụ huynh về buổi học đó (bằng tiếng Việt)

    Trả về nhận xét tổng hợp thân thiện bằng tiếng Việt dựa trên đánh giá giáo viên.
    Ví dụ: 'Buổi 3 con học gì?', 'Buổi 5 con có tập trung không?', 'Bài tập về nhà buổi 2 ra sao?'
    """
    logger.info(
        f"--- [Tool: answer_lesson_question] Học viên: '{student_name}', "
        f"Buổi: {lesson_number}, Câu hỏi: '{question}' ---"
    )
    try:
        data = load_student_data(student_name)
    except Exception as e:
        return f"Lỗi không thể truy cập dữ liệu của {student_name}: {e}"

    if not isinstance(data, list) or not data:
        return "Dữ liệu không đúng định dạng."

    lessons = []
    for record in data:
        lessons.extend(record.get("lessons", []))

    if not lessons:
        return "Không tìm thấy dữ liệu buổi học."

    # Chuyển đổi lesson_number → index (1-indexed, -1 = mới nhất)
    if lesson_number == -1:
        target = lessons[-1]
    elif 1 <= lesson_number <= len(lessons):
        target = lessons[lesson_number - 1]
    else:
        return f"Không tìm thấy buổi học số {lesson_number}. Khóa học có {len(lessons)} buổi."

    title = target.get("title", f"Buổi {lesson_number}")
    objective = target.get("objective", "")
    criteria_table = target.get("criteria_table", [])

    # Tổng hợp nhận xét theo nhóm để đưa vào LLM
    criteria_summary_lines = []
    for item in criteria_table:
        grp = item.get("group", "")
        crit = item.get("criteria", "")
        comment = item.get("comment", "")
        criteria_summary_lines.append(f"  [{grp}] {crit}: {comment}")
    criteria_text = "\n".join(criteria_summary_lines)

    prompt = f"""Bạn là trợ lý chatbot của Teky - học viện lập trình cho trẻ em.

Phụ huynh đang hỏi về buổi học của con:
Câu hỏi: "{question}"

Dữ liệu buổi học:
Buổi học: {title}
Mục tiêu: {objective}

Nhận xét giáo viên:
{criteria_text}

Yêu cầu:
- Hãy trả lời câu hỏi của phụ huynh dựa trên dữ liệu buổi học trên.
- Dùng ngôn ngữ thân thiện, dễ hiểu, phù hợp với phụ huynh (không chuyên môn kỹ thuật).
- Nếu câu hỏi về nội dung học → tóm tắt mục tiêu và những gì con làm được.
- Nếu câu hỏi về thái độ/tập trung → dùng nhận xét Thái độ học tập.
- Nếu câu hỏi về kỹ năng → dùng nhận xét Kĩ Năng.
- Nếu câu hỏi về sản phẩm/dự án → dùng nhận xét Sản phẩm.
- Trả lời ngắn gọn, rõ ràng (3-6 câu). Trả lời bằng tiếng Việt."""

    time.sleep(0.5)
    try:
        llm = get_llm(temperature=0.3)
        response = llm.invoke(prompt)
        result = response.content.strip()
        logger.info(f"   => answer_lesson_question thành công cho {title}")
        return result
    except Exception as e:
        logger.error(f"   => Lỗi LLM trong answer_lesson_question: {e}")
        # Fallback: trả về raw data nếu LLM lỗi
        return json.dumps({
            "title": title,
            "objective": objective,
            "criteria": criteria_table,
        }, ensure_ascii=False, indent=2)


@tool
def get_course_summary_scores(student_name: str) -> str:
    """
    Tính và trả về điểm trung bình TOÀN KHÓA (tất cả buổi học) của học viên.
    Khác với get_student_scores (chỉ trả buổi mới nhất), tool này tính trung bình
    trên toàn bộ khóa học, giúp đánh giá tổng quát hơn.

    Dùng khi phụ huynh hỏi:
    - "Điểm trung bình cả khóa của con là bao nhiêu?"
    - "Con tiến bộ thế nào trong cả khóa học?"
    - "Nhìn chung con học được không?"
    """
    logger.info(f"--- [Tool: get_course_summary_scores] Học viên: '{student_name}' ---")
    try:
        from scoring import compute_course_average
        data = load_student_data(student_name)
        result = compute_course_average(data)
        if "error" in result:
            return json.dumps(result, ensure_ascii=False)
        # Trả về dữ liệu gọn cho LLM
        return json.dumps({
            "student": result["student"],
            "total_lessons": result["total_lessons"],
            "4c_avg_toan_khoa": result["4c_avg"],
            "category_avg_toan_khoa": result["category_avg"],
            "chi_tiet_tung_buoi_4c": result["4c_per_lesson"],
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"   => Lỗi get_course_summary_scores: {e}")
        return f"Lỗi khi tính điểm toàn khóa cho {student_name}: {e}"


# Danh sách tool để export
@tool
def get_lesson_group_comments(student_name: str, lesson_number: int, group: str) -> str:
    """
    Truy xuất toàn bộ nhận xét của giáo viên cho một nhóm tiêu chí cụ thể trong một buổi học.
    - lesson_number: số thứ tự buổi (1, 2, ... hoặc -1 cho buổi mới nhất).
    - group: tên nhóm (ví dụ: 'Kiến thức', 'Kĩ Năng', 'Sản phẩm', 'Thái độ học tập').
    """
    logger.info(f"--- [Tool: get_lesson_group_comments] Học viên: '{student_name}', Buổi: {lesson_number}, Nhóm: '{group}' ---")
    try:
        data = load_student_data(student_name)
    except Exception as e:
        return f"Lỗi truy cập dữ liệu: {e}"

    if not isinstance(data, list) or not data:
        return "Dữ liệu không hợp lệ."

    lessons = []
    for record in data:
        lessons.extend(record.get("lessons", []))

    if not lessons:
        return "Không có dữ liệu buổi học."

    if lesson_number == -1:
        target = lessons[-1]
    elif 1 <= lesson_number <= len(lessons):
        target = lessons[lesson_number - 1]
    else:
        return f"Không tìm thấy buổi {lesson_number}."

    criteria_table = target.get("criteria_table", [])
    results = [
        f"- {item.get('criteria')}: {item.get('comment')}"
        for item in criteria_table if item.get("group", "").lower() == group.lower()
    ]

    if not results:
        return f"Không có nhận xét nào trong nhóm '{group}' ở buổi {lesson_number}."
    
    return "\n".join(results)


@tool
def get_specific_criteria_comment(student_name: str, lesson_number: int, criteria: str) -> str:
    """
    Tìm và truy xuất chính xác nhận xét của giáo viên cho một tiêu chí cụ thể trong buổi học.
    - lesson_number: số thứ tự buổi (1, 2, ... hoặc -1 cho buổi mới nhất).
    - criteria: từ khóa tiêu chí (ví dụ: 'Bài tập về nhà', 'Tư duy phản biện', 'Tập trung').
    """
    logger.info(f"--- [Tool: get_specific_criteria_comment] Học viên: '{student_name}', Buổi: {lesson_number}, Tiêu chí: '{criteria}' ---")
    try:
        data = load_student_data(student_name)
    except Exception as e:
        return f"Lỗi truy cập dữ liệu: {e}"

    if not isinstance(data, list) or not data:
        return "Dữ liệu không hợp lệ."

    lessons = []
    for record in data:
        lessons.extend(record.get("lessons", []))

    if not lessons:
        return "Không có dữ liệu buổi học."

    if lesson_number == -1:
        target = lessons[-1]
    elif 1 <= lesson_number <= len(lessons):
        target = lessons[lesson_number - 1]
    else:
        return f"Không tìm thấy buổi {lesson_number}."

    criteria_table = target.get("criteria_table", [])
    # Tìm kiếm gần đúng (chứa từ khoá)
    for item in criteria_table:
        if criteria.lower() in item.get("criteria", "").lower():
            return f"[{item.get('group')}] {item.get('criteria')}: {item.get('comment')}"

    return f"Không tìm thấy tiêu chí nào có chứa từ '{criteria}' trong buổi {lesson_number}."


ALL_TOOLS = [
    analyze_intent,
    generate_query,
    query_json,
    get_student_scores,
    answer_lesson_question,
    get_course_summary_scores,
    get_lesson_group_comments,
    get_specific_criteria_comment,
]
