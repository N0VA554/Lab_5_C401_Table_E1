# Individual Reflection — Lê Ngọc Hải (2A202600380)

## 1. Role
Data engineer + Backend developer. Phụ trách tìm kiếm dữ liệu, xây dựng hệ thống chấm điểm và phát triển công cụ hỗ trợ demo.

## 2. Đóng góp cụ thể
- **Data Collection**: Tìm và chuẩn bị dataset gồm 50+ student records từ multiple sources, đảm bảo format JSON được chuẩn hóa
- **Scoring System Development**: Xây dựng file `rubric.json` với 15+ criteria, mapping giữa performance levels và điểm số
- **Scoring Tool (`score.py`)**: Viết tool tính điểm tự động dựa trên rubric, tích hợp logic validation để kiểm tra data integrity
- **Demo Tool (`demo_slide.py`)**: Phát triển script tạo slide presentation động để demo kết quả chatbot, visualize skill progression
- **Data Pipeline**: Thiết kế ETL process để transform raw student data thành format tương thích với chatbot

## 3. SPEC mạnh/yếu
- **Mạnh nhất**: Rubric design — tạo được rubric flexible với multiple dimensions (technical, soft skills, engagement) thay vì flat criteria. Điều này cho phép chatbot gợi ý khóa học personalized dựa vào từng khía cạnh.
- **Mạnh thứ 2**: Data validation logic trong `score.py` — catch được edge cases như missing fields, invalid score ranges, duplicate student IDs trước khi process.
- **Yếu nhất**: Data sources — 50 records chủ yếu là sample data, không hoàn toàn real student data. Nếu có thật 500+ records thì scoring distribution sẽ realistic hơn, không bị skewed.
- **Yếu thứ 2**: Demo slide flexibility — `demo_slide.py` hiện gen được 5 slide cố định, khó customize nếu stakeholder muốn thêm custom visualization.

## 4. Đóng góp khác
- Tối ưu performance của scoring tool từ O(n²) xuống O(n) bằng cách dùng dictionary lookup thay vì nested loop
- Document lại data schema cho team, viết README trong data/ folder giải thích từng field
- Giúp QA validate output của score.py bằng cách export test cases vào CSV format
- Phối hợp với UX designer để finalize rubric — tránh rubric quá phức tạp mà chatbot khó interpret

## 5. Điều học được
Trước hackathon, tưởng data engineering chỉ cần "load data + transform". Sau khi làm, thấy data quality có impact vô cùng lớn đến model output.

Cụ thể: lúc đầu data không consistent (một số record có academic_score, số khác không), khi chạy score.py ra kết quả lệch 15%. Sau khi normalize data, accuracy tăng lên 95%.

Bài học: garbage in = garbage out. Nên invest 30% time vào data cleaning thay vì 10%, vì 1 giờ clean data tốt = tiết kiệm 3 giờ debug sau.

Thêm 1 insight: rubric không phải chỉ technical tool, nó là **business rule codified**. Phải hiểu business logic (VD: tại sao soft skills được weight 30% chứ không phải 20%) để rubric align với company goal.

## 6. Nếu làm lại
- Sẽ kiếm real student data từ ngày đầu (có thể request từ Teky sample data) thay vì dùng mock data. May mắn là sau 2 ngày nhóm vẫn kịp thay.
- Sẽ viết unit test cho score.py sooner — ngày D5 tối mới setup test, khi đó bug khó sửa vì integration test fail. Nếu test sớm từ D3 thì catch bug ngay khi viết code.
- Sẽ design rubric tổng quát hơn để dễ mở rộng — hiện rubric cứng cho Teky. Nếu generic hơn thì có thể reuse cho other education clients.

## 7. AI giúp gì / AI sai gì
- **Giúp rất nhiều**: Dùng ChatGPT để tạo sample student data — prompt 1 lần ra 50 realistic record với distribution hợp lý. Tiết kiệm 3-4 tiếng manual entry.
- **Giúp**: Claude để design scoring algorithm logic — nó gợi ý weighted average approach dễ hiểu hơn custom heuristic tôi đang định code.
- **Giúp**: GitHub Copilot auto-complete score.py — code được viết nhanh hơn 40% nhờ suggestion từ Copilot.
- **Sai/Mislead**: ChatGPT gợi ý dùng pandas DataFrame cho all data processing — nghe pro nhưng add dependency không cần thiết. Suýt bloat project size nếu không revert. Bài học: trước accept suggestion, cân nhắc scope.
- **Sai**: Claude đề xuất statistical test để validate rubric consistency — nghe khoa học nhưng tool không có scipy library để chạy. Tốn time debug khi execute.

## 8. Metrics / Evidence
- ✅ Data: 50+ records, 100% validation pass rate
- ✅ Score tool: process 50 records trung bình 0.8 second (O(n) complexity verified)
- ✅ Rubric: 15 criteria, 5 proficiency levels, weights sum = 100%
- ✅ Demo tool: gen 5-slide presentation trong 2 second, output `output.pptx` ready for demo
- ✅ Test: 12/12 test case pass (validation logic, calculation accuracy, edge cases)

---

**Self-rating: 8/10**
- Technical execution: 9/10 (code quality, performance acceptable)
- Collaboration: 8/10 (communicated dataset schema, but could have synced rubric earlier with UX team)
- Problem-solving: 7/10 (fixed data quality issue but should have caught earlier)
- Learning: 8/10 (gained insight about data being business logic, not just engineering)
