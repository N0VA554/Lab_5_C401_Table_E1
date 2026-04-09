# Prototype 

## Mô tả
AI chatbot hỗ trợ cho phụ huynh nắm được tình hình học tập của con và tư vấn khóa học cho nền tảng Teki

## Level: Sketch prototype
UI build bằng Claude Artifacts (HTML/CSS/JS)
- 1 flow chính chạy thật với OpenAI API: nhập câu hỏi về buổi học của cháu -> nhận được kết quả và phân tích

## Links
Video demo:
https://drive.google.com/drive/folders/1XbR6JeQEhpZOUg-TiJDXxChEt7kcHexE?fbclid=IwY2xjawRDU3BleHRuA2FlbQIxMABicmlkETF0UUd0UGxSVXVDd2pkeGkxc3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHvDoyNaJkSrV_kwR7zrhmPuulmLNCyANqHugDB_bLJ9P1C_dFmJun7Ep_Zrt_aem_vqcSHT3MVgWILhJhul0B_w

## Tools và API đã dùng: 
UI: Claude AI để tạo giao diện
AI: Google Gemini 2.5 Flash (via Google AI Studio)

## Phân công
| Thành viên | Phần | Output |
|-----------|------|--------|
| An | course, readme prototype | course.json, readme.md |
| Hào | Làm agent analysis, failure mode |  agent.py, logger.py |
| Hải | tìm data, build tool tính điểm, demo_slide | scoring.py, demo/slides.pdf |
| Mạnh | build agent advised, build UI, merge, chạy demo | app.py, tools.py, dashboard.py |
| Cường | spec-draf final, data hoc sinh a | hocsinhA.json, NguyenDucManh.json |







