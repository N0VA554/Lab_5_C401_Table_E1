# SPEC — AI Product Hackathon

**Nhóm:** Teky (Trợ lý Phụ huynh)
**Track:** ☐ VinFast · ☐ Vinmec · ☐ VinUni-VinSchool (Giáo dục) · ☐ XanhSM · ☒ Open
**Problem statement (1 câu):** Phụ huynh Teky không nắm rõ tiến độ học tập của con, phải chờ 5-10 phút gọi hotline hoặc 1 ngày gửi email để được tra cứu thủ công; AI sẽ đóng vai trò trợ lý 24/7 giúp giải đáp thắc mắc và phân tích kết quả học tập bằng biểu đồ trực quan trong dưới 30 giây.

---

## 1. AI Product Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi** | User nào? Pain gì? AI giải gì? | Khi AI sai thì sao? User sửa bằng cách nào? | Cost/latency bao nhiêu? Risk chính? |
| **Trả lời** | *Phụ huynh học sinh. Chờ hotline lâu, không hiểu tiến độ con. AI giải quyết bằng việc tự động hỏi đáp, trực quan hóa kết quả (kỹ năng 4C) và tư vấn 24/7.* | *Nếu AI gợi ý sai hoặc không có dữ liệu, phụ huynh có thể feedback, nhập lại thông tin hoặc yêu cầu chuyển tiếp (fallback) qua hotline người thật.* | *Latency <30 giây. Cost vận hành giảm 97% so với tổng đài. Risk: Phụ huynh hỏi ngoài lề hoặc AI bịa thông tin.* |

**Automation hay augmentation?** ☒ Automation · ☐ Augmentation
**Justify:** *Automation — Chatbot AI tự động hóa hoàn toàn khâu tra cứu thông tin điểm số và tư vấn cơ bản thay cho lễ tân/hotline, giúp giảm 70% lượng gọi hotline.*

**Learning signal:**
1. **User correction đi vào đâu?** Lựa chọn của user (click khóa học), feedback trực tiếp, và yêu cầu "Gặp người thật" (Fallback hotline) được ghi log để cải thiện model từ 5-10% mỗi tháng.
2. **Product thu signal gì để biết tốt lên hay tệ đi?** Implicit: Tỷ lệ click khóa học, thời gian phản hồi (latency). Explicit: Điểm CSAT, số lần bấm nút yêu cầu gặp nhân sự thật.
3. **Data thuộc loại nào?** ☒ User-specific · ☒ Domain-specific · ☐ Real-time · ☐ Human-judgment
   **Có marginal value không?** Có, model sẽ học được cách tư vấn khéo léo hơn dựa trên tỷ lệ chuyển đổi click khóa học từ các phụ huynh trước.

---

## 2. User Stories — 4 paths

### Feature: Trợ lý thông minh kiểm tra lộ trình & Tư vấn khóa học

**Trigger:** Phụ huynh mở ứng dụng và nhắn: "Cho tôi xem tình hình học tập của bé nhà tôi".

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| **Happy** | User thấy gì? Flow kết thúc ra sao? | *AI nhận diện đúng bé, trích xuất điểm. Trả về biểu đồ Radar kỹ năng 4C (Giao tiếp, Phản biện, Sáng tạo, Hợp tác) và tóm tắt nhận xét của giáo viên. Phụ huynh hiểu ngay vấn đề.* |
| **Low-confidence** | System báo "không chắc" bằng cách nào? User quyết thế nào? | *Phụ huynh nhập tên "Gia Huy" (tên phổ biến). AI báo: "Hệ thống tìm thấy 2 bé Gia Huy (Lớp Python và Lớp Scratch). Phụ huynh vui lòng chọn lớp của bé hoặc nhập thêm SĐT."* |
| **Failure** | User biết AI sai bằng cách nào? Recover ra sao? | *AI bịa ra môn học con không học hoặc đánh giá sai thái độ (Hallucination). Phụ huynh thấy thông tin lạ so với thực tế ở nhà.* |
| **Correction** | User sửa bằng cách nào? Data đó đi vào đâu? | *Phụ huynh thắc mắc lại hoặc bấm nút "Liên hệ hỗ trợ/Hotline" ở góc. Hệ thống fallback chuyển đoạn chat cho nhân viên, đồng thời đánh flag đoạn chat để Dev tinh chỉnh prompt giới hạn.* |

---

## 3. Eval metrics + threshold

**Optimize precision hay recall?** ☒ Precision · ☐ Recall
**Tại sao?** Vì đây là dữ liệu giáo dục và điểm số của trẻ em. Nếu AI bịa ra điểm số hoặc nhận xét sai (False Positive), phụ huynh sẽ bức xúc và mất niềm tin. Thà AI báo "Không tìm thấy dữ liệu" (False Negative) còn hơn cung cấp sai thông tin học tập của trẻ.

