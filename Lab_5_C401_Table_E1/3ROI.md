## **1\. Kịch bản "Đánh giá sự trưởng thành" (Cái nhìn tổng thể)**

* **Mục đích:** Cung cấp bức tranh toàn cảnh về sự thay đổi của con sau một lộ trình dài, giúp phụ huynh thấy rõ các điểm mạnh và điểm yếu cốt lõi.  
* **Cách thức:** Kết hợp giữa trực quan hóa dữ liệu (**Biểu đồ Radar**) và sự phân tích của AI. Phụ huynh có thể đặt câu hỏi về các kỹ năng mềm (4C \- Tư duy phản biện, Sáng tạo, Cộng tác, Giao tiếp).  
* **Câu hỏi gợi ý:** *"Sau lộ trình 9 buổi vừa qua, cô đánh giá con mạnh nhất ở kỹ năng nào và cần cải thiện gì thêm?"*

## **2\. Kịch bản "Bám sát buổi học mới nhất" (Cập nhật tức thì)**

* **Mục đích:** Giải pháp tối ưu cho những phụ huynh bận rộn, cần nắm bắt nhanh nội dung và kết quả ngay sau mỗi buổi học.  
* **Cách thức:** Chatbot sử dụng công cụ `answer_lesson_question` để quét bảng nhận xét của giáo viên và chuyển đổi từ các tiêu chí khô khan thành văn xuôi dễ đọc, cô đọng.  
* **Câu hỏi gợi ý:** *"Buổi học hôm qua con đã học những kiến thức gì? Thầy cô có lưu ý hay nhắc nhở gì đặc biệt về con không?"*

## **3\. Kịch bản "Giám sát Thái độ cử chỉ" (Phân tích chuyên sâu)**

* **Mục đích:** Đi sâu vào khía cạnh tâm lý, hành vi và thái độ học tập để giải tỏa những lo lắng cụ thể của phụ huynh mà điểm số không thể hiện hết.  
* **Cách thức:** Chatbot gọi công cụ chuyên biệt `get_lesson_group_comments` để lọc duy nhất nhóm thông tin về **Thái độ học tập**, giúp phụ huynh tập trung vào biểu hiện của con mà không bị xao nhãng bởi các thông số kỹ thuật hay điểm số khác.  
* **Câu hỏi gợi ý:** *"Hôm nay con có tập trung nghe giảng không? Thái độ của con khi làm việc nhóm với các bạn như thế nào?"*

