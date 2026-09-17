# 📱 TÀI LIỆU BÁO CÁO & BẢO VỆ CHUYÊN SÂU: THÀNH VIÊN 1 - MOBILE & WEB FRONTEND LEAD

---

## 👨‍💻 I. THÔNG TIN THÀNH VIÊN & NỀN TẢNG CÔNG NGHỆ
* **Họ và tên**: Thành viên 1 (Frontend Developer Lead)
* **Vai trò**: Trưởng nhóm Kiến trúc & Phát triển Giao diện Người dùng (Mobile Client & Web Platform)
* **Ngôn ngữ lập trình & Framework**: 
  - **Language**: **Dart 3.13** (Ngôn ngữ biên dịch AOT & JIT, hỗ trợ Sound Null Safety, Strong Typing, Asynchronous Programming với `Future` và `Stream`).
  - **Framework**: **Flutter 3.47.1** (Engine Skia/Impeller render trực tiếp ra Canvas đồ họa).
  - **State Management**: **Provider Pattern** (Dựa trên `InheritedWidget` và `ChangeNotifier`).
  - **Giao thức Truyền dữ liệu Real-time**: **HTTP SSE (Server-Sent Events)** lắng nghe qua `StreamSubscription`.
  - **Bảo mật Bộ nhớ Cục bộ**: `flutter_secure_storage` (Keychain trên iOS, EncryptedSharedPreferences trên Android, Secure Browser Storage trên Web).

---

## 🎯 II. CHI TIẾT KỸ THUẬT & NHIỆM VỤ ĐÃ THỰC HIỆN

### 1. Kiến trúc Mã nguồn Frontend (Clean Architecture Layout)
```
apps/mobile/lib/
├── core/                # Utility, Constant, Theme, Network Client, Security Storage
├── models/              # Data Models (User, Account, Transaction, Budget, AIChatMessage)
├── providers/           # State Management (AuthProvider, TransactionProvider, AIChatProvider)
├── screens/             # UI Views (LoginScreen, HomeScreen, AnalyticsScreen, AIChatScreen)
└── widgets/             # Reusable UI Elements (CustomCard, ChartWidget, StreamingTextWidget)
```

### 2. Nhiệm vụ Chi tiết & Xử lý Kỹ thuật
- **Quản lý Phiên đăng nhập & Bảo mật Token**:
  - Lưu cặp `access_token` và `refresh_token` vào bộ nhớ mã hóa thiết bị qua `flutter_secure_storage`.
  - Xây dựng Interceptor trong HTTP Client: Tự động đính kèm `Authorization: Bearer <token>` vào mọi Request. Nếu API trả về HTTP `401 Unauthorized`, tự động gọi `/api/v1/auth/refresh` lấy Token mới và gửi lại Request ban đầu mà người dùng không hề hay biết.
- **Xử lý Phản hồi Real-time từ AI Chatbot (SSE Stream Handling)**:
  - Khi người dùng gửi câu hỏi tới AI, ứng dụng không dùng Polling (hỏi dồn) mà mở kết nối **Server-Sent Events (SSE)**.
  - Sử dụng `http.Client()` đọc luồng dữ liệu `response.stream` theo từng chunk byte.
  - Giải mã utf-8 từng dòng `data: {"token": "..."}`, đẩy chuỗi ký tự mới vào `AIChatProvider` và gọi `notifyListeners()`. UI lập tức re-render tạo hiệu ứng chữ gõ sinh động.
- **Báo cáo Thống kê Đồ họa (Data Visualization)**:
  - Tích hợp thư viện biểu đồ render mượt mà với dữ liệu động từ API (Pie Chart cho phân bổ danh mục chi tiêu, Bar Chart cho so sánh Thu vs Chi).

---

## ❓ III. BỘ CÂU HỎI & ĐÁP BẢO VỆ KÍN KẼ (DÀNH CHO HỘI ĐỒNG/GIẢNG VIÊN)

