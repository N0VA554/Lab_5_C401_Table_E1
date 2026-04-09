import sys
import os

print("Đường dẫn Python hiện tại:", sys.executable)
try:
    import openai
    print("✅ Đã tìm thấy thư viện OpenAI phiên bản:", openai.__version__)
except ImportError:
    print("❌ Vẫn không tìm thấy thư viện OpenAI!")