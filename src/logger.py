import datetime
import json
from pathlib import Path
from typing import Any

# Đường dẫn thư mục log (lấy từ vị trí file này)
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
TOKEN_LOG_FILE = LOG_DIR / "token_usage.log"

def log_token_usage(ai_message: Any, mode: str):
    """
    Trích xuất thông tin token từ AI message và ghi vào file log.
    Hỗ trợ cả định dạng của OpenAI và Google Gemini thông qua LangChain.
    """
    try:
        # 1. Trích xuất metadata sử dụng
        usage = getattr(ai_message, "usage_metadata", None)
        
        # Fallback 1: Trích xuất từ response_metadata (dành cho OpenAI và một số provider khác)
        if not usage and hasattr(ai_message, "response_metadata"):
            usage = ai_message.response_metadata.get("token_usage")

        if not usage:
            return

        # 2. Chuẩn hóa Key (Hỗ trợ cả Gemini và OpenAI định dạng LangChain)
        # Gemini dùng: input_tokens, output_tokens
        # OpenAI dùng: prompt_tokens, completion_tokens
        prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        total_tokens = usage.get("total_tokens") or (prompt_tokens + completion_tokens)

        # 3. Chuẩn bị dữ liệu ghi log
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] Mode: {mode:8} | "
            f"Prompt: {prompt_tokens:5} | "
            f"Completion: {completion_tokens:5} | "
            f"Total: {total_tokens:5}\n"
        )

        # 3. Ghi vào file
        with open(TOKEN_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

    except Exception as e:
        # Đảm bảo việc ghi log không làm crash ứng dụng chính
        print(f"⚠️ Warning: Coud không thể ghi log token: {e}")
