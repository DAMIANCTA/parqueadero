import 'dart:typed_data';

import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';

import '../models/app_models.dart';

class ImagePreparationService {
  const ImagePreparationService();

  Future<LocalEvidenceDraft> buildDraft({
    required XFile file,
    required String label,
  }) async {
    final sourceBytes = await file.readAsBytes();
    final prepared = _normalizeToJpeg(sourceBytes);
    final normalizedFileName = prepared.wasNormalized ? _normalizeFileName(file.name) : file.name;

    return LocalEvidenceDraft(
      label: label,
      fileName: normalizedFileName,
      bytes: prepared.bytes,
      contentType: prepared.wasNormalized ? 'image/jpeg' : 'application/octet-stream',
      isMock: false,
    );
  }

  _PreparedImage _normalizeToJpeg(Uint8List sourceBytes) {
    try {
      final decoded = img.decodeImage(sourceBytes);
      if (decoded == null) {
        return _PreparedImage(bytes: sourceBytes, wasNormalized: false);
      }

      final resized = decoded.width > 1600
          ? img.copyResize(decoded, width: 1600)
          : decoded;
      return _PreparedImage(
        bytes: Uint8List.fromList(img.encodeJpg(resized, quality: 88)),
        wasNormalized: true,
      );
    } catch (_) {
      return _PreparedImage(bytes: sourceBytes, wasNormalized: false);
    }
  }

  String _normalizeFileName(String originalName) {
    final dotIndex = originalName.lastIndexOf('.');
    final baseName = dotIndex > 0 ? originalName.substring(0, dotIndex) : originalName;
    final cleaned = baseName.trim().isEmpty ? 'capture' : baseName.trim();
    return '$cleaned.jpg';
  }
}

class _PreparedImage {
  const _PreparedImage({
    required this.bytes,
    required this.wasNormalized,
  });

  final Uint8List bytes;
  final bool wasNormalized;
}
