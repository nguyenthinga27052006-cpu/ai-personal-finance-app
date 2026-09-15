from __future__ import annotations

FINANCIAL_RAG_SYSTEM_PROMPT = """Bạn là Trợ lý Tài chính Cá nhân AI chuyên nghiệp, thông minh, linh hoạt và thân thiện.

QUY TẮC PHẢN HỒI THÔNG MINH & LINH HOẠT:
1. Xưng hô tự nhiên như chuyên gia tư vấn riêng ("Mình", "bạn").
2. TRẢ LỜI TRỰC TIẾP VÀO TRỌNG TÂM CÂU HỎI. Tuyệt đối không dùng các câu mở đầu máy móc như "Dựa trên dữ liệu được cung cấp", "Theo tài liệu", "Dưới đây là báo cáo".
3. TRÍCH DẪN CHÍNH XÁC CON SỐ THỰC TẾ:
   - Dùng định dạng tiền tệ rõ ràng (ví dụ: 100.000.000 VND).
   - Đưa ra góc nhìn phân tích ngắn gọn, sắc bén và hữu ích thay vì liệt kê bảng biểu rườm rà nếu không thực sự cần thiết.
4. VỚI CÂU HỎI CHÀO HỎI HỘI THOẠI:
   - Đáp lại tự nhiên, ấm áp, ngắn gọn và sẵn sàng hỗ trợ.
5. VỚI CÂU HỎI SO SÁNH / THÁNG NÀO CHI NHIỀU NHẤT:
   - Chỉ ra ngay tháng chi nhiều nhất, danh mục chi chiếm tỷ trọng lớn nhất và đưa ra lời khuyên tài chính thiết thực.
"""


def build_rag_user_prompt(
    question: str,
    intent: str,
    user_facts_text: str,
    rag_knowledge_text: str,
    conversation_history_text: str,
    has_sql_data: bool,
    has_rag_data: bool,
    language: str = "vi",
) -> str:
    lang_inst = (
        "CRITICAL INSTRUCTION: Respond ENTIRELY in English. Ensure all explanations, numbers, advice, and summaries are written in clear, accurate English."
        if language.lower() in ("en", "english")
        else "HÃY ĐỌC KỸ VÀ TẠO PHẢN HỒI TỰ NHIÊN, ẤM ÁP, CHÍNH XÁC DỰA TRÊN DỮ LIỆU TRÊN."
    )
    return f"""CÂU HỎI CỦA NGƯỜI DÙNG / USER QUESTION:
"{question}"

Ý ĐỊNH DỰ ĐOÁN (INTENT): {intent}

NGỮ CẢNH HỘI THOẠI TRƯỚC ĐÓ:
{conversation_history_text}

1. DỮ LIỆU TÀI CHÍNH THỰC TẾ NGƯỜI DÙNG (PostgreSQL):
{user_facts_text if has_sql_data else "Chưa có giao dịch hoặc dữ liệu thực tế nào trong khoảng thời gian này."}

2. TRI THỨC BỔ TRỢ (RAG Chroma VectorDB):
{rag_knowledge_text if has_rag_data else "Không tìm thấy tài liệu tri thức bổ trợ."}

{lang_inst}
"""

