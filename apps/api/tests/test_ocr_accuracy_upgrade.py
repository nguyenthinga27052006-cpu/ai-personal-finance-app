from __future__ import annotations


def test_real_vat_invoice_with_lookup_code():
    """
    MASTER REAL CASE BUG REPRODUCTION & FIX:
    Invoice with:
    - Thành tiền trước thuế: 4.712.963
    - Tiền thuế VAT: 377.037
    - Cộng tiền thanh toán: 5.090.000
    - Amount in words: NĂM TRIỆU KHÔNG TRĂM CHÍN MƯƠI NGHÌN ĐỒNG
    - Mã của cơ quan thuế: 74589218491829
    - Mã tra cứu: 74589218491829
    Expected: Total MUST BE 5.090.000, NOT 745... and NOT 4.712.963!
    """
    from app.ai.receipt import LocalReceiptOCRProvider

    ocr_provider = LocalReceiptOCRProvider()
    
    # Simulate the layout-aware text lines from RapidOCR
    test_lines = [
        "CÔNG TY TNHH PHẦN MỀM VÀ CÔNG NGHỆ SAO MAI",
        "Tầng 5, Tòa nhà Tech Tower, Q. Cầu Giấy, Hà Nội",
        "Mã số thuế: 0108923456",
        "HÓA ĐƠN GIÁ TRỊ GIA TĂNG (TIỀN ĐIỆN TỬ)",
        "Ký hiệu: 1C26TBB - Số: 0045891",
        "Ngày 15 tháng 09 năm 2026",
        "1. Dịch vụ lưu trữ đám mây cao cấp   4.712.963",
        "Cộng tiền hàng: 4.712.963",
        "Thuế suất GTGT: 8%   Tiền thuế GTGT: 377.037",
        "Cộng tiền thanh toán: 5.090.000",
        "Số tiền viết bằng chữ: NĂM TRIỆU KHÔNG TRĂM CHÍN MƯƠI NGHÌN ĐỒNG",
        "Người bán hàng: Đã ký điện tử",
        "Mã của cơ quan thuế: 74589218491829",
        "Mã tra cứu hóa đơn: 74589218491829",
        "Tra cứu tại: https://hoadon.gdt.gov.vn",
    ]

    res = ocr_provider._parse_from_lines(test_lines)
    assert res["total"] == 5090000, f"Expected 5,090,000 but got {res['total']}"
    assert res["merchant"] == "CÔNG TY TNHH PHẦN MỀM VÀ CÔNG NGHỆ SAO MAI"
    assert res["date"] == "2026-09-15"
    assert res["validation_checks"]["subtotal_plus_vat_reconciled"] is True
    assert res["validation_checks"]["words_reconciled"] is True
    assert res["confidence"] >= 0.95


def test_vietnamese_amount_in_words_parser():
    from app.ai.receipt import VietnameseAmountInWordsParser

    parser = VietnameseAmountInWordsParser()
    assert parser.parse("NĂM TRIỆU KHÔNG TRĂM CHÍN MƯƠI NGHÌN ĐỒNG") == 5090000
    assert parser.parse("Bốn triệu bảy trăm mười hai nghìn chín trăm sáu mươi ba đồng") == 4712963
    assert parser.parse("Ba trăm bảy mươi bảy nghìn không trăm ba mươi bảy đồng") == 377037
    assert parser.parse("Năm trăm ba mươi bảy nghìn đồng") == 537000
    assert parser.parse("Một trăm năm mươi nghìn đồng chẵn") == 150000
    assert parser.parse("Hai mươi lăm nghìn đồng") == 25000
    assert parser.parse("Số tiền viết bằng chữ: Tám mươi nghìn đồng") == 80000
    assert parser.parse("Hai triệu bốn trăm năm mươi nghìn đồng") == 2450000
    assert parser.parse("Mười lăm triệu đồng") == 15000000


def test_restaurant_receipt_with_separate_cash_box():
    from app.ai.receipt import LocalReceiptOCRProvider

    ocr_provider = LocalReceiptOCRProvider()
    test_lines = [
        "QUAN AN THIEN TAN",
        "17-19 TON DAN F13Q4 TPHCM",
        "DT: 9407863-8259956",
        "13-11-2011 20:54",
        "BANSO: 47",
        "1 BUN SING 42,000",
        "1 MI GION X CHAY 37,000",
        "2 MI X GION N 80,000",
        "4 COM BAT BUU 172,000",
        "1 SUON CHIEN KDO 65,000",
        "1 HU TIEU N 40,000",
        "1 TOM LAN BOT 65,000",
        "2 PEPSI 16,000",
        "10 TRA DA 20,000",
        "TIEN MAT",
        "537,000",
        "CAM ON QUY KHACH HEN GAP LAI!",
    ]
    res = ocr_provider._parse_from_lines(test_lines)
    assert res["total"] == 537000
    assert "THIEN TAN" in res["merchant"].upper()
    assert res["date"] == "2011-11-13"


def test_supermarket_receipt_with_discount_and_subtotal():
    from app.ai.receipt import LocalReceiptOCRProvider

    ocr_provider = LocalReceiptOCRProvider()
    test_lines = [
        "SIÊU THỊ CO.OPMART NGUYỄN KIỆM",
        "571-573 Nguyễn Kiệm, P.9, Q.Phú Nhuận",
        "Mã số thuế: 0300588520",
        "HÓA ĐƠN BÁN LẺ",
        "Ngày: 20/09/2026 18:30",
        "1. Sữa tươi Vinamilk 1L 38,000",
        "2. Bánh mì sandwich 22,000",
        "3. Dầu ăn Simply 1L 65,000",
        "Tổng tiền hàng: 125,000",
        "Giảm giá voucher: -25,000",
        "Tổng cộng thanh toán: 100,000",
        "Tiền mặt: 100,000",
        "Điểm tích lũy: 120",
        "Số thẻ: 970422******1234",
    ]
    res = ocr_provider._parse_from_lines(test_lines)
    assert res["total"] == 100000
    assert "CO.OPMART" in res["merchant"].upper()


def test_negative_signals_reject_tax_code_and_phone():
    from app.ai.receipt import LocalReceiptOCRProvider

    ocr_provider = LocalReceiptOCRProvider()
    test_lines = [
        "NHÀ HÀNG HẢI SẢN BIỂN ĐÔNG",
        "Mã số thuế: 0314987654",
        "Hotline: 0908123456",
        "Số tài khoản VCB: 0071001234567",
        "Ngày: 12/08/2026",
        "Cơm chiên hải sản 120,000",
        "Cua rang me 450,000",
        "Khách phải trả: 570,000",
        "Mã tra cứu: 998877665544",
    ]
    res = ocr_provider._parse_from_lines(test_lines)
    # Must NOT pick tax code (0314987654), hotline (0908123456), bank account (0071001234567) or lookup code (998877665544)
    assert res["total"] == 570000


def test_low_confidence_when_total_uncertain():
    from app.ai.receipt import LocalReceiptOCRProvider, extract_receipt

    ocr_provider = LocalReceiptOCRProvider()
    # Badly degraded text with ambiguous numbers
    test_lines = [
        "Cửa hàng tạp hóa",
        "Số 12",
        "Giao dịch 45678",
        "Không rõ khoản mục",
    ]
    res = ocr_provider._parse_from_lines(test_lines)
    candidate = extract_receipt(res)
    # Low confidence must require review
    assert candidate.status == "LOW_CONFIDENCE"
    assert candidate.review_required is True
