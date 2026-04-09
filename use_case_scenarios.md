# 3 Kịch bản Sử dụng Thực tế của TekyChatbot

Dưới đây là 3 kịch bản tương tác điển hình giúp Phụ huynh khai thác tối đa sức mạnh của hệ thống TekyChatbot, từ việc xem biểu đồ tổng quan đến tra cứu nhận xét chi tiết của giáo viên.

---

## 🚀 Kịch bản 1: Theo dõi sự tiến bộ tổng thể (Tổng kết khóa học)

**Bối cảnh:** Phụ huynh muốn biết sau 2 tháng học tập, con mình đang ở mức độ nào so với mục tiêu chung của khóa học, thay vì chỉ xem từng buổi lẻ tẻ.

*   **Hành động của Phụ huynh:**
    1. Truy cập vào Dashboard Analyst của con.
    2. Nhìn vào biểu đồ **"🎯 Tổng kết toàn khóa học"** ngay phía trên cùng.
    3. Quan sát biểu đồ **Radar 4C** để thấy điểm mạnh/yếu (Ví dụ: Con mạnh về *Giao tiếp* nhưng cần cải thiện *Sáng tạo*).
*   **Câu hỏi Chatbot:** "Sau 9 buổi vừa qua, cô đánh giá con mạnh nhất ở kỹ năng nào và cần tập trung thêm vào đâu?"
*   **Luồng xử lý của Bot:**
    *   Sử dụng tool `get_course_summary_scores` để lấy điểm trung bình 4C toàn khóa.
    *   LLM nhận thấy điểm *Communication* (3.89) cao nhất và *Creativity* (0.78) thấp nhất.
*   **Kết quả:** Bot trả lời: *"Dạ chào phụ huynh, dựa trên dữ liệu 9 buổi học, bé Mạnh đang thể hiện cực kỳ xuất sắc ở kỹ năng **Giao tiếp** (3.89/4). Tuy nhiên, về phần **Sáng tạo**, bé đang ở mức cần cố gắng (0.78/4). Ba mẹ nên khuyến khích bé thử nghiệm nhiều ý tưởng mới hơn trong các dự án tới nhé!"*

---

## 📝 Kịch bản 2: Tra cứu nội dung buổi học cụ thể (Hỏi đáp Buổi học)

**Bối cảnh:** Phụ huynh bận công tác nên không đi đón con buổi học hôm qua được, muốn biết con đã học những gì và giáo viên nhận xét ra sao.

*   **Hành động của Phụ huynh:** Mở khung chat và hỏi trực tiếp.
*   **Câu hỏi Chatbot:** "Buổi học mới nhất con học về chủ đề gì và thầy có khen con chỗ nào không?"
*   **Luồng xử lý của Bot:**
    *   Sử dụng tool `answer_lesson_question` với tham số `lesson_number=-1`.
    *   Tool này bốc toàn bộ bảng tiêu chí và mục tiêu của buổi cuối cùng về cho LLM tổng hợp.
*   **Kết quả:** Bot trả lời: *"Hôm qua bé học buổi 9 về chủ đề 'Lập trình Python cơ bản'. Thầy có lời khen đặc biệt về sự **Tập trung** của con (đạt điểm tối đa). Con đã hoàn thành 100% nhiệm vụ trên lớp và trình bày ý tưởng sản phẩm rất thuyết phục đó ạ!"*

---

## 🔍 Kịch bản 3: Đào sâu vào khía cạnh Thái độ & Kỹ năng (Truy xuất chi tiết)

**Bối cảnh:** Phụ huynh nhận thấy con dạo này hay dùng điện thoại, lo lắng con lên lớp có tập trung hay đi muộn không.

*   **Hành động của Phụ huynh:** Đặt câu hỏi cụ thể về hành vi.
*   **Câu hỏi Chatbot:** "Thái độ trong lớp của con 3 buổi gần đây có tốt không? Có hay đi muộn hay mất tập trung không?"
*   **Luồng xử lý của Bot:**
    *   Agent có thể gọi tool `get_lesson_group_comments` cho nhóm "Thái độ học tập" của 3 buổi gần nhất (buổi 7, 8, 9).
    *   Hoặc dùng tool `get_specific_criteria_comment` cho từ khóa "tập trung" và "đi muộn".
*   **Kết quả:** Bot trả lời: *"Dạ, em đã kiểm tra nhận xét 3 buổi gần nhất: Bé vẫn đi học rất đúng giờ và không gặp vấn đề về kỷ luật. Tuy nhiên, ở buổi 8, thầy có nhắc nhẹ là con đôi lúc còn bối rối khi áp dụng kiến thức mới nên cần tập trung nghe giảng kỹ hơn một chút. Hai buổi còn lại (7 và 9) con đều tương tác rất chủ động với thầy cô ạ."*

---

> [!TIP]
> **Điểm ưu việt:** Phụ huynh không cần phải đọc hàng chục file JSON hay bảng điểm phức tạp. Chatbot đóng vai trò như một **"Giáo viên chủ nhiệm ảo"** hiểu rõ mọi ngóc ngách dữ liệu để phản hồi bằng ngôn ngữ tự nhiên, ấm áp.
