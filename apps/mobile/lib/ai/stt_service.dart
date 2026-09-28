import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

/// UX States for Voice/STT interaction per Master Implementation Prompt Section VIII.
enum VoiceState {
  idle,
  listening,
  transcribing,
  transcriptReady,
  sending,
  aiResponding,
  completed,
  error,
}

/// Metadata payload for STT recognition results per Section VII.
class STTResult {
  const STTResult({
    required this.text,
    required this.isFinal,
    this.confidence,
    this.language = 'vi',
    this.provider = 'native_speech_to_text',
    this.model = 'system_stt',
    this.durationMs = 0,
  });

  final String text;
  final bool isFinal;
  final double? confidence;
  final String language;
  final String provider;
  final String model;
  final int durationMs;
}

/// Abstraction interface for Speech-to-Text provider per Section VII.
abstract interface class SpeechToTextProvider {
  Future<bool> initialize({
    required void Function(String status) onStatus,
    required void Function(String error) onError,
  });
  Future<void> listen({
    required String requestedLocale,
    required void Function(STTResult result) onResult,
  });
  Future<void> stop();
  Future<void> cancel();
  bool get isListening;
}

/// Robust SpeechToText provider supporting Android, iOS, and Web Speech API
/// with explicit BCP 47 Vietnamese (`vi-VN`) locale negotiation.
class MobileAndWebSpeechProvider implements SpeechToTextProvider {
  MobileAndWebSpeechProvider({stt.SpeechToText? speech})
      : _speech = speech ?? stt.SpeechToText();

  final stt.SpeechToText _speech;
  bool _initialized = false;
  List<stt.LocaleName> _availableLocales = [];

  @override
  bool get isListening => _speech.isListening;

  @override
  Future<bool> initialize({
    required void Function(String status) onStatus,
    required void Function(String error) onError,
  }) async {
    try {
      final available = await _speech.initialize(
        onStatus: onStatus,
        onError: (errorNotification) {
          debugPrint('[STT Provider] Error: ${errorNotification.errorMsg}, permanent=${errorNotification.permanent}');
          onError(errorNotification.errorMsg);
        },
      );
      if (available) {
        _initialized = true;
        try {
          _availableLocales = await _speech.locales();
          debugPrint('[STT Provider] Initialized successfully. Available locales count: ${_availableLocales.length}');
        } catch (e) {
          debugPrint('[STT Provider] Could not load locales list: $e');
        }
      }
      return available;
    } catch (e) {
      debugPrint('[STT Provider] Initialization exception: $e');
      onError(e.toString());
      return false;
    }
  }

  /// Negotiate the best locale identifier from device/browser capabilities.
  /// Web Speech API strictly requires BCP 47 ('vi-VN' with hyphen).
  /// Mobile native might have 'vi_VN' or 'vi-VN'.
  String resolveLocale(String requestedLang) {
    final langLower = requestedLang.toLowerCase();
    final isEn = langLower == 'en' || langLower == 'english';
    final requestedTag = isEn ? 'en-US' : 'vi-VN';
    final targetPrefix = isEn ? 'en' : 'vi';

    if (_availableLocales.isEmpty) {
      debugPrint('[STT Provider] No locale list available, using standard BCP 47 tag: $requestedTag');
      return requestedTag;
    }

    // 1. Try to find exact standard BCP 47 match (e.g. 'vi-VN')
    for (final loc in _availableLocales) {
      final normalizedId = loc.localeId.replaceAll('_', '-').toLowerCase();
      if (normalizedId == requestedTag.toLowerCase()) {
        debugPrint('[STT Provider] Found exact match: ${loc.localeId} (${loc.name})');
        return loc.localeId;
      }
    }

    // 2. Try prefix match (e.g. 'vi' or any 'vi_*')
    for (final loc in _availableLocales) {
      final normalizedId = loc.localeId.replaceAll('_', '-').toLowerCase();
      if (normalizedId.startsWith(targetPrefix)) {
        debugPrint('[STT Provider] Found prefix match: ${loc.localeId} (${loc.name})');
        return loc.localeId;
      }
    }

    // 3. Fallback to standard BCP 47 tag
    debugPrint('[STT Provider] No prefix match found in ${_availableLocales.length} locales, falling back to $requestedTag');
    return requestedTag;
  }

  @override
  Future<void> listen({
    required String requestedLocale,
    required void Function(STTResult result) onResult,
  }) async {
    if (!_initialized) {
      final ok = await initialize(onStatus: (_) {}, onError: (_) {});
      if (!ok) return;
    }

    final actualLocaleId = resolveLocale(requestedLocale);
    final startTime = DateTime.now();

    debugPrint(
      '[STT Provider] Start listening. requested_locale="$requestedLocale", actual_locale="$actualLocaleId"',
    );

    await _speech.listen(
      localeId: actualLocaleId,
      listenMode: stt.ListenMode.dictation,
      partialResults: true,
      cancelOnError: false,
      onResult: (speechResult) {
        final duration = DateTime.now().difference(startTime).inMilliseconds;
        final text = speechResult.recognizedWords.trim();
        debugPrint(
          '[STT Provider] recognized_text="$text", is_final=${speechResult.finalResult}, confidence=${speechResult.confidence}, duration=${duration}ms',
        );
        onResult(
          STTResult(
            text: text,
            isFinal: speechResult.finalResult,
            confidence: speechResult.hasConfidenceRating ? speechResult.confidence : null,
            language: requestedLocale.startsWith('en') ? 'en' : 'vi',
            provider: kIsWeb ? 'web_speech_api' : 'native_mobile_stt',
            model: actualLocaleId,
            durationMs: duration,
          ),
        );
      },
    );
  }

  @override
  Future<void> stop() async {
    try {
      await _speech.stop();
    } catch (e) {
      debugPrint('[STT Provider] Error on stop: $e');
    }
  }

  @override
  Future<void> cancel() async {
    try {
      await _speech.cancel();
    } catch (e) {
      debugPrint('[STT Provider] Error on cancel: $e');
    }
  }
}
