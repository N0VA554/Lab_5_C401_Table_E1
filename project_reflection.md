# Technical Project Reflection: TekyChatbot System

**Document Type:** Technical Retrospective / Post-mortem 
**Project:** TekyChatbot (LLM-powered Educational Analytics Assistant)

---

## 1. Executive Summary & Objectives
Dự án TekyChatbot được thiết kế và phát triển nhằm giải quyết bài toán xử lý rác dữ liệu phi cấu trúc và bán cấu trúc (JSON-based student portfolios). Hệ thống hoạt động như một lớp middleware thông minh, đóng vai trò trích xuất (extract), tính toán (transform), và phân tích ngữ nghĩa (semantic analysis) dữ liệu học tập nội bộ để cung cấp một giao diện truy vấn tự nhiên (Natural Language Interface) cho người dùng cuối. 

Mục tiêu kỹ thuật cốt lõi là duy trì độ trễ (latency) thấp khi phản hồi, giảm thiểu số lượng token tiêu thụ thông qua kiến trúc công cụ (tool-calling architecture), đồng thời đảm bảo tính nhất quán của dữ liệu khi biểu diễn dưới dạng biểu đồ song song với văn bản.

## 2. System Architecture & Tech Stack

Hệ thống được thiết kế theo kiến trúc **Agentic Workflow**, phân chia rõ ràng giữa tầng giao diện, tầng xử lý tác vụ (Agent) và tầng nghiệp vụ tính toán:

*   **Tầng Giao diện (Presentation Layer):** Được triển khai bằng **Streamlit** kết hợp **Plotly**. Phục vụ mục đích render liên tục (reactive rendering) các biểu đồ Radar và Bar Chart dựa trên state của ứng dụng.
*   **Tầng Điều phối (Orchestration Layer):** Xây dựng trên **LangGraph / LangChain**. Chịu trách nhiệm quản lý LLM State, thực thi cơ chế định tuyến tác vụ (Task Routing) và kiểm soát luồng hội thoại.
*   **Tầng Công cụ (Execution Layer):** Tập hợp 8 custom tools được định nghĩa nghiêm ngặt về kiểu dữ liệu I/O, thực hiện các truy vấn từ O(1) qua JSON Path đến các vòng lặp O(N) qua toàn bộ cấu trúc khóa học.
*   **Data Layer:** Sử dụng Local JSON filesystem cho giai đoạn PoC, giả lập NoSQL document structure.

## 3. Core Technical Implementations

### 3.1. Multi-Tier Tool Definition (Kiến trúc Công cụ Đa tầng)
Hệ thống không parse qua LLM toàn bộ document (gây tràn context window) mà áp dụng mô hình phân tầng công cụ:
*   **Macro-level Analysis:** Hàm `get_course_summary_scores` tổng hợp (aggregate) dữ liệu toàn khóa bằng thuật toán nội bộ (`scoring.py`), truyền kết quả vô hướng (scalar metrics) lại cho agent.
*   **Micro-level Extraction:** Các hàm `get_specific_criteria_comment` áp dụng deterministic search (tìm kiếm xác định) để trích xuất exaclty matching data thay vì để LLM tự generate, đảm bảo tính nguyên vẹn của nhận xét giáo viên (Zero Hallucination).

### 3.2. State Injection & Prompt Engineering
Áp dụng mô hình **Late-Binding Context**. Thay vì context window bị nhồi nhét từ ban đầu, chỉ phần system prompt chứa metadata và điểm số baseline (`scoring_summary`) được khởi tạo tĩnh. Các dữ liệu động khác được Agent chủ động truy xuất (pull) thông qua function calling khi phát hiện intent của câu hỏi.

## 4. Technical Challenges & Resolutions

### 4.1. LLM API Schema Validation Error do Mismatch ToolMessage
*   **Triệu chứng:** Exception phát sinh từ LLM Provider (OpenAI/Gemini) sau 1-2 lượt hội thoại (turns) vì lịch sử truyền đi chứa `AIMessage` kèm thuộc tính `tool_calls` nhưng thiếu `ToolMessage` tương ứng (do cơ chế slice list giới hạn lịch sử).
*   **Giải pháp (Root-cause Fix):** Triển khai cơ chế **History Sanitization** tại tầng Streamlit (`app.py`). Trong quá trình append lịch sử vào bộ nhớ hội thoại, tiến hành map/filter để tước bỏ array `tool_calls` khỏi raw `AIMessage`, ép kiểu về phân đoạn text standard (`AIMessage(content=m.content)`). Phương pháp này chặn đứng triệt để lỗi parse schema của API mà vẫn giữ nguyên context hội thoại cho LLM.

### 4.2. Streamlit Reactivity & Duplicate Element ID Exception
*   **Triệu chứng:** Exception `streamlit.errors.StreamlitDuplicateElementId` khi ứng dụng kích hoạt fallback logic (ví dụ: hiển thị Contact Card) nhiều lần trong cùng một runtime state do Streamlit duy trì reference hash tĩnh trên các Widget IDs.
*   **Giải pháp:** Áp dụng dynamic key generation bằng thư viện `uuid` (`uuid.uuid4().hex`) cho các functional components. Cấu trúc lại vòng đời (lifecycle) của Fallback Component, đảm bảo mỗi lần render đều được snapshot vào một unique memory block độc lập.

### 4.3. Data Normalization Cross-Modules
*   **Triệu chứng:** Logic scoring cũ gặp hiện tượng "Out-of-Bounds" khi xử lý dữ liệu học sinh tham gia nhiều module liên tiếp.
*   **Giải pháp:** Refactor toàn bộ pipeline trong module `scoring.py`. Chuyển đổi định dạng list traversal đơn giản thành nested-loop có khả năng flatten array đa cấp (multi-level payload flatten) trước khi apply các toán tử thống kê học (Mean Calculation).

## 5. Future Engineering Improvements (Roadmap)

Trong các pha phát triển tiếp theo, kiến trúc kỹ thuật cần mở rộng ở các khía cạnh:

1.  **Vectorization & Semantic Search (RAG):** Thay vì sử dụng deterministic tool (`query_json`), cần đẩy toàn bộ lịch sử JSON vào Vector Database (như Qdrant/Milvus). Áp dụng Embedding để agent tìm kiếm nhận xét mờ (Fuzzy Search) nhanh hơn với nội dung hàng GBs.
2.  **Streaming Callbacks:** Áp dụng LangChain Async Streaming API để render token cho UI thay vì block synchronous UI waiting (Spinner). Giảm perceived latency cho người dùng.
3.  **Data Persistence Integration:** Dịch chuyển Local JSON parsing sang async calls thông qua RESTful API, tương tác với Backend Database nhằm đồng bộ state real-time (ví dụ: MongoDB/PostgreSQL).

---
**Conclusion:** 
Kiến trúc hiện tại của dự án đáp ứng đầy đủ tiêu chuẩn của một MVP (Minimum Viable Product) phức hợp. Hệ thống quản lý tốt State Management của cả hai môi trường vốn xung đột nhau về triết lý thiết kế (Streamlit re-run model vs LangGraph persistent checkpointer), thiết lập một design pattern chuẩn mực để mở rộng các luồng LLM Agents tương lai.
