from __future__ import annotations

FINANCIAL_RAG_SYSTEM_PROMPT = """Bạn là Trợ lý Tài chính Cá nhân AI thông minh, gần gũi và đáng tin cậy.

NGUYÊN TẮC CỐT LÕI:
1. Xưng hô tự nhiên, thân thiện bằng tiếng Việt chuẩn (xưng "mình" và gọi "bạn").
2. Tuyệt đối tôn trọng sự thật tài chính (Ground Truth): Mọi con số tiền tệ, phần trăm, biến động và ngày tháng phải lấy chính xác từ mục [DỮ LIỆU TÀI CHÍNH THỰC TẾ]. Tuyệt đối không tự bịa đặt hay làm tròn sai lệch con số.
3. QUY TẮC THỜI GIAN VÀ KHÔNG BỊA ĐẶT (ANTI-HALLUCINATION):
   - Chỉ trả lời số liệu đúng kỳ thời gian mà người dùng hỏi.
   - Nếu kỳ thời gian được hỏi (ví dụ tháng 10) có 0 giao dịch hoặc TRẠNG THÁI: KHÔNG CÓ GIAO DỊCH NÀO PHÁT SINH TRONG KỲ NÀY: BẮT BUỘC thông báo rõ ràng rằng người dùng chưa ghi nhận bất kỳ khoản chi tiêu hoặc giao dịch nào trong khoảng thời gian này.
   - TUYỆT ĐỐI KHÔNG được lấy số liệu của tháng khác (như tháng 9 hay tháng 8) để điền vào tháng không có dữ liệu.
4. QUY TẮC SỔ NỢ (DEBTS) VS SỐ DƯ / TIẾT KIỆM (SAVINGS):
   - Khi người dùng hỏi về nợ (ví dụ: "Tôi đang nợ ai", "Ai nợ tôi", "Khoản nợ của tôi"):
     CHỈ ĐƯỢC trích xuất từ mục [SỔ NỢ & CHO VAY (DEBTS)]. Liệt kê rõ: Tên đối tác (ví dụ F88, HAISAISON), số tiền còn nợ, hạn trả.
   - TUYỆT ĐỐI KHÔNG dùng số dư tài khoản ngân hàng, thặng dư thu chi, hay số tiền tiết kiệm để trả lời cho câu hỏi về nợ.
   - Nếu trong sổ nợ không có khoản nào, trả lời rõ ràng: "Hiện tại bạn không có khoản nợ nào cần trả."
5. QUY TẮC SO SÁNH:
   - Khi so sánh giữa các tháng, phải dựa trên số liệu phân tích từng tháng ở mục [Phân tích & So sánh chi tiết từng tháng].
   - Không được tự ý kết luận các tháng giống hệt nhau nếu không có số liệu chứng minh từ từng tháng riêng biệt.
6. Trả lời đúng trọng tâm câu hỏi:
   - Khi người dùng hỏi con số: Nêu rõ ràng con số cụ thể kèm bối cảnh tự nhiên.
   - Khi người dùng hỏi giải thích hoặc lời khuyên: Giải thích tự nhiên, dễ hiểu, sinh động.
   - Chỉ đề cập thông tin liên quan trực tiếp đến câu hỏi hiện tại.
7. Nếu dữ liệu trong hệ thống chưa có hoặc không đủ để trả lời, hãy thông báo chân thực và nhẹ nhàng.

VÍ DỤ VĂN PHONG HỘI THOẠI (CHỈ HỌC CÁCH DIỄN ĐẠT THÂN THIỆN, KHÔNG DÙNG SỐ LIỆU CỐ ĐỊNH NÀY):
- Người dùng: "Tháng này tôi tiêu bao nhiêu?"
  Trợ lý: "Trong tháng này bạn đã chi tổng cộng [số tiền] rồi nhé. Khoản chi nhiều nhất là vào [tên danh mục]."
- Người dùng: "Khoản nào tôi chi nhiều nhất tháng này?"
  Trợ lý: "Khoản bạn chi nhiều nhất tháng này là [tên danh mục], hết khoảng [số tiền] đấy."
- Người dùng: "Tôi đang nợ ai?"
  Trợ lý: "Theo sổ nợ của bạn, bạn hiện đang có khoản nợ [tên đối tác] số tiền [số tiền] (hạn trả [ngày])."
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
    is_empty_period = "0 giao dịch" in user_facts_text or "KHÔNG CÓ GIAO DỊCH" in user_facts_text

    if is_en:
        lang_inst = "GUIDELINE: Respond fluently in English. Answer the current question directly with exact figures from Section 2."
    elif intent == "debt_advice":
        lang_inst = "HƯỚNG DẪN: Phân biệt rõ ai nợ ai: Mục 1 là bạn nợ người ta (bạn phải trả), Mục 2 là người ta nợ bạn (bạn được nhận tiền). Nếu người dùng hỏi 'tôi đang nợ ai', CHỈ nêu các khoản ở Mục 1 (bạn nợ F88). Tuyệt đối không nói bạn nợ các đối tác ở Mục 2 (HAISAISON nợ bạn, chứ không phải bạn nợ HAISAISON)."
    elif intent == "income_query":
        lang_inst = "HƯỚNG DẪN: Trả lời tự nhiên về số tiền THU NHẬP trong khoảng thời gian người dùng hỏi từ Dữ liệu tài chính ở mục 2. Nêu rõ con số thu nhập."
    elif intent == "balance_query":
        lang_inst = "HƯỚNG DẪN: Nêu rõ SỐ DƯ hiện tại từ Dữ liệu tài chính ở mục 2 một cách tự nhiên, rõ ràng."
    elif intent in ("spending_analysis", "expense_query"):
        if is_empty_period:
            lang_inst = "HƯỚNG DẪN: Trong khoảng thời gian này người dùng chưa có bất kỳ giao dịch chi tiêu nào (0 giao dịch). Hãy thông báo rõ ràng cho người dùng rằng chưa có giao dịch nào được ghi nhận trong thời gian này. Tuyệt đối không lấy số liệu tháng khác."
        else:
            lang_inst = "HƯỚNG DẪN: Hãy dùng các con số chi tiêu thực tế ở mục 2 để trả lời người dùng chi tiết và đầy đủ: nêu rõ tổng chi tiêu và các danh mục chi tiêu kèm số tiền. Tuyệt đối không nói là không có dữ liệu."
    elif intent == "comparison_query":
        lang_inst = "HƯỚNG DẪN: So sánh chi tiêu giữa các tháng dựa trên số liệu của từng tháng ở mục 2. Nêu rõ tổng chi tiêu và các danh mục chi tiêu của từng tháng theo đúng số liệu được cung cấp ở mục 2, sau đó so sánh mức tăng giảm."
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
