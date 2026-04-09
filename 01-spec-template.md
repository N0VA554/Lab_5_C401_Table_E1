# SPEC — AI Product Hackathon

**Nhóm:** Teky (Trợ lý Phụ huynh)
**Track:** ☐ VinFast · ☐ Vinmec · ☐ VinUni-VinSchool (Giáo dục) · ☐ XanhSM · ☒ Open
**Problem statement (1 câu):** Phụ huynh không rõ tiến độ học tập của con và phải chờ đợi lâu (5-10 phút qua hotline, 1 ngày qua email) để được hỗ trợ, AI sẽ đóng vai trò trợ lý 24/7 giúp giải đáp thắc mắc, phân tích kết quả học tập và tư vấn khóa học chỉ trong dưới 30 giây.

---

## 1. AI Product Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi** | User nào? Pain gì? AI giải gì? | Khi AI sai thì sao? User sửa bằng cách nào? | Cost/latency bao nhiêu? Risk chính? |
| **Trả lời** | *Phụ huynh học sinh. Chờ hotline lâu, không hiểu tiến độ con. AI giải quyết bằng việc tự động hỏi đáp, trực quan hóa kết quả (kỹ năng 4C) và tư vấn 24/7.* | *Nếu AI gợi ý sai hoặc không có dữ liệu, phụ huynh có thể feedback, nhập lại thông tin hoặc yêu cầu chuyển tiếp (fallback) qua hotline người thật.* | *Latency <30 giây. Cost vận hành giảm 97% so với tổng đài truyền thống. Risk: Phụ huynh hỏi ngoài lề hoặc AI ảo giác thông tin.* |

**Automation hay augmentation?** ☒ Automation · ☐ Augmentation
Justify: *Automation — Chatbot AI tự động hóa hoàn toàn khâu tra cứu thông tin điểm số và tư vấn cơ bản thay cho lễ tân/hotline, giúp giảm 70% lượng gọi hotline.*

**Learning signal:**

1. User correction đi vào đâu? *Hệ thống ghi nhận feedback của người dùng và các lựa chọn (click khóa học) để cải thiện model từ 5-10% mỗi tháng.*
2. Product thu signal gì để biết tốt lên hay tệ đi? *Đo lường qua tỷ lệ Click khóa học, Lựa chọn user, Điểm Feedback, Tần suất yêu cầu gặp người thật (Request human) và Thời gian phản hồi (Response time).*
3. Data thuộc loại nào? · ☒ Real-time · ☐ Human-judgment
   Có marginal value không? *Có, model sẽ học được cách tư vấn khéo léo hơn dựa trên tỷ lệ chuyển đổi click khóa học từ các phụ huynh trước.*

---

## 2. User Stories — 4 paths

### Feature: *Trợ lý thông minh kiểm tra lộ trình & Tư vấn khóa học*

**Trigger:** *Phụ huynh mở ứng dụng/khung chat để hỏi về tình hình học tập của con[cite: 67].*

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy Path — Trải nghiệm mượt mà | User thấy gì? Flow kết thúc ra sao? | *User nhận được biểu đồ radar phân tích kỹ năng 4C, nhận xét chi tiết buổi học. Flow kết thúc khi user hài lòng và hiểu rõ tiến độ.* |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | *Khi câu hỏi mơ hồ, AI tự động hỏi lại để làm rõ ý định của user thay vì đoán bừa.* |
| Failure — AI sai/Thiếu dữ liệu | User biết AI sai bằng cách nào? Recover ra sao? | *User hỏi thông tin ngoài lề (VD: Mua cây xanh) hoặc không có dữ liệu học viên. AI từ chối trả lời vấn đề không liên quan hoặc yêu cầu nhập lại định danh.* |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | *User có thể trực tiếp nhấn nút "Request human" (yêu cầu người thật). Tín hiệu này được ghi log để team Dev tối ưu lại kịch bản cho AI.* |

---

## 3. Eval metrics + threshold

**Optimize precision hay recall?** ☒ Precision · ☐ Recall
Tại sao? *Đối với dữ liệu học tập của trẻ, tính chính xác (Precision) là tối quan trọng. Nếu AI bịa ra điểm số hoặc đánh giá sai lệch thái độ của trẻ, phụ huynh sẽ mất niềm tin hoàn toàn. Thà báo "Không có dữ liệu" còn hơn cung cấp sai.*

| Metric | Threshold | Red flag (dừng khi) |
|--------|-----------|---------------------|
| *Thời gian phản hồi (Latency)* | *< 30 giây* | *> 1 phút liên tục trong nhiều giờ.* |
| *Tỷ lệ giảm tải Hotline* | *Giảm 70% cuộc gọi* | *Lượng gọi hotline không giảm hoặc tăng lên.* |
| *Điểm hài lòng (CSAT)* | *Mức 4.5/5* | *< 4.0 trong 1 tuần liên tục.* |

