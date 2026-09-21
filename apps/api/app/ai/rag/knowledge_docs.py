from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    title: str
    content: str
    source: str
    topic: str
    category: str = "financial_education"
    language: str = "vi"
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def to_metadata(self) -> dict[str, Any]:
        meta = {
            "document_id": self.doc_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "source": self.source,
            "topic": self.topic,
            "category": self.category,
            "language": self.language,
            "version": self.version,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active": True,
        }
        meta.update(self.extra_metadata)
        return meta


SEED_KNOWLEDGE_DOCUMENTS: list[KnowledgeDocument] = [
    KnowledgeDocument(
        doc_id="rule_50_30_20",
        title="Quy tắc Quản lý Tài chính 50/30/20",
        topic="budgeting",
        category="financial_education",
        source="Quy tắc 50/30/20 (Cẩm nang Tài chính)",
        content=(
            "Quy tắc 50/30/20 là phương pháp phân bổ thu nhập ròng hàng tháng thành 3 nhóm chính: "
            "1. 50% Thu nhập dành cho Nhu cầu thiết yếu (Needs) như tiền nhà, ăn uống cơ bản, hóa đơn điện nước, đi lại. "
            "2. 30% Thu nhập dành cho Mong muốn cá nhân (Wants) như mua sắm đồ công nghệ, giải trí, ăn tiệm, du lịch. "
            "3. 20% Thu nhập dành cho Mục tiêu tài chính & Tiết kiệm (Savings/Debt) như quỹ khẩn cấp, đầu tư tích sản, trả nợ. "
            "Khi chi tiêu vượt quá 50% cho nhu cầu thiết yếu, bạn nên cắt giảm nhóm mong muốn cá nhân trước để duy trì tỷ lệ tiết kiệm 20%."
        ),
    ),
    KnowledgeDocument(
        doc_id="emergency_fund",
        title="Hướng dẫn Xây dựng Quỹ Khẩn Cấp",
        topic="saving",
        category="financial_education",
        source="Cẩm nang Tiết kiệm Cá nhân",
        content=(
            "Quỹ khẩn cấp là khoản tiền dự phòng dành cho các tình huống bất ngờ như ốm đau, mất việc hoặc hỏng hóc thiết bị quan trọng. "
            "Quy mô tối ưu của quỹ khẩn cấp là từ 3 đến 6 tháng chi phí thiết yếu tối thiểu. "
            "Khoản tiền này nên được gửi ở các tài khoản thanh toán hoặc tiết kiệm linh hoạt có thể rút ngay khi cần. "
            "Bắt đầu xây dựng quỹ khẩn cấp bằng cách tự động trích 10-15% thu nhập mỗi khi nhận lương."
        ),
    ),
    KnowledgeDocument(
        doc_id="debt_snowball_avalanche",
        title="Phương pháp Trả nợ Snowball và Avalanche",
        topic="debt",
        category="financial_education",
        source="Cẩm nang Quản lý Nợ",
        content=(
            "Có hai phương pháp trả nợ hiệu quả nhất: "
            "1. Phương pháp Tuyết lăn (Snowball): Trả hết các khoản nợ từ nhỏ nhất đến lớn nhất. Giúp tạo động lực tâm lý nhanh chóng khi từng khoản nợ nhỏ biến mất. "
            "2. Phương pháp Tuyết lở (Avalanche): Tập trung trả khoản nợ có lãi suất cao nhất trước. Giúp tiết kiệm tổng số tiền lãi phải trả nhiều nhất. "
            "Nguyên tắc chung: Luôn duy trì trả khoản tối thiểu cho tất cả các nợ, và dồn tiền thặng dư vào nợ mục tiêu."
        ),
    ),
    KnowledgeDocument(
        doc_id="saving_tips_eating_out",
        title="Mẹo Tối ưu Chi phí Ăn uống và Mua sắm",
        topic="saving",
        category="saving_tips",
        source="Cẩm nang Tiết kiệm AI Vietnam",
        content=(
            "Chi tiêu cho ăn uống ngoài và cà phê thường chiếm tỷ trọng lớn trong ngân sách hàng tháng. "
            "Mẹo cắt giảm hiệu quả mà không giảm chất lượng sống: "
            "1. Quy tắc 24 giờ trước khi mua hàng ngẫu hứng: Đợi 24h để xem nhu cầu đó có thật sự cần thiết. "
            "2. Đặt ngân sách tuần cho việc ăn ngoài thay vì đặt theo tháng. "
            "3. Lập danh sách mua sắm trước khi đi siêu thị để tránh mua thêm sản phẩm quảng cáo. "
            "4. Đặt hạn mức chi tiêu tự động (Budget Limit) cho danh mục Ăn uống và nhận cảnh báo khi vượt 80% hạn mức."
        ),
    ),
    KnowledgeDocument(
        doc_id="investment_basics",
        title="Nguyên tắc Đầu tư Tích sản Dài hạn",
        topic="investment",
        category="financial_education",
        source="Cẩm nang Đầu tư Tài chính Cá nhân",
        content=(
            "Đầu tư tích sản là việc trích định kỳ một phần thặng dư hàng tháng vào các tài sản tài chính an toàn như chứng chỉ quỹ chỉ số, vàng hoặc tiền gửi tiết kiệm. "
            "Nguyên tắc vàng: Chỉ sử dụng tiền nhàn rỗi sau khi đã hoàn thành quỹ khẩn cấp 3-6 tháng. "
            "Không bỏ tất cả trứng vào một giỏ và thực hiện chiến lược bình quân giá (DCA) để giảm rủi ro thị trường."
        ),
    ),
    KnowledgeDocument(
        doc_id="app_faq_features",
        title="Hướng dẫn Sử dụng Tính năng Ứng dụng Tài chính AI",
        topic="faq",
        category="system_policy",
        source="Hướng dẫn Ứng dụng AI Personal Finance",
        content=(
            "Ứng dụng AI Personal Finance hỗ trợ người dùng theo dõi tài khoản, phân loại giao dịch tự động, lập ngân sách chi tiêu và theo dõi mục tiêu tiết kiệm. "
            "Tính năng AI Assistant cho phép đặt câu hỏi bằng tiếng Việt như 'Tôi tiêu nhiều nhất ở đâu?', 'Có đủ tiền mua laptop không?'. "
            "Mọi dữ liệu tài chính của người dùng được bảo mật tuyệt đối, chỉ hiển thị riêng cho tài khoản cá nhân đã xác thực."
        ),
    ),
]
