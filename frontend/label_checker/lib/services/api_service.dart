import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import '../models/scan_result.dart';

/// API service for communicating with the FastAPI backend.
class ApiService {
  late final Dio _dio;

  static String get defaultBaseUrl {
    if (kIsWeb) return Uri.base.origin;
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000';
      if (Platform.isIOS) return 'http://10.14.57.179:8000';
    } catch (_) {}
    return 'http://localhost:8000';
  }

  ApiService({String? baseUrl}) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl ?? defaultBaseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {
        'Accept': 'application/json',
      },
    ));

    // Logging interceptor for development
    _dio.interceptors.add(LogInterceptor(
      requestBody: false,
      responseBody: true,
      logPrint: (obj) => print('📡 API: $obj'),
    ));
  }

  /// Scan a product label image for compliance.
  ///
  /// Sends the image as multipart/form-data to POST /api/v1/scan
  /// and returns the full [ScanResult].
  Future<ScanResult> scanLabel(File imageFile) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
        ),
      });

      final response = await _dio.post(
        '/api/v1/scan',
        data: formData,
        onSendProgress: (sent, total) {
          final progress = (sent / total * 100).toStringAsFixed(0);
          print('📤 Upload: $progress%');
        },
      );

      return ScanResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get paginated scan history.
  Future<List<ScanHistoryItem>> getHistory({
    int page = 1,
    int pageSize = 20,
    String? status,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
      };
      if (status != null) queryParams['status'] = status;

      final response = await _dio.get(
        '/api/v1/scans',
        queryParameters: queryParams,
      );

      final data = response.data as Map<String, dynamic>;
      final items = data['items'] as List;
      return items
          .map((item) =>
              ScanHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get detailed scan result by ID.
  Future<ScanResult> getScanDetail(String scanId) async {
    try {
      final response = await _dio.get('/api/v1/scans/$scanId');
      return ScanResult.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Health check — verify backend is reachable.
  Future<bool> healthCheck() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Convert DioException to a user-friendly error message.
  Exception _handleError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return Exception('Connection timed out. Please check your network.');
      case DioExceptionType.connectionError:
        return Exception(
          'Cannot connect to the server. '
          'Make sure the backend is running on $defaultBaseUrl',
        );
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final detail = e.response?.data?['detail'] ?? 'Unknown error';
        return Exception('Server error ($statusCode): $detail');
      default:
        return Exception('An unexpected error occurred: ${e.message}');
    }
  }
}
