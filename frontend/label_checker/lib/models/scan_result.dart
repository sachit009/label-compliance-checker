/// Data models for scan results — mirrors backend Pydantic schemas.
library;

/// Result for a single compliance field.
class FieldResult {
  final String fieldName;
  final String displayName;
  final String status; // FOUND, MISSING, ILLEGIBLE
  final String? value;
  final double confidence;
  final String? recommendation;

  FieldResult({
    required this.fieldName,
    required this.displayName,
    required this.status,
    this.value,
    required this.confidence,
    this.recommendation,
  });

  factory FieldResult.fromJson(Map<String, dynamic> json) {
    return FieldResult(
      fieldName: json['field_name'] as String,
      displayName: json['display_name'] as String,
      status: json['status'] as String,
      value: json['value'] as String?,
      confidence: (json['confidence'] as num).toDouble(),
      recommendation: json['recommendation'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'field_name': fieldName,
        'display_name': displayName,
        'status': status,
        'value': value,
        'confidence': confidence,
        'recommendation': recommendation,
      };

  bool get isFound => status == 'FOUND';
  bool get isMissing => status == 'MISSING';
  bool get isIllegible => status == 'ILLEGIBLE';
}

/// Full response from a label scan.
class ScanResult {
  final String scanId;
  final String overallStatus; // COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT
  final List<FieldResult> fields;
  final String? rawText;
  final String ocrEngine;
  final DateTime scannedAt;
  final int compliantCount;
  final int totalFields;

  ScanResult({
    required this.scanId,
    required this.overallStatus,
    required this.fields,
    this.rawText,
    required this.ocrEngine,
    required this.scannedAt,
    required this.compliantCount,
    required this.totalFields,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    return ScanResult(
      scanId: json['scan_id'] as String,
      overallStatus: json['overall_status'] as String,
      fields: (json['fields'] as List)
          .map((f) => FieldResult.fromJson(f as Map<String, dynamic>))
          .toList(),
      rawText: json['raw_text'] as String?,
      ocrEngine: json['ocr_engine'] as String? ?? 'paddle',
      scannedAt: DateTime.parse(json['scanned_at'] as String),
      compliantCount: json['compliant_count'] as int? ?? 0,
      totalFields: json['total_fields'] as int? ?? 6,
    );
  }

  bool get isCompliant => overallStatus == 'COMPLIANT';
  bool get isNonCompliant => overallStatus == 'NON_COMPLIANT';
  bool get isPartiallyCompliant => overallStatus == 'PARTIALLY_COMPLIANT';

  double get compliancePercentage =>
      totalFields > 0 ? compliantCount / totalFields : 0.0;
}

/// Compact scan summary for history list views.
class ScanHistoryItem {
  final String scanId;
  final String overallStatus;
  final int compliantCount;
  final int totalFields;
  final DateTime scannedAt;

  ScanHistoryItem({
    required this.scanId,
    required this.overallStatus,
    required this.compliantCount,
    required this.totalFields,
    required this.scannedAt,
  });

  factory ScanHistoryItem.fromJson(Map<String, dynamic> json) {
    return ScanHistoryItem(
      scanId: json['scan_id'] as String,
      overallStatus: json['overall_status'] as String,
      compliantCount: json['compliant_count'] as int? ?? 0,
      totalFields: json['total_fields'] as int? ?? 6,
      scannedAt: DateTime.parse(json['scanned_at'] as String),
    );
  }

  double get compliancePercentage =>
      totalFields > 0 ? compliantCount / totalFields : 0.0;
}