### ❓ Câu 1: Tại sao bạn chọn Flutter & Dart thay vì React Native / JavaScript? Ngôn ngữ Dart có điểm mạnh gì?
> **Trả lời kín kẽ**: 
> 1. **Kiến trúc Rendering**: React Native phải đi qua chiếc cầu nối **JavaScript Bridge** để chuyển đổi component JS sang Native Widget của OS, gây nghẽn hiệu năng khi render biểu đồ hoặc danh sách dài. Flutter sở hữu Engine đồ họa riêng (Skia/Impeller), biên dịch code Dart trực tiếp ra ARM Native Code, vẽ trực tiếp lên màn hình với tốc độ **60-120 FPS**.
> 2. **Ngôn ngữ Dart**: Hỗ trợ cả hai cơ chế biên dịch: **JIT (Just-In-Time)** cho tính năng Hot Reload giúp phát triển nhanh, và **AOT (Ahead-Of-Time)** biên dịch ra mã máy nguyên bản khi Release giúp tối ưu dung lượng và tốc độ thực thi.

### ❓ Câu 2: Tại sao dự án chọn Provider làm State Management mà không dùng BLoC hay Riverpod?
> **Trả lời kín kẽ**: 
> - **Nguyên lý thiết kế**: Provider dựa trên cơ chế `InheritedWidget` nguyên bản của Flutter, kết hợp `ChangeNotifier` để thông báo cho đúng Widget cần cập nhật (`Consumer` hoặc `Selector`).
> - **Lý do chọn**: Dự án tập trung vào độ tin cậy và tốc độ phát triển. Provider đáp ứng hoàn hảo tính chất tách biệt giữa UI và Business Logic, không bị hiện tượng dư thừa mã nguồn (Boilerplate code) như BLoC, giúp mã nguồn sạch sẽ, dễ bảo trì và dễ viết Unit Test cho Provider.

### ❓ Câu 3: Làm thế nào ứng dụng hiển thị từng từ (Streaming) khi AI trả lời mà không bị giật lag giao diện?
> **Trả lời kín kẽ**: 
> - Chúng tôi sử dụng cơ chế **Asynchronous Stream handling** của Dart.
> - HTTP Connection mở luồng nhận dữ liệu dưới dạng `Stream<List<int>>`. Mỗi khi có gói tin nhỏ tới, stream listener sẽ parse JSON token và chỉ thực hiện update lại duy nhất Widget văn bản câu trả lời bằng `Selector<AIChatProvider, String>`, không làm re-render toàn bộ màn hình Chat, giúp chỉ số CPU và RAM của ứng dụng giữ mức cực thấp.

### ❓ Câu 4: Việc lưu trữ JWT Token dưới Client được bảo mật chống bị hacker lấy cắp ra sao?
> **Trả lời kín kẽ**: 
> - Chúng tôi **tuyệt đối không** lưu token dưới dạng plain text trong `SharedPreferences` (Android) hay `localStorage` (Web).
> - Dự án dùng `flutter_secure_storage`:
>   - **Trên iOS**: Lưu trong **Apple Keychain** mã hóa bằng phần cứng Secure Enclave.
>   - **Trên Android**: Mã hóa bằng **Android Keystore System** với thuật toán AES-256 GCM.
>   - **Trên Web**: Lưu trữ mã hóa theo phiên làm việc bảo mật.

### ❓ Câu 5: Nếu Backend AI phản hồi quá lâu hoặc bị ngắt kết nối mạng giữa chừng khi đang Stream thì Frontend xử lý thế nào?
> **Trả lời kín kẽ**: 
> - Chúng tôi cài đặt **Client-side Connection Timeout** (15s cho API thường, 60s cho Stream AI).
> - Nếu kết nối bị đứt giữa chừng, `Stream.onError` sẽ bắt sự kiện, hiển thị Icon cảnh báo *"Mất kết nối với AI"* kèm nút *"Thử lại (Retry)"*, đồng thời bảo lưu phần văn bản AI đã nhận được trước đó trong State chứ không xóa sạch dữ liệu trên màn hình.
