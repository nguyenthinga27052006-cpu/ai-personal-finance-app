import 'package:flutter/material.dart';

import '../auth/api_client.dart';
import 'models.dart';

class AIScreen extends StatefulWidget {
  const AIScreen({super.key, required this.gateway});

  final AIGateway gateway;

  @override
  State<AIScreen> createState() => _AIScreenState();
}

class _AIScreenState extends State<AIScreen> {
  final controller = TextEditingController();
  AIQueryResult? result;
  String? error;
  bool loading = false;

  static const suggestions = [
    'How much did I spend this month?',
    'What is my current balance?',
    'How much income did I receive this month?',
    'Show my budget status',
  ];

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> ask(String question) async {
    final value = question.trim();
    if (value.isEmpty) return;
    setState(() {
      loading = true;
      error = null;
      result = null;
    });
    try {
      final response = await widget.gateway.query(value);
      if (!mounted) return;
      setState(() => result = response);
    } catch (exception) {
      if (!mounted) return;
      setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Ask your finances', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text('Answers are grounded in your current financial records.'),
          const SizedBox(height: 16),
          TextField(
            controller: controller,
            onSubmitted: ask,
            decoration: InputDecoration(
              labelText: 'Ask a financial question',
              suffixIcon: IconButton(
                onPressed: loading ? null : () => ask(controller.text),
                icon: const Icon(Icons.send),
                tooltip: 'Ask',
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text('Suggested questions', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: suggestions
                .map((question) => ActionChip(
                      label: Text(question),
                      onPressed: loading ? null : () {
                        controller.text = question;
                        ask(question);
                      },
                    ))
                .toList(),
          ),
          const SizedBox(height: 24),
          if (loading) const Center(child: CircularProgressIndicator()),
          if (error != null) _StateCard(label: 'Provider or network error', detail: error!),
          if (!loading && error == null && result == null)
            const _StateCard(label: 'Ready', detail: 'Choose a suggested question or ask your own.'),
          if (result case final response?) _StateCard(
            label: response.status,
            detail: response.answer,
            source: response.source,
          ),
        ],
      );
}

class _StateCard extends StatelessWidget {
  const _StateCard({required this.label, required this.detail, this.source});

  final String label;
  final String detail;
  final String? source;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(detail),
              if (source != null) ...[
                const SizedBox(height: 8),
                Text('Source: $source', style: Theme.of(context).textTheme.labelSmall),
              ],
            ],
          ),
        ),
      );
}
