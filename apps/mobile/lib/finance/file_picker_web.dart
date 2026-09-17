// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

void pickWebImageFile(Function(String fileName, String base64Data) onSelected) {
  final uploadInput = html.FileUploadInputElement()..accept = 'image/*';
  uploadInput.click();
  uploadInput.onChange.listen((event) {
    final files = uploadInput.files;
    if (files != null && files.isNotEmpty) {
      final file = files[0];
      final reader = html.FileReader();
      reader.readAsDataUrl(file);
      reader.onLoadEnd.listen((event) {
        final result = reader.result as String;
        onSelected(file.name, result);
      });
    }
  });
}
