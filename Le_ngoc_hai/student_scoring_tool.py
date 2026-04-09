import json
import os
from difflib import SequenceMatcher

class EvaluationTool:
    def __init__(self, rubric_path, students_dir):
        self.rubric_path = rubric_path
        self.students_dir = students_dir
        with open(rubric_path, 'r', encoding='utf-8-sig') as f:
            self.rubric = json.load(f)

    def _get_similarity(self, a, b):
        return SequenceMatcher(None, str(a).strip().lower(), str(b).strip().lower()).ratio()

    def _get_score_from_comment(self, category, title, student_comment):
        """Lấy điểm hệ 100 từ comment bằng so sánh với rubric levels"""
        rubric_cat = self.rubric.get(category, {})
        rubric_item = next((r for r in rubric_cat.values() if r['title'].lower() == title.lower()), None)
        
        if rubric_item and 'levels' in rubric_item:
            best_match = max(rubric_item['levels'], key=lambda l: self._get_similarity(student_comment, l['comment']))
            return best_match['score']
        return 50  # Default

    def get_student_evaluation(self, student_name):
        """Lấy dữ liệu điểm hệ 4 của học sinh"""
        search_name = student_name.lower().replace(" ", "_")
        all_files = os.listdir(self.students_dir)
        target_file = next((f for f in all_files if search_name in f.lower() and f.endswith('.json')), None)

        if not target_file:
            return {"status": "error", "message": f"Không tìm thấy học sinh {student_name}"}

        with open(os.path.join(self.students_dir, target_file), 'r', encoding='utf-8-sig') as f:
            student_data = json.load(f)

        # Tính điểm hệ 4 cho tất cả tiêu chí
        scores = {
            "info": {
                "name": student_name,
                "course": student_data.get("course"),
                "lesson": student_data.get("lesson")
            },
            "Knowledge": {},
            "Skill": {},
            "Product": {},
            "Behavior": {}
        }

        for category in ["Knowledge", "Skill", "Product", "Behavior"]:
            if category in student_data:
                for criterion_key, criterion_data in student_data[category].items():
                    title = criterion_data.get("title", "")
                    comment = criterion_data.get("comment", "")
                    
                    # Lấy điểm hệ 100
                    score_100 = self._get_score_from_comment(category, title, comment)
                    # Quy đổi sang hệ 4
                    score_4 = round(score_100 / 25, 2)
                    
                    scores[category][title] = score_4

        return {"status": "success", "data": scores}