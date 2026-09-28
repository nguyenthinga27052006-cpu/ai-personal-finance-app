from __future__ import annotations

from app.ai.receipt import LocalReceiptOCRProvider, extract_receipt

# =====================================================================
# 15 GROUND-TRUTH TEST BENCHMARK DATASET (Section XX)
# =====================================================================
BENCHMARK_DATASET = [
    {
        "id": "case_01_vat_cloud_service",
        "type": "clear",
        "category": "VAT invoice",
        "lines": [
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
            "Mã của cơ quan thuế: 74589218491829",
            "Mã tra cứu hóa đơn: 74589218491829",
            "Tra cứu tại: https://hoadon.gdt.gov.vn",
        ],
        "ground_truth": {
            "merchant": "CÔNG TY TNHH PHẦN MỀM VÀ CÔNG NGHỆ SAO MAI",
            "date": "2026-09-15",
            "total": 5090000,
            "subtotal": 4712963,
            "vat": 377037,
        },
    },
    {
        "id": "case_02_supermarket_coopmart",
        "type": "clear",
        "category": "supermarket receipt",
        "lines": [
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
        ],
        "ground_truth": {
            "merchant": "SIÊU THỊ CO.OPMART NGUYỄN KIỆM",
            "date": "2026-09-20",
            "total": 100000,
            "subtotal": 125000,
        },
    },
    {
        "id": "case_03_restaurant_thien_tan",
        "type": "clear",
        "category": "restaurant receipt",
        "lines": [
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
        ],
        "ground_truth": {
            "merchant": "QUAN AN THIEN TAN",
            "date": "2011-11-13",
            "total": 537000,
        },
    },
    {
        "id": "case_04_convenience_store_circle_k",
        "type": "clear",
        "category": "convenience store",
        "lines": [
            "CIRCLE K VIETNAM",
            "Cửa hàng Circle K Hai Bà Trưng",
            "Ngày: 05/08/2026 14:15",
            "1. Mì xào xúc xích trứng 25,000",
            "2. Nước tăng lực Sting dâu 12,000",
            "Cộng tiền thanh toán: 37,000",
            "Tiền mặt: 50,000",
            "Tiền thừa trả khách: 13,000",
        ],
        "ground_truth": {
            "merchant": "CIRCLE K VIETNAM",
            "date": "2026-08-05",
            "total": 37000,
        },
    },
    {
        "id": "case_05_pharmacy_long_chau",
        "type": "clear",
        "category": "pharmacy",
        "lines": [
            "NHÀ THUỐC FPT LONG CHÂU",
            "379 Hai Bà Trưng, P.8, Q.3, TP.HCM",
            "Mã số thuế: 0315228221",
            "PHIẾU XUẤT THUỐC KIÊM BÁN LẺ",
            "Ngày: 10/09/2026 09:30",
            "1. Thuốc Panadol Extra đỏ hộp 145,000",
            "2. Viên sủi Vitamin C 1000mg 85,000",
            "Tổng thanh toán: 230,000",
            "Mã hóa đơn: LC-2026-99882",
        ],
        "ground_truth": {
            "merchant": "NHÀ THUỐC FPT LONG CHÂU",
            "date": "2026-09-10",
            "total": 230000,
        },
    },
    {
        "id": "case_06_electronics_tgdd",
        "type": "clear",
        "category": "electronics",
        "lines": [
            "CÔNG TY CỔ PHẦN THẾ GIỚI DI ĐỘNG",
            "Mã số thuế: 0303217354",
            "HÓA ĐƠN ĐIỆN TỬ BÁN HÀNG",
            "Ngày 22 tháng 07 năm 2026",
            "1. Tai nghe Bluetooth AirPods Pro 2   8.324.074",
            "Tiền hàng trước thuế: 8.324.074",
            "Tiền thuế GTGT 8%: 665.926",
            "Tổng cộng tiền thanh toán: 8.990.000",
            "Số tiền bằng chữ: Tám triệu chín trăm chín mươi nghìn đồng",
            "Mã tra cứu: 9812739812738",
        ],
        "ground_truth": {
            "merchant": "CÔNG TY CỔ PHẦN THẾ GIỚI DI ĐỘNG",
            "date": "2026-07-22",
            "total": 8990000,
            "subtotal": 8324074,
            "vat": 665926,
        },
    },
    {
        "id": "case_07_shipping_viettel_post",
        "type": "clear",
        "category": "shipping",
        "lines": [
            "TỔNG CÔNG TY CỔ PHẦN BƯU CHÍNH VIETTEL",
            "Mã số thuế: 0104093672",
            "BIÊN NHẬN GỬI HÀNG",
            "Ngày: 19/08/2026",
            "Mã vận đơn: VP883921938",
            "Cước chuyển phát nhanh: 45,000",
            "Phụ phí xăng dầu: 4,500",
            "Thuế GTGT 10%: 4,950",
            "Tổng thanh toán: 54,450",
            "Hotline hỗ trợ: 19008095",
        ],
        "ground_truth": {
            "merchant": "TỔNG CÔNG TY CỔ PHẦN BƯU CHÍNH VIETTEL",
            "date": "2026-08-19",
            "total": 54450,
        },
    },
    {
        "id": "case_08_blurry_image_uncertain",
        "type": "blurry",
        "category": "blurry image",
        "lines": [
            "Tạp hóa Chú Bảy",
            "so 45 hem nho",
            "ma hd 9999",
            "tien thanh toan khong ro rang 8??00",
        ],
        "ground_truth": {
            "merchant": "Tạp hóa Chú Bảy",
            "uncertainty_expected": True,
        },
    },
    {
        "id": "case_09_skewed_highlands",
        "type": "clear",
        "category": "skewed image",
        "lines": [
            "HIGHLANDS COFFEE TÔ HIẾN THÀNH",
            "Ngày 02 tháng 09 năm 2026",
            "1. Phin sữa đá cỡ L 45,000",
            "2. Trà sen vàng cỡ L 55,000",
            "Cộng tiền hàng: 100,000",
            "Tổng tiền thanh toán: 100,000",
        ],
        "ground_truth": {
            "merchant": "HIGHLANDS COFFEE TÔ HIẾN THÀNH",
            "date": "2026-09-02",
            "total": 100000,
        },
    },
    {
        "id": "case_10_low_light_the_coffee_house",
        "type": "clear",
        "category": "low-light image",
        "lines": [
            "THE COFFEE HOUSE",
            "Võ Văn Tần, P.6, Q.3, TP.HCM",
            "Ngày: 30/08/2026 21:10",
            "1. Cà phê sữa đá 39,000",
            "2. Bánh mì chà bông phô mai 35,000",
            "Tổng cộng: 74,000",
            "Tiền mặt: 100,000",
        ],
        "ground_truth": {
            "merchant": "THE COFFEE HOUSE",
            "date": "2026-08-30",
            "total": 74000,
        },
    },
    {
        "id": "case_11_receipt_with_qr_and_bank",
        "type": "clear",
        "category": "receipt with QR",
        "lines": [
            "TRÀ SỮA PHÚC LONG",
            "Mã số thuế: 0302741912",
            "Ngày: 25/09/2026",
            "1. Trà sữa Phúc Long size L 60,000",
            "STK Vietcombank: 0071000998877",
            "Mã giao dịch QR: 00020101021238540010A0000007270124",
            "Tổng tiền thanh toán: 60,000",
        ],
        "ground_truth": {
            "merchant": "TRÀ SỮA PHÚC LONG",
            "date": "2026-09-25",
            "total": 60000,
        },
    },
    {
        "id": "case_12_receipt_with_long_tax_code",
        "type": "clear",
        "category": "receipt with long tax code",
        "lines": [
            "TỔNG CÔNG TY ĐIỆN LỰC MIỀN BẮC",
            "Mã số thuế: 0100100079001",
            "HÓA ĐƠN TIỀN ĐIỆN",
            "Ký hiệu: 1C26MNN - Số HĐ: 0984712",
            "Ngày: 15/08/2026",
            "Mã cơ quan thuế: 7459102847192841",
            "Tiền điện trước thuế: 1,850,000",
            "Tiền thuế GTGT 8%: 148,000",
            "Tổng tiền thanh toán: 1,998,000",
            "Mã khách hàng: PA01NN123456",
        ],
        "ground_truth": {
            "merchant": "TỔNG CÔNG TY ĐIỆN LỰC MIỀN BẮC",
            "date": "2026-08-15",
            "total": 1998000,
            "subtotal": 1850000,
            "vat": 148000,
        },
    },
    {
        "id": "case_13_bilingual_receipt",
        "type": "clear",
        "category": "bilingual receipt",
        "lines": [
            "STARBUCKS COFFEE VIETNAM",
            "Tax Code: 0311749823",
            "Date / Ngày: 18/09/2026",
            "1. Iced Caramel Macchiato Grande 95,000",
            "Grand Total / Tổng cộng: 95,000",
            "Cash / Tiền mặt: 100,000",
            "Change / Tiền thừa: 5,000",
        ],
        "ground_truth": {
            "merchant": "STARBUCKS COFFEE VIETNAM",
            "date": "2026-09-18",
            "total": 95000,
        },
    },
    {
        "id": "case_14_receipt_with_discount",
        "type": "clear",
        "category": "receipt with discount",
        "lines": [
            "NHÀ SÁCH FAHASA NGUYỄN HUỆ",
            "Mã số thuế: 0301121045",
            "Ngày: 05/09/2026",
            "1. Sách Thiết Kế Cuộc Đời 180,000",
            "2. Sách Tư Duy Nhanh Và Chậm 170,000",
            "Cộng tiền sách: 350,000",
            "Chiết khấu thành viên 10%: -35,000",
            "Cần thanh toán: 315,000",
            "Tiền mặt: 500,000",
        ],
        "ground_truth": {
            "merchant": "NHÀ SÁCH FAHASA NGUYỄN HUỆ",
            "date": "2026-09-05",
            "total": 315000,
        },
    },
    {
        "id": "case_15_vat_fuel_petrolimex",
        "type": "clear",
        "category": "receipt with VAT",
        "lines": [
            "TẬP ĐOÀN XĂNG DẦU VIỆT NAM (PETROLIMEX)",
            "Cửa hàng Xăng dầu Số 01",
            "Mã số thuế: 0100107624",
            "HÓA ĐƠN ĐIỆN TỬ BÁN HÀNG",
            "Ngày: 22/09/2026",
            "Xăng RON 95-III: 609,330",
            "Tiền hàng trước thuế: 609,330",
            "Tiền thuế GTGT 10%: 60,933",
            "Cộng tiền thanh toán: 670,263",
            "Số tiền viết bằng chữ: Sáu trăm bảy mươi nghìn hai trăm sáu mươi ba đồng",
            "Mã cơ quan thuế cấp: 74581928471928",
        ],
        "ground_truth": {
            "merchant": "TẬP ĐOÀN XĂNG DẦU VIỆT NAM (PETROLIMEX)",
            "date": "2026-09-22",
            "total": 670263,
            "subtotal": 609330,
            "vat": 60933,
        },
    },
]


def test_run_full_receipt_benchmark_suite():
    """
    Executes the 15 receipt test suite and computes strict accuracy metrics (Section XXI):
    - Total Exact Match Rate
    - Merchant Exact Match Rate
    - Date Exact Match Rate
    - Total Absolute Error
    - Total Relative Error
    - Blurry / Uncertainty Detection Rate
    """
    provider = LocalReceiptOCRProvider()

    clear_cases = [c for c in BENCHMARK_DATASET if c["type"] == "clear"]
    blurry_cases = [c for c in BENCHMARK_DATASET if c["type"] == "blurry"]

    total_exact_matches = 0
    merchant_exact_matches = 0
    date_exact_matches = 0
    total_abs_errors: list[float] = []
    total_rel_errors: list[float] = []

    print("\n" + "=" * 65)
    print("AI PERSONAL FINANCE — RECEIPT OCR ACCURACY BENCHMARK")
    print("=" * 65)

    for case in clear_cases:
        res = provider._parse_from_lines(case["lines"])
        gt = case["ground_truth"]

        expected_total = gt["total"]
        actual_total = res["total"]

        is_total_match = (actual_total == expected_total)
        if is_total_match:
            total_exact_matches += 1

        abs_err = abs(actual_total - expected_total)
        rel_err = abs_err / max(1, expected_total)
        total_abs_errors.append(abs_err)
        total_rel_errors.append(rel_err)

        is_merchant_match = (res["merchant"].strip().upper() == gt["merchant"].strip().upper())
        if is_merchant_match:
            merchant_exact_matches += 1

        is_date_match = (res["date"] == gt["date"])
        if is_date_match:
            date_exact_matches += 1

        print(
            f"[{case['id']}] {case['category']:<24} -> Total: Expected={expected_total:>9,d} | Actual={actual_total:>9,d} | Match={str(is_total_match):<5} | Conf={res['confidence']:.2f}"
        )

    # Blurry / Uncertainty verification (Section XXII)
    blurry_detected = 0
    for case in blurry_cases:
        res = provider._parse_from_lines(case["lines"])
        candidate = extract_receipt(res)
        is_uncertain = (candidate.status == "LOW_CONFIDENCE" and candidate.review_required is True)
        if is_uncertain:
            blurry_detected += 1
        print(
            f"[{case['id']}] {case['category']:<24} -> Status={candidate.status} | ReviewRequired={candidate.review_required} | Detected={is_uncertain}"
        )

    # Compute Metrics
    num_clear = len(clear_cases)
    total_exact_match_rate = total_exact_matches / num_clear
    merchant_match_rate = merchant_exact_matches / num_clear
    date_match_rate = date_exact_matches / num_clear
    mean_abs_error = sum(total_abs_errors) / num_clear
    mean_rel_error = sum(total_rel_errors) / num_clear
    uncertainty_detection_rate = blurry_detected / len(blurry_cases)

    print("\n" + "=" * 65)
    print("ACCURACY METRICS SUMMARY (Section XXI)")
    print("=" * 65)
    print(f"Clear Test Cases Total           : {num_clear}")
    print(f"Total Exact Match Rate           : {total_exact_match_rate * 100:.2f}% ({total_exact_matches}/{num_clear})")
    print(f"Merchant Exact Match Rate        : {merchant_match_rate * 100:.2f}% ({merchant_exact_matches}/{num_clear})")
    print(f"Date Exact Match Rate            : {date_match_rate * 100:.2f}% ({date_exact_matches}/{num_clear})")
    print(f"Mean Total Absolute Error (MAE)  : {mean_abs_error:,.2f} VND")
    print(f"Mean Total Relative Error (MRE)  : {mean_rel_error * 100:.4f}%")
    print(f"Blurry Uncertainty Detection Rate: {uncertainty_detection_rate * 100:.2f}% ({blurry_detected}/{len(blurry_cases)})")
    print("=" * 65)

    assert total_exact_match_rate == 1.0, f"Expected 100% Total Exact Match on clear cases, got {total_exact_match_rate * 100}%"
    assert uncertainty_detection_rate == 1.0, f"Expected 100% Uncertainty Detection on blurry cases, got {uncertainty_detection_rate * 100}%"
