import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import 'result_screen.dart';
import 'history_screen.dart';

/// Home screen with hero section, scan actions, and recent history preview.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final ApiService _api = ApiService();
  final ImagePicker _picker = ImagePicker();
  bool _isScanning = false;
  late AnimationController _pulseController;
  late AnimationController _gradientController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);

    _gradientController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _gradientController.dispose();
    super.dispose();
  }

  Future<void> _scanFromCamera() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
      maxWidth: 2000,
    );
    if (image != null) {
      _processImage(File(image.path));
    }
  }

  Future<void> _scanFromGallery() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
      maxWidth: 2000,
    );
    if (image != null) {
      _processImage(File(image.path));
    }
  }

  Future<void> _processImage(File imageFile) async {
    setState(() => _isScanning = true);

    try {
      final result = await _api.scanLabel(imageFile);
      if (!mounted) return;
      Navigator.push(
        context,
        PageRouteBuilder(
          pageBuilder: (_, __, ___) => ResultScreen(result: result),
          transitionsBuilder: (_, anim, __, child) {
            return FadeTransition(
              opacity: anim,
              child: SlideTransition(
                position: Tween<Offset>(
                  begin: const Offset(0, 0.05),
                  end: Offset.zero,
                ).animate(CurvedAnimation(
                  parent: anim,
                  curve: Curves.easeOutCubic,
                )),
                child: child,
              ),
            );
          },
          transitionDuration: const Duration(milliseconds: 400),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: AppTheme.nonCompliant,
        ),
      );
    } finally {
      if (mounted) setState(() => _isScanning = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppTheme.backgroundGradient,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),
                  _buildHeader(),
                  const SizedBox(height: 32),
                  _buildHeroCard(),
                  const SizedBox(height: 28),
                  _buildActionButtons(),
                  const SizedBox(height: 36),
                  _buildInfoSection(),
                  const SizedBox(height: 32),
                  _buildHistoryPreview(),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ShaderMask(
              shaderCallback: (bounds) =>
                  AppTheme.accentGradient.createShader(bounds),
              child: Text(
                '🏷️ LabelCheck',
                style: Theme.of(context).textTheme.displayMedium,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Legal Metrology Compliance',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textMuted,
                  ),
            ),
          ],
        ),
        // History button
        GestureDetector(
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const HistoryScreen()),
          ),
          child: Container(
            width: 44,
            height: 44,
            decoration: AppTheme.glassDecoration(
              opacity: 0.08,
              borderRadius: 14,
            ),
            child: const Icon(
              Icons.history_rounded,
              color: AppTheme.textSecondary,
              size: 22,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHeroCard() {
    return AnimatedBuilder(
      animation: _gradientController,
      builder: (context, child) {
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(28),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppTheme.accentPrimary.withValues(alpha: 0.3),
                AppTheme.accentSecondary.withValues(alpha: 0.15),
                AppTheme.accentPrimary.withValues(alpha: 0.2),
              ],
              begin: Alignment(
                -1 + _gradientController.value * 2,
                -1,
              ),
              end: Alignment(
                1 - _gradientController.value * 0.5,
                1,
              ),
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: AppTheme.accentPrimary.withValues(alpha: 0.2),
            ),
            boxShadow: [
              BoxShadow(
                color: AppTheme.accentPrimary.withValues(alpha: 0.15),
                blurRadius: 40,
                spreadRadius: -10,
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.accentPrimary.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  '📋 Rules 2011',
                  style: TextStyle(
                    color: AppTheme.accentSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Verify Product\nLabel Compliance',
                style: Theme.of(context).textTheme.displayLarge?.copyWith(
                      fontSize: 28,
                      height: 1.2,
                    ),
              ),
              const SizedBox(height: 12),
              Text(
                'Scan any product label to instantly check for '
                'all 6 mandatory fields required under the Legal '
                'Metrology (Packaged Commodities) Rules.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondary.withValues(alpha: 0.9),
                      height: 1.5,
                    ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        // Primary: Camera scan
        _buildScanButton(
          onTap: _isScanning ? null : _scanFromCamera,
          icon: Icons.camera_alt_rounded,
          label: _isScanning ? 'Scanning...' : 'Scan Label',
          subtitle: 'Use camera to capture label',
          gradient: AppTheme.accentGradient,
          isPrimary: true,
        ),
        const SizedBox(height: 14),
        // Secondary: Gallery upload
        _buildScanButton(
          onTap: _isScanning ? null : _scanFromGallery,
          icon: Icons.photo_library_rounded,
          label: 'Upload Image',
          subtitle: 'Choose from gallery',
          gradient: null,
          isPrimary: false,
        ),
      ],
    );
  }

  Widget _buildScanButton({
    required VoidCallback? onTap,
    required IconData icon,
    required String label,
    required String subtitle,
    required LinearGradient? gradient,
    required bool isPrimary,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        decoration: isPrimary
            ? AppTheme.glassDecorationWithGradient(
                gradient: gradient!,
                borderRadius: 18,
              )
            : AppTheme.glassDecoration(
                opacity: 0.06,
                borderRadius: 18,
              ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: isPrimary
                    ? Colors.white.withValues(alpha: 0.2)
                    : AppTheme.accentPrimary.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(14),
              ),
              child: _isScanning && isPrimary
                  ? const Padding(
                      padding: EdgeInsets.all(12),
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : Icon(
                      icon,
                      color: isPrimary
                          ? Colors.white
                          : AppTheme.accentPrimary,
                      size: 24,
                    ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(
                      color: isPrimary
                          ? Colors.white
                          : AppTheme.textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: isPrimary
                          ? Colors.white.withValues(alpha: 0.7)
                          : AppTheme.textMuted,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_rounded,
              color: isPrimary
                  ? Colors.white.withValues(alpha: 0.7)
                  : AppTheme.textMuted,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoSection() {
    final fields = [
      ('🏭', 'Manufacturer', 'Name & Address'),
      ('📦', 'Generic Name', 'Common Name'),
      ('⚖️', 'Net Quantity', 'Weight / Volume'),
      ('📅', 'Mfg Date', 'Month & Year'),
      ('💰', 'MRP', 'Retail Price'),
      ('📞', 'Consumer Care', 'Contact Details'),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'What We Check',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 4),
        Text(
          '6 mandatory fields as per Legal Metrology Rules',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: fields.map((f) {
            return Container(
              width: (MediaQuery.of(context).size.width - 58) / 2,
              padding: const EdgeInsets.all(14),
              decoration: AppTheme.glassDecoration(
                opacity: 0.04,
                borderRadius: 14,
              ),
              child: Row(
                children: [
                  Text(f.$1, style: const TextStyle(fontSize: 20)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          f.$2,
                          style: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Text(
                          f.$3,
                          style: const TextStyle(
                            color: AppTheme.textMuted,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _buildHistoryPreview() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Recent Scans',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            GestureDetector(
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const HistoryScreen()),
              ),
              child: const Text(
                'View All',
                style: TextStyle(
                  color: AppTheme.accentSecondary,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(32),
          decoration: AppTheme.glassDecoration(
            opacity: 0.03,
            borderRadius: 16,
          ),
          child: Column(
            children: [
              Icon(
                Icons.document_scanner_outlined,
                color: AppTheme.textMuted.withValues(alpha: 0.5),
                size: 40,
              ),
              const SizedBox(height: 12),
              const Text(
                'No scans yet',
                style: TextStyle(
                  color: AppTheme.textMuted,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Scan a product label to get started',
                style: TextStyle(
                  color: AppTheme.textMuted,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
