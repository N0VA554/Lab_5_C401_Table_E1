# Individual reflection — Nguyễn Ngọc Cường (2A202600186)

## 1. Role
spec-draf final, data hoc sinh a. Phụ trách thiết kế AI Product Canvas, metrics,user story,failure mode và 3ROI.

## 2. Đóng góp cụ thể
- Thiết kế AI Product Canvas với tiêu chí nhóm người dùng là ai, pain point là gì và AI giải quyết ra sao
- Thiết kế các metrics cùng threshold và redflag chi tiết, cụ thể
- ROI 3 kịch bản sát với nhu cầu thực tế của bên mua và sử dụng chatbot

## 3. SPEC mạnh/yếu
- Mạnh nhất: AI Product Canvas: Lý do: Giải quyết trực tiếp nhu cầu, mong muốn của bậc pơhuj huynh ngay lập tức về tình hình con các học trong trung tâm thay vì mất nhiều thời gian hơn hỏi giáo viên và CSKH
- Yếu nhất: Top 3 failure modes: Nên cụ thể hóa con số hơn, cách xử lý khi gặp các failure modes và khắc phục sao cho hiệu quả, đặc biệt việc LLM Hallucination vẫn còn

## 4. Đóng góp khác
- Tao data test ở NguyenVanA.json
- Đề xuất cần xây dựng metric cụ thể, rõ ràng đẻ khiến người có định mua chatbot cho trung tâm có thể cảm nhận được chính xác độ hiệu quả thay vì thông số khô khăn 

## 5. Điều học được
Trước hackathon nghĩ precision và recall chỉ là metric kỹ thuật cao siêu, khó hiểu.
Sau khi thiết kế AI triage mới hiểu: chọn precision cao hơn cho việc phụ huynh muốn biết tình hình con cái mình học hành tiến độ ra sao (thông báo sai kết quả học tập) và có thể diễn giải theo cách thuận người dùng hơn (như tăng tốc thời gian cho tra cứu thông tin học tập còn khoảng 30s)

## 6. Nếu làm lại
Xây dựng failure modes cụ thể hơn, phương án giải quyết rạch ròi hơn

## 7. AI giúp gì / AI sai gì
- **Giúp:** dùng Gemini biết được Gemini đề xuất gợi ý không cần mô hình hoàn hảo, cần nên xử lý chính xác với phần User Stories — 4 paths, đặc biệt Failure và Correction
- **Sai/mislead:** Gemini gợi ý các thông số đo metric nhưng Gemini đưa ra quá nhiều lựa chọn, cần lọc bỏ các metric không cần thiết