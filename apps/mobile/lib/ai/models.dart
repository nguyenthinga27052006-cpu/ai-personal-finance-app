class AIQueryResult {
  const AIQueryResult({
    required this.status,
    required this.answer,
    this.intent,
    this.source,
    this.message,
  });

  final String status;
  final String answer;
  final String? intent;
  final String? source;
  final String? message;

  factory AIQueryResult.fromJson(Map<String, dynamic> json) => AIQueryResult(
        status: json['status'] as String,
        answer: json['answer'] as String,
        intent: json['intent'] as String?,
        source: json['source'] as String?,
        message: json['message'] as String?,
      );
}

class AISpendingResult {
  const AISpendingResult({required this.status, required this.answer});

  final String status;
  final String answer;

  factory AISpendingResult.fromJson(Map<String, dynamic> json) {
    final output = json['output'] as Map<String, dynamic>;
    return AISpendingResult(
      status: output['status'] as String,
      answer: output['answer'] as String,
    );
  }
}
