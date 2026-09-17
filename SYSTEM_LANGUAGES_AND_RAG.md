# TỔNG HỢP NGÔN NGỮ PHÁT TRIỂN & CƠ CHẾ RAG EMBEDDING HỆ THỐNG
*(System Languages & RAG Embedding Architecture Overview)*

> **Dự án**: AI Personal Finance App  
> **Thư mục gốc**: `d:\Projects\ai-personal-finance\ai-personal-finance-app`

---

## 📋 MỤC LỤC
1. [Các Ngôn Ngữ & Công Nghệ Được Sử Dụng](#1-các-ngôn-ngữ--công-nghệ-được-sử-dụng)
2. [Chi Tiết Vai Trò Của Từng Ngôn Ngữ](#2-chi-tiết-vai-trò-của-từng-ngôn-ngữ)
3. [Cơ Chế RAG Embedding & Các Mô Hình Embedding](#3-cơ-chế-rag-embedding--các-mô-hình-embedding)
4. [Quy Trình Tìm Kiếm Hybrid Search (Sparse + Dense)](#4-quy-trình-tìm-kiếm-hybrid-search-sparse--dense)

---

## 1. CÁC NGÔN NGỮ & CÔNG NGHỆ ĐƯỢC SỬ DỤNG

Hệ thống được xây dựng theo kiến trúc Microservices & Cross-Platform kết hợp các ngôn ngữ lập trình và định dạng cấu hình chính sau:

| Ngôn ngữ / Công nghệ | Phạm vi ứng dụng trong hệ thống | Thư mục chính liên quan |
| :--- | :--- | :--- |
| **Python 3.11+** | Backend REST API, RAG AI Engine, OCR Hóa đơn, Background Worker, Script xử lý DB | [`apps/api`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api), [`apps/worker`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/worker) |
| **Dart (Flutter SDK)** | Frontend Mobile & Web App (iOS, Android, Web, Windows/macOS Desktop) | [`apps/mobile`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile) |
| **SQL (PostgreSQL / PL/pgSQL)** | Lưu trữ cơ sở dữ liệu quan hệ, tìm kiếm vector qua extension `pgvector` | [`apps/api/app/db`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/db), [`apps/api/migrations`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/migrations) |
| **PowerShell (.ps1)** | Kịch bản tự động hóa môi trường (Dev Ops, Docker Control, DB Migration, Test Automation) | [`scripts/`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts) |
| **Docker / YAML Syntax** | Containerization, Orchestration dịch vụ (API, Worker, Postgres, Redis) | [`infra/docker`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra/docker), [`docker-compose.dev.yml`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra/docker/docker-compose.dev.yml) |
| **JSON / TOML / INI** | File cấu hình hệ thống, dependencies, cấu hình linter & migration | `pyproject.toml`, `pubspec.yaml`, `alembic.ini`, `.env` |

---

## 2. CHI TIẾT VAI TRÒ CỦA TỪNG NGÔN NGỮ

### 🐍 1. Python (Backend & AI Core)
* **Framework**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic.
* **Vai trò**:
  * Xử lý toàn bộ logic nghiệp vụ (Authentication, Quản lý giao dịch, Ngân sách, Mục tiêu tài chính).
  * Xây dựng lõi RAG Chatbot (Retrieval-Augmented Generation), quản lý Vector Store, Prompt Engineering và tương tác với các LLM Provider (OpenAI / Gemini / Ollama).
  * Xử lý OCR hóa đơn (Receipt recognition) và phân loại chi tiêu tự động.

### 🎯 2. Dart (Frontend App với Flutter Framework)
* **Framework**: Flutter, State Management (Riverpod / Provider), HTTP Client (Dio), GoRouter.
* **Vai trò**:
  * Phát triển giao diện người dùng (UI/UX) đa nền tảng (iOS, Android, Web, Desktop) với thiết kế hiện đại, mượt mà.
  * Tương tác với Backend API qua REST API và WebSocket/Streaming cho trải nghiệm Chatbot trực tiếp.

### 🗄️ 3. SQL & pgvector (Database Layer)
* **Cơ sở dữ liệu**: PostgreSQL 16 tích hợp Extension `pgvector`.
* **Vai trò**:
  * Lưu trữ cấu trúc dữ liệu quan hệ (Người dùng, Tài khoản, Giao dịch, Ngân sách, Lịch sử chat).
  * Lưu trữ các vector nhúng (vector embeddings) và thực hiện các phép truy vấn tìm kiếm độ tương đồng vector (`cosine distance`, `L2 distance`).

### 🛠️ 4. PowerShell & Shell Scripting (DevOps & Management)
* **Thư mục**: [`scripts/`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts)
* **Vai trò**:
  * Tự động hóa các thao tác điều khiển môi trường: `dev-up.ps1` (chạy Docker container), `migrate.ps1` (chạy DB migrations), `reset-dev-db.ps1` (làm sạch dữ liệu dev), `test.ps1` (chạy bộ kiểm thử tự động).

---

## 3. CƠ CHẾ RAG EMBEDDING & CÁC MÔ HÌNH EMBEDDING

Tệp nguồn định nghĩa cơ chế Embedding: [`apps/api/app/ai/rag/vector_store.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/vector_store.py)  
Lớp đại diện: `DenseEmbeddingProvider`

### 💡 Hệ thống RAG hỗ trợ Kiến trúc Pluggable Embedding (Cho phép chuyển đổi linh hoạt qua biến môi trường `EMBEDDING_PROVIDER`):

```
                       ┌──────────────────────────────────────────────┐
                       │           EMBEDDING PROVIDERS                │
                       └──────────────────────┬───────────────────────┘
                                              │
         ┌───────────────────┬────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                ▼                   ▼                   ▼
┌─────────────────┐ ┌────────────────┐ ┌─────────────┐ ┌─────────────────────┐ ┌─────────────────┐
│ SemanticVector  │ │    OpenAI      │ │   Gemini    │ │Sentence-Transformers│ │   ChromaDB /    │
│(Local Default)  │ │ (text-embed-3) │ │ (text-004)  │ │      (bge-m3)       │ │    pgvector     │
└─────────────────┘ └────────────────┘ └─────────────┘ └─────────────────────┘ └─────────────────┘
```

#### 1️⃣ `semantic_vector` (Mặc định - Chạy hoàn toàn Local, Không tốn chi phí API)
* **Cơ chế**:
  1. **Financial Synonym Expansion (Mở rộng từ đồng nghĩa ngành tài chính)**:  
     Hệ thống tự động phát hiện và ánh xạ các cụm từ tiếng Việt đời thường sang khái niệm tài chính chuyên ngành.  
     *Ví dụ*:  
     * `"lương về"` ➡️ ánh xạ sang `["thu_nhập", "lương", "tiền_vào", "income"]`  
     * `"thủng ví"` ➡️ ánh xạ sang `["vượt_ngân_sách", "chi_tiêu", "hạn_mức", "deficit"]`  
     * `"tích sản"` ➡️ ánh xạ sang `["đầu_tư", "tích_lũy", "dca", "chứng_chỉ_quỹ"]`  
     * `"50/30/20"` ➡️ ánh xạ sang `["quy_tắc_50", "nhu_cầu_thiết_yếu", "mong_muốn_cá_nhân"]`
  2. **Feature Concept Vectorization & Hashing Trick**:  
     Từ văn bản nhập vào, hệ thống trích xuất trọng số tần suất từ kết hợp trọng số từ đồng nghĩa, sau đó dùng thuật toán Hashing biến đổi thành vector 32 chiều (`32-dim dense float array`) được chuẩn hóa L2 norm.
  3. **Cosine Similarity Calculator**:  
     Tính độ tương đồng góc Cosine giữa Vector truy vấn (Query) và Vector đoạn văn bản kiến thức (Chunk Knowledge) để xếp hạng.

#### 2️⃣ `openai` (Cloud High-Accuracy Embedding)
* **Mô hình**: `text-embedding-3-small` (Độ dài vector: 1536 chiều).
* **Ứng dụng**: Dành cho môi trường Production khi cấu hình `OPENAI_API_KEY`, cung cấp độ chính xác cao nhất cho ngữ nghĩa tiếng Anh và tiếng Việt.

#### 3️⃣ `gemini` (Google GenAI Embedding)
* **Mô hình**: `text-embedding-004` (Độ dài vector: 768 chiều).
* **Ứng dụng**: Tối ưu khi kết nối với hệ sinh thái Google Gemini API.

#### 4️⃣ `sentence_transformers` / `fastembed` (Local Open-Source AI Model)
* **Mô hình**: `bge-m3` (BAAI BGE-M3 model).
* **Ứng dụng**: Mô hình nhúng đa ngôn ngữ thế hệ mới chạy cục bộ trên CPU/GPU, cho kết quả tìm kiếm ngữ nghĩa tiếng Việt cực kỳ ấn tượng mà không phụ thuộc cloud API.

---

## 4. QUY TRÌNH TÌM KIẾM HYBRID SEARCH (SPARSE + DENSE)

Để đạt độ chính xác tối đa khi chatbot trả lời câu hỏi tài chính của người dùng, hệ thống kết hợp **2 cơ chế tìm kiếm song song (Hybrid Search)**:

### 🔍 1. Sparse Search (BM25 Tiếng Việt - Chính xác theo từ khóa)
* **Lớp xử lý**: `VietnameseBM25Tokenizer` & `VietnameseBM25Searcher` trong [`vector_store.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/vector_store.py#L75-L148)
* **Cơ chế**:
  * Tách từ tiếng Việt bằng thư viện chuyên dụng (`pyvi` hoặc `underthesea`). Nếu chưa cài đặt, hệ thống tự động tách từ ghép tài chính (`"quỹ_khẩn_cấp"`, `"nhu_cầu_thiết_yếu"`, `"tuyết_lăn"`,...).
  * Chấm điểm BM25 dựa trên tần suất từ khóa chính xác xuất hiện trong đoạn văn bản.

### 🧠 2. Dense Search (Vector Search - Hiểu ngữ nghĩa)
* Chuyển đổi truy vấn của người dùng thành Vector và thực hiện truy vấn Cosine Similarity trong `RAGVectorStore` (ChromaDB / pgvector).

### 🔀 3. Reciprocal Rank Fusion (RRF) & Reranking
* Kết quả từ **BM25 (Sparse)** và **Vector Search (Dense)** được hợp nhất bằng thuật toán **RRF (Reciprocal Rank Fusion)** để chọn ra các đoạn tài liệu có điểm liên quan cao nhất trước khi đưa vào LLM để tổng hợp câu trả lời cuối cùng.

---
*Tài liệu tổng hợp về Ngôn ngữ lập trình và Cơ chế RAG Embedding của AI Personal Finance App.*