---

## 4. Top 3 failure modes

| # | Trigger | Hậu quả | Mitigation |
|---|---------|---------|------------|
| 1 | *Câu hỏi mơ hồ (Ambiguous query)* | *AI đoán sai ý định (Ví dụ hỏi công thức nấu ăn/mua đồ ngoài lề).* | *Thiết lập prompt rào kỹ miền kiến thức (chỉ trả lời giáo dục), hỏi ngược lại user để làm rõ.* |
| 2 | *Thiếu dữ liệu hệ thống (Missing Data)* | *Trả về kết quả trắng hoặc AI tự ảo giác ra kết quả học tập giả.* | *Validate đầu vào, chủ động thông báo "Không có dữ liệu" và yêu cầu phụ huynh nhập lại mã học viên.* |
| 3 | *Khách hàng mất kiên nhẫn* | *Chatbot cứ lặp đi lặp lại câu hỏi, gây trải nghiệm tệ hại.* | *Luôn có lối thoát: Nút "Gặp nhân viên hỗ trợ" (Fallback hotline) hiển thị rõ ràng.* |

---

## 5. ROI 3 kịch bản

|   | Conservative | Realistic | Optimistic |
|---|-------------|-----------|------------|
| **Assumption** | *Áp dụng giờ hành chính, 60% user dùng thử* | *Áp dụng 24/7, giảm 70% gọi hotline* | *Áp dụng 24/7, điểm CSAT đạt tuyệt đối 4.5/5* |
| **Cost** | *Giảm 50% chi phí vận hành* | *Giảm 80% chi phí vận hành* | *Giảm 97% chi phí vận hành (Cost giảm 97%)* |
| **Benefit** | *Rút ngắn thời gian chờ còn 2-3 phút* | *Thời gian chờ < 30 giây [cite: 49]* | *Thời gian chờ < 30s, Hiểu kết quả tăng >90%* |
| **Net** | **Tiết kiệm chi phí nhẹ** | **Chuyển đổi số mảng CSKH thành công** | **Đột phá trải nghiệm, tối đa hóa biên lợi nhuận** |

**Kill criteria:** * **Lỗ kéo dài:** Chi phí vận hành AI API cao hơn chi phí duy trì nhân sự tổng đài cũ.
* **Chất lượng thấp:** Tỷ lệ phụ huynh yêu cầu chuyển sang người thật (Request human) vượt quá 40%.
* **Sai lệch thông tin:** Gặp sự cố nghiêm trọng về việc lộ lọt điểm số sai học viên.

---

## 6. Mini AI spec (1 trang)

**TEKY CHATBOT - Trợ lý Giáo dục Tự động hóa**

**Vấn đề:** Hiện nay, phụ huynh Teky thiếu một kênh cập nhật thông tin học tập của con tức thời. Việc phụ thuộc vào hotline (chờ 5-10 phút) hay email (chờ 1 ngày) khiến trải nghiệm bị đứt gãy, bộ phận CSKH bị quá tải, và phụ huynh thường "không rõ kết quả" thực tế của con mình.

**Giải pháp AI:** Một Chatbot Trợ lý Phụ huynh hoạt động 24/7 (Automation). Khi phụ huynh có thắc mắc, AI sẽ trích xuất cơ sở dữ liệu học tập và phản hồi dưới 30 giây. Bot có khả năng phân tích biểu đồ kỹ năng 4C, đánh giá tiến độ từng buổi học, và cá nhân hóa việc tư vấn khóa học tiếp theo. 

**Chất lượng & Rủi ro:** Sản phẩm tối ưu hóa Precision — tuyệt đối không cung cấp sai lệch điểm số. Rủi ro chính nằm ở việc thiếu dữ liệu đầu vào hoặc bị vặn vẹo bởi các câu hỏi ngoài lề (hỏi mua sắm, nấu ăn)[cite: 130]. Tuy nhiên, hệ thống đã trang bị cơ chế tự động hỏi lại (khi câu hỏi mơ hồ) và Fallback trực tiếp sang hotline khi người dùng yêu cầu người thật.

**Data Flywheel:** Chatbot thu thập liên tục các learning signals như: click khóa học, lựa chọn người dùng, thời gian phản hồi và feedback trực tiếp. Vòng lặp này giúp AI tự tinh chỉnh, kỳ vọng cải thiện chất lượng phản hồi từ 5-10% mỗi tháng, đồng thời hướng tới mục tiêu giảm 97% chi phí vận hành và nâng mức độ thấu hiểu kết quả học tập của phụ huynh lên trên 90%.