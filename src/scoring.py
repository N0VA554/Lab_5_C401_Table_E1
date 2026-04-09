"""
scoring.py - Engine tính điểm học viên dựa trên rubric (hệ 4)
Adapt từ Lab_5_C401_Table_E1/student_scoring_tool.py cho portfolio data format.
"""

import json
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).parent / "data"
RUBRIC_PATH = DATA_DIR / "rubric.json"

# Load rubric một lần
with open(RUBRIC_PATH, "r", encoding="utf-8") as f:
    RUBRIC = json.load(f)

# Mapping từ tên group tiếng Việt trong portfolio → key trong rubric
GROUP_MAP = {
    "Kiến thức": "Knowledge",
    "Kĩ Năng": "Skill",
    "Sản phẩm": "Product",
    "Thái độ học tập": "Behavior",
}

# Mapping (group_vn, criteria_name) → (rubric_category, rubric_key)
# Dùng tuple (group, criteria) để tránh nhầm lẫn giữa các criteria cùng tên ở nhóm khác nhau
CRITERIA_TO_RUBRIC = {
    # Knowledge
    ("Kiến thức", "Bài tập về nhà"): ("Knowledge", "bai_tap_ve_nha"),
    ("Kiến thức", "Kiến thức cũ"): ("Knowledge", "kien_thuc_cu"),
    ("Kiến thức", "Kiến thức mới"): ("Knowledge", "kien_thuc_moi"),
    # Skill (4C)
    ("Kĩ Năng", "Tư duy phản biện (Critical Thinking)"): ("Skill", "tu_duy_phan_bien"),
    ("Kĩ Năng", "Hợp tác nhóm (Collaboration)"): ("Skill", "hop_tac"),
    ("Kĩ Năng", "Sáng tạo (Creativity)"): ("Skill", "sang_tao"),
    ("Kĩ Năng", "Chia sẻ ý tưởng (Communication)"): ("Skill", "giao_tiep"),
    # Product
    ("Sản phẩm", "Ý tưởng dự án/sản phẩm"): ("Product", "y_tuong"),
    ("Sản phẩm", "Kiến thức"): ("Product", "van_dung_kien_thuc"),
    ("Sản phẩm", "Tính hoàn thiện"): ("Product", "tinh_hoan_thien"),
    ("Sản phẩm", "Thiết kế"): ("Product", "thiet_ke"),
    # Behavior
    ("Thái độ học tập", "Đúng giờ"): ("Behavior", "dung_gio"),
    ("Thái độ học tập", "Mức độ tập trung"): ("Behavior", "tap_trung"),
    ("Thái độ học tập", "Tham gia hoạt động"): ("Behavior", "tham_gia"),
    ("Thái độ học tập", "Thái độ"): ("Behavior", "thai_do"),
}


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def _score_from_rubric(category: str, rubric_key: str, comment: str) -> float:
    """Tìm điểm (hệ 100) bằng cách so sánh comment với rubric levels."""
    rubric_cat = RUBRIC.get(category, {})
    rubric_item = rubric_cat.get(rubric_key)
    if not rubric_item or "levels" not in rubric_item:
        return 50.0  # default

    best = max(rubric_item["levels"], key=lambda l: _similarity(comment, l["comment"]))
    return best["score"]


def _score_to_4(score_100: float) -> float:
    """Chuyển điểm hệ 100 sang hệ 4."""
    return round(score_100 / 25, 2)


def score_single_criteria(group_vn: str, criteria_name: str, comment: str) -> float:
    """Tính điểm hệ 4 cho một tiêu chí cụ thể."""
    # Lookup bằng (group, criteria) tuple
    mapping = CRITERIA_TO_RUBRIC.get((group_vn, criteria_name))

    if not mapping:
        # Fallback: tìm gần đúng theo criteria name
        best_sim = 0
        for (g, c), (cat, rkey) in CRITERIA_TO_RUBRIC.items():
            if g == group_vn:
                sim = _similarity(criteria_name, c)
                if sim > best_sim:
                    best_sim = sim
                    mapping = (cat, rkey)
        if not mapping or best_sim < 0.5:
            return 2.0  # default trung bình

    category, rubric_key = mapping
    score_100 = _score_from_rubric(category, rubric_key, comment)
    return _score_to_4(score_100)


def compute_lesson_scores(lesson: dict) -> dict:
    """
    Tính điểm cho một buổi học.
    Returns: {
        "lesson_number": int,
        "title": str,
        "categories": {
            "Kiến thức": {"avg": float, "details": [...]},
            "Kĩ Năng": {"avg": float, "details": [...]},
            ...
        },
        "4c": {
            "Critical Thinking": float,
            "Collaboration": float,
            "Creativity": float,
            "Communication": float,
        }
    }
    """
    criteria_table = lesson.get("criteria_table", [])
    categories = {}
    c4_scores = {}

    c4_map = {
        "Tư duy phản biện (Critical Thinking)": "Critical Thinking",
        "Hợp tác nhóm (Collaboration)": "Collaboration",
        "Sáng tạo (Creativity)": "Creativity",
        "Chia sẻ ý tưởng (Communication)": "Communication",
    }

    for item in criteria_table:
        group = item.get("group", "")
        criteria = item.get("criteria", "")
        comment = item.get("comment", "")

        score = score_single_criteria(group, criteria, comment)

        # Group vào categories
        if group not in categories:
            categories[group] = {"total": 0, "count": 0, "details": []}
        categories[group]["total"] += score
        categories[group]["count"] += 1
        categories[group]["details"].append({
            "criteria": criteria,
            "comment": comment,
            "score": score,
        })

        # 4C scores
        if criteria in c4_map:
            c4_scores[c4_map[criteria]] = score

    # Tính trung bình
    for cat in categories.values():
        cat["avg"] = round(cat["total"] / cat["count"], 2) if cat["count"] > 0 else 0
        del cat["total"]
        del cat["count"]

    return {
        "lesson_number": lesson.get("lesson_number", 0),
        "title": lesson.get("title", ""),
        "categories": categories,
        "4c": c4_scores,
    }


def compute_course_average(student_data: list) -> dict:
    """
    Tính điểm trung bình TOÀN KHÓA (tất cả buổi học) cho một học sinh.
    Khác với compute_all_scores() - hàm này tổng hợp qua tất cả buổi, không chỉ buổi cuối.
    Input: student_data (list từ JSON portfolio)
    Returns: {
        "student": {...},
        "total_lessons": int,
        "4c_avg": {"Critical Thinking": float, ...},       # Trung bình cả khóa
        "category_avg": {"Kiến thức": float, ...},         # Trung bình cả khóa
        "4c_per_lesson": [{"lesson": int, "title": str, "scores": {...}}, ...],
        "category_per_lesson": [{"lesson": int, "title": str, "scores": {...}}, ...],
    }
    """
    if not student_data or not isinstance(student_data, list):
        return {"error": "Dữ liệu không hợp lệ"}

    lessons = []
    student_info = {}
    for record in student_data:
        if not student_info and "student" in record:
            student_info = record["student"]
        lessons.extend(record.get("lessons", []))

    lesson_scores = [compute_lesson_scores(l) for l in lessons]
    if not lesson_scores:
        return {"error": "Không có buổi học nào"}

    # --- Tính trung bình 4C toàn khóa ---
    c4_keys = ["Critical Thinking", "Collaboration", "Creativity", "Communication"]
    c4_totals = {k: 0.0 for k in c4_keys}
    c4_counts  = {k: 0   for k in c4_keys}

    for ls in lesson_scores:
        for k, v in ls["4c"].items():
            if k in c4_totals:
                c4_totals[k] += v
                c4_counts[k] += 1

    c4_avg = {
        k: round(c4_totals[k] / c4_counts[k], 2) if c4_counts[k] > 0 else 0.0
        for k in c4_keys
    }

    # --- Tính trung bình 4 nhóm toàn khóa ---
    cat_totals: dict = {}
    cat_counts: dict = {}

    for ls in lesson_scores:
        for cat, data in ls["categories"].items():
            cat_totals.setdefault(cat, 0.0)
            cat_counts.setdefault(cat, 0)
            cat_totals[cat] += data["avg"]
            cat_counts[cat] += 1

    category_avg = {
        cat: round(cat_totals[cat] / cat_counts[cat], 2) if cat_counts[cat] > 0 else 0.0
        for cat in cat_totals
    }

    # --- Per-lesson detail (for charts) ---
    c4_per_lesson = [
        {"lesson": ls["lesson_number"], "title": ls["title"], "scores": ls["4c"]}
        for ls in lesson_scores
    ]
    category_per_lesson = [
        {
            "lesson": ls["lesson_number"],
            "title": ls["title"],
            "scores": {cat: data["avg"] for cat, data in ls["categories"].items()},
        }
        for ls in lesson_scores
    ]

    return {
        "student": student_info,
        "total_lessons": len(lessons),
        "4c_avg": c4_avg,
        "category_avg": category_avg,
        "4c_per_lesson": c4_per_lesson,
        "category_per_lesson": category_per_lesson,
    }


def compute_all_scores(student_data: list) -> dict:
    """
    Tính điểm toàn bộ cho một học sinh.
    Input: student_data (list từ JSON portfolio)
    Returns: {
        "student": {"name": ..., "course": ..., "module": ...},
        "lessons": [compute_lesson_scores(lesson) for each lesson],
        "summary": {
            "4c_latest": {...},
            "4c_progress": [{lesson: ..., scores: {...}}, ...],
            "category_latest": {...},
            "category_progress": [{lesson: ..., scores: {...}}, ...],
            "total_lessons": int,
        }
    }
    """
    if not student_data or not isinstance(student_data, list):
        return {"error": "Dữ liệu không hợp lệ"}

    lessons = []
    student_info = {}
    for record in student_data:
        if not student_info and "student" in record:
            student_info = record["student"]
        lessons.extend(record.get("lessons", []))

    lesson_scores = [compute_lesson_scores(l) for l in lessons]

    # 4C progress qua các buổi
    c4_progress = []
    for ls in lesson_scores:
        c4_progress.append({
            "lesson": ls["lesson_number"],
            "title": ls["title"],
            "scores": ls["4c"],
        })

    # Category progress
    cat_progress = []
    for ls in lesson_scores:
        cat_avg = {cat: data["avg"] for cat, data in ls["categories"].items()}
        cat_progress.append({
            "lesson": ls["lesson_number"],
            "title": ls["title"],
            "scores": cat_avg,
        })

    # Latest scores
    latest = lesson_scores[-1] if lesson_scores else {}

    return {
        "student": student_info,
        "lessons": lesson_scores,
        "summary": {
            "4c_latest": latest.get("4c", {}),
            "4c_progress": c4_progress,
            "category_latest": {
                cat: data["avg"] for cat, data in latest.get("categories", {}).items()
            },
            "category_progress": cat_progress,
            "total_lessons": len(lessons),
        },
    }
