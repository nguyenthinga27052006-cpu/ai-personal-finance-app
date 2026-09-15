import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../auth/api_client.dart';
import '../settings/settings_controller.dart';

class AIMessageItem {
  const AIMessageItem({
    required this.isUser,
    required this.text,
    this.source,
    this.status,
  });

  final bool isUser;
  final String text;
  final String? source;
  final String? status;
}

class AIScreen extends StatefulWidget {
  const AIScreen({super.key, required this.gateway});

  final AIGateway gateway;

  @override
  State<AIScreen> createState() => _AIScreenState();
}

class _AIScreenState extends State<AIScreen> {
  final controller = TextEditingController();
  final List<AIMessageItem> messages = [];
  String? error;
  bool loading = false;

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> ask(String question, {String? language}) async {
    final value = question.trim();
    if (value.isEmpty) return;
    controller.clear();
    setState(() {
      messages.add(AIMessageItem(isUser: true, text: value));
      loading = true;
      error = null;
    });
    try {
      final response = await widget.gateway.query(value, language: language);
      if (!mounted) return;
      setState(() {
        messages.add(AIMessageItem(
          isUser: false,
          text: response.answer,
          source: response.source,
          status: response.status,
        ));
      });
    } catch (exception) {
      if (!mounted) return;
      setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  void clearHistory() {
    setState(() {
      messages.clear();
      error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final suggestions = settings.language == AppLanguage.vi
        ? const [
            'Số dư hiện tại của tôi là bao nhiêu?',
            'Tháng này tôi đã chi tiêu bao nhiêu?',
            'Thu nhập tháng này của tôi là bao nhiêu?',
            'Kiểm tra tình hình ngân sách & mục tiêu',
            'Cho tôi lời khuyên tiết kiệm theo quy tắc 50/30/20',
          ]
        : const [
            'What is my current balance?',
            'How much did I spend this month?',
            'What is my income this month?',
            'Check my budget and goals status',
            'Give me savings advice using the 50/30/20 rule',
          ];

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(settings.tr('ai_header_title'), style: Theme.of(context).textTheme.titleLarge),
                  Text(
                    settings.tr('ai_header_subtitle'),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                ],
              ),
              if (messages.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.delete_sweep_outlined),
                  tooltip: settings.tr('ai_clear'),
                  onPressed: clearHistory,
                ),
            ],
          ),
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: suggestions
                .map((question) => Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ActionChip(
                        label: Text(question, style: const TextStyle(fontSize: 12)),
                        onPressed: loading ? null : () => ask(question, language: settings.language.name),
                      ),
                    ))
                .toList(),
          ),
        ),
        const Divider(height: 16),
        Expanded(
          child: messages.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      settings.tr('ai_empty_hint'),
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.grey),
                    ),
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final item = messages[index];
                    return Align(
                      alignment: item.isUser ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(12),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.8,
                        ),
                        decoration: BoxDecoration(
                          color: item.isUser
                              ? Theme.of(context).colorScheme.primaryContainer
                              : Theme.of(context).colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  item.isUser ? settings.tr('ai_user_label') : settings.tr('ai_assistant_label'),
                                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                                ),
                                if (item.status != null)
                                  Text(
                                    item.status!,
                                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                          color: Colors.green.shade800,
                                          fontWeight: FontWeight.bold,
                                        ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            item.isUser
                                ? SelectableText(item.text)
                                : MarkdownBody(
                                    data: item.text,
                                    selectable: true,
                                  ),
                            if (item.source != null && item.source!.isNotEmpty) ...[
                              const SizedBox(height: 6),
                              Text(
                                '${settings.tr('ai_source_label')} ${item.source}',
                                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                      color: Colors.grey.shade700,
                                    ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        if (loading)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: SizedBox(
              height: 20,
              width: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ),
        if (error != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Text(
              'Error: $error',
              style: const TextStyle(color: Colors.red, fontSize: 12),
            ),
          ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  onSubmitted: loading ? null : (val) => ask(val, language: settings.language.name),
                  decoration: InputDecoration(
                    labelText: settings.tr('ai_input_hint'),
                    hintText: settings.tr('ai_input_hint'),
                    border: const OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: loading ? null : () => ask(controller.text, language: settings.language.name),
                icon: const Icon(Icons.send),
                tooltip: settings.tr('ai_send'),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