| Metric | Threshold | Red flag (dừng khi) |
|--------|-----------|---------------------|
| *Thời gian phản hồi (Latency)* | *< 30 giây* | *> 1 phút liên tục trong nhiều giờ.* |
| *Tỷ lệ giảm tải Hotline (Deflection rate)* | *Giảm 70% cuộc gọi* | *Lượng gọi hotline không giảm hoặc tăng lên.* |
| *Điểm hài lòng (CSAT)* | *Mức 4.5/5* | *< 4.0 trong 1 tuần liên tục.* |

---

## 4. Top 3 failure modes

| # | Trigger | Hậu quả | Mitigation |
|---|---------|---------|------------|
| 1 | **Rate Limit Exhaustion** (Quá tải API giờ cao điểm) | *Lỗi 429, chatbot ngừng phản hồi, giảm UX.* | *Áp dụng exponential backoff, cache câu hỏi phổ biến, dùng Local Intent Classifier.* |
| 2 | **Identity Ambiguity** (Nhầm danh tính do trùng tên/thiếu thông tin) | *Trả dữ liệu sai học viên, vi phạm bảo mật, mất uy tín nặng nề.* | *Bắt buộc xác thực thêm SĐT/Lớp học nếu trùng tên (Disambiguation).* |
| 3 | **LLM Hallucination** (AI ảo giác, bịa điểm/nhận xét) | *Phụ huynh bị lừa bởi câu trả lời nghe rất hợp lý nhưng sai sự thật (User không biết bị sai).* | *Hard constraint trong System Prompt "Chỉ trả lời dựa trên dữ liệu cung cấp", yêu cầu trích dẫn ID buổi học.* |

---

## 5. ROI 3 kịch bản

|   | Conservative | Realistic | Optimistic |
|---|-------------|-----------|------------|
| **Assumption** | *Áp dụng giờ hành chính, 60% user dùng thử* | *Áp dụng 24/7, giảm 70% gọi hotline* | *Áp dụng 24/7, điểm CSAT đạt tuyệt đối 4.5/5* |
| **Cost** | *Giảm 50% chi phí vận hành* | *Giảm 80% chi phí vận hành* | *Giảm 97% chi phí vận hành* |
| **Benefit** | *Rút ngắn thời gian chờ còn 2-3 phút* | *Thời gian chờ < 30 giây* | *Thời gian chờ < 30s, Hiểu lộ trình con >90%* |
| **Net** | **Tiết kiệm chi phí nhẹ** | **Chuyển đổi số CSKH thành công** | **Đột phá trải nghiệm, tối ưu lợi nhuận lớn** |

**Kill criteria:** - Chi phí vận hành API cao hơn chi phí duy trì nhân sự tổng đài cũ trong 2 tháng liên tục.
- Tỷ lệ ấn nút "Chuyển gặp người thật" (Fallback) lớn hơn 40%.
- Xảy ra sự cố nghiêm trọng về việc cung cấp sai hoặc lộ điểm số học viên.
## 6. Mini AI spec
Trợ lý Phụ huynh Teky là một giải pháp tự động hóa hoàn toàn (Automation) nhằm giải quyết dứt điểm "nỗi đau" chờ đợi lâu của phụ huynh khi muốn tra cứu tiến độ học tập của con. Thay vì mất 5-10 phút gọi hotline hoặc 1 ngày chờ email, AI đóng vai trò như một tư vấn viên 24/7, trích xuất dữ liệu và trực quan hóa kỹ năng 4C của trẻ thành biểu đồ dễ hiểu chỉ trong chưa đầy 30 giây.

Về mặt chất lượng, hệ thống kiên quyết tối ưu hóa độ chính xác (Precision). Đối với dữ liệu giáo dục, tính minh bạch và chân thực là tối thượng; AI được thiết lập thà báo "không tìm thấy dữ liệu" còn hơn là bịa đặt điểm số hay nhận xét (Hallucination) gây phẫn nộ và đánh mất niềm tin của phụ huynh. Các rủi ro lớn nhất như quá tải API, nhầm lẫn học sinh trùng tên, và ảo giác LLM đều được kiểm soát bằng cơ chế xác thực thông tin phụ trợ (SĐT, lớp học) và các giới hạn kiểm soát chặt chẽ (hard constraints) ở mức hệ thống.

Sản phẩm sở hữu một "bánh đà dữ liệu" (Data Flywheel) mạnh mẽ. Mọi tương tác của người dùng — từ việc bấm xem khóa học gợi ý, gửi phản hồi, cho đến những lần yêu cầu chuyển tiếp sang người thật (hotline fallback) — đều trở thành tín hiệu học tập (learning signal). Nhờ lượng dữ liệu domain-specific này, model có thể cải thiện mức độ chính xác từ 5-10% mỗi tháng, ngày càng nâng cao kỹ năng tư vấn khéo léo và mang lại tỷ lệ chuyển đổi cao hơn cho các chiến dịch của Teky.
---
