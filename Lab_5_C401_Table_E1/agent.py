import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from student_scoring_tool import EvaluationTool

# 1. Khởi tạo môi trường
# Load .env từ thư mục hiện tại
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Đọc System Prompt từ file .txt
def load_system_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 3. Khởi tạo Tool
tool_instance = EvaluationTool(
    rubric_path=os.getenv("RUBRIC_FILE_PATH"),
    students_dir=os.getenv("STUDENTS_DATA_DIR")
)

def ask_for_student_data(user_query):
    """
    Bước 1: Hỏi AI xem có cần lấy dữ liệu học sinh không
    """
    system_instruction = load_system_prompt("system_prompt.txt")
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_query}
    ]

    # Yêu cầu AI phân tích và trả lời
    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME", "gpt-4o"),
        messages=messages
    )

    response_text = response.choices[0].message.content
    
    # Kiểm tra xem có cần dữ liệu hay không
    if any(keyword in response_text.lower() for keyword in ["tên", "học sinh", "em nào", "ai"]):
        return None, response_text  # AI yêu cầu tên học sinh
    
    return "no_data_needed", response_text

def run_agent_with_student(user_query, student_name):
    """
    Bước 2: Lấy dữ liệu điểm của học sinh và trả về JSON
    """
    result = tool_instance.get_student_evaluation(student_name)
    return result

if __name__ == "__main__":
    # Nhập tên học sinh
    student_name = input("Nhập tên học sinh: ")
    
    # Lấy dữ liệu điểm
    result = run_agent_with_student("", student_name)
    
    # Output JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Lưu vào file
    if result.get("status") == "success":
        output_file = f"INDIVIDUAL_REPORT/{student_name}_scores.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Đã lưu vào: {output_file}")