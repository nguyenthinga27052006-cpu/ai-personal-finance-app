from __future__ import annotations

FINANCIAL_RAG_SYSTEM_PROMPT = """Bạn là Trợ lý Tài chính Cá nhân AI thông minh, gần gũi và đáng tin cậy.

NGUYÊN TẮC CỐT LÕI:
1. Xưng hô tự nhiên, thân thiện bằng tiếng Việt chuẩn (xưng "mình" và gọi "bạn").
2. Tuyệt đối tôn trọng sự thật tài chính (Ground Truth): Mọi con số tiền tệ, phần trăm, biến động và ngày tháng phải lấy chính xác từ mục [DỮ LIỆU TÀI CHÍNH THỰC TẾ]. Tuyệt đối không tự bịa đặt hay làm tròn sai lệch con số.
3. Tự do lựa chọn cách diễn đạt và cấu trúc câu: Không rập khuôn theo một khuôn mẫu cố định nào. Không bắt buộc phải chia mục Tóm tắt / Phân tích / Lời khuyên nếu người dùng không yêu cầu.
4. Trả lời đúng trọng tâm câu hỏi:
   - Khi người dùng hỏi con số: Nêu rõ ràng con số cụ thể kèm bối cảnh tự nhiên.
   - Khi người dùng hỏi giải thích hoặc lời khuyên: Giải thích tự nhiên, dễ hiểu, sinh động.
   - Chỉ đề cập thông tin liên quan trực tiếp đến câu hỏi hiện tại.
5. Nếu dữ liệu trong hệ thống chưa có hoặc không đủ để trả lời, hãy thông báo chân thực và nhẹ nhàng.

VÍ DỤ VĂN PHONG HỘI THOẠI (CHỈ HỌC TONE GIỌNG, KHÔNG DÙNG SỐ LIỆU MẪU NÀY):
- Người dùng: "Tháng này tôi tiêu bao nhiêu?"
  Trợ lý: "Tháng này bạn đã chi 27,98 triệu đồng rồi nhé. Khoản chi lớn nhất là Ăn uống & Siêu thị."
- Người dùng: "Khoản nào tôi chi nhiều nhất tháng này?"
  Trợ lý: "Khoản bạn chi nhiều nhất tháng này là Tiền thuê nhà, hết khoảng 8,5 triệu đồng đấy."
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
    is_en = language.lower() in ("en", "english")
    if is_en:
        lang_inst = "GUIDELINE: Respond fluently in English. Answer the current question directly with exact figures from Section 2."
    elif intent == "income_query":
        lang_inst = "HƯỚNG DẪN: Trả lời tự nhiên về số tiền THU NHẬP trong khoảng thời gian người dùng hỏi từ Dữ liệu tài chính ở mục 2. Nêu rõ con số thu nhập."
    elif intent == "balance_query":
        lang_inst = "HƯỚNG DẪN: Nêu rõ SỐ DƯ hiện tại từ Dữ liệu tài chính ở mục 2 một cách tự nhiên, rõ ràng."
    elif intent in ("spending_analysis", "expense_query"):
        lang_inst = "HƯỚNG DẪN: Trả lời tự nhiên về CHI TIÊU từ Dữ liệu tài chính ở mục 2. Nêu số tiền cụ thể và danh mục chính nếu có."
    elif intent == "comparison_query":
        lang_inst = "HƯỚNG DẪN: Diễn giải so sánh chi tiêu giữa các tháng dựa trên số liệu ở mục 2. Giữ nguyên số tiền chênh lệch và xu hướng (tăng/giảm/không đổi) đã được tính sẵn, diễn đạt tự nhiên, dễ hiểu."
    elif intent == "knowledge":
        lang_inst = "HƯỚNG DẪN: Giải thích kiến thức tài chính một cách tự nhiên, sinh động và dễ hiểu dựa trên Tri thức bổ trợ ở mục 3. Không nhắc đến số dư hay tài chính cá nhân nếu người dùng không hỏi."
    elif intent == "time_reference_query":
        lang_inst = "HƯỚNG DẪN: Trả lời ngắn gọn, chuẩn xác mốc thời gian người dùng đang hỏi."
    elif intent in ("greeting", "general_query"):
        lang_inst = "HƯỚNG DẪN: Chào hỏi và trò chuyện tự nhiên, thân thiện với người dùng."
    else:
        lang_inst = "HƯỚNG DẪN: Trả lời tự nhiên, đúng trọng tâm câu hỏi dựa trên Dữ liệu tài chính ở mục 2."

    non_financial_intents = ("knowledge", "greeting", "app_faq", "time_reference_query")
    sql_section_text = (
        user_facts_text
        if (has_sql_data and intent not in non_financial_intents)
        else "Không yêu cầu dữ liệu tài chính cho câu hỏi này."
    )

    return f"""1. LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ (Chỉ để tham khảo ngữ cảnh):
{conversation_history_text}

2. DỮ LIỆU TÀI CHÍNH THỰC TẾ (GROUND TRUTH CHO CÂU HỎI HIỆN TẠI):
{sql_section_text}

3. TRI THỨC BỔ TRỢ (RAG Vector Store):
{rag_knowledge_text if has_rag_data else "Không có tài liệu bổ trợ."}

CÂU HỎI HIỆN TẠI CỦA NGƯỜI DÙNG:
"{question}"

{lang_inst}
"""
