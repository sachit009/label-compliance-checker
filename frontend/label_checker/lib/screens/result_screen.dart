import 'dart:ui';
import 'package:flutter/material.dart';
import '../models/scan_result.dart';
import '../theme/app_theme.dart';
import '../widgets/compliance_card.dart';

/// Result screen showing overall compliance status and per-field details.
class ResultScreen extends StatefulWidget {
  final ScanResult result;

  const ResultScreen({super.key, required this.result});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen>
    with TickerProviderStateMixin {
  late AnimationController _scoreController;
  late Animation<double> _scoreAnimation;
  bool _showRawText = false;

  @override
  void initState() {
    super.initState();
    _scoreController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _scoreAnimation = Tween<double>(
      begin: 0,
      end: widget.result.compliancePercentage,
    ).animate(CurvedAnimation(
      parent: _scoreController,
      curve: Curves.easeOutCubic,
    ));

    // Start the score animation after a brief delay
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _scoreController.forward();
    });
  }

  @override
  void dispose() {
    _scoreController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppTheme.backgroundGradient,
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildAppBar(),
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 8),
                      _buildScoreCard(),
                      const SizedBox(height: 28),
                      _buildFieldsHeader(),
                      const SizedBox(height: 16),
                      _buildFieldsList(),
                      const SizedBox(height: 28),
                      _buildRawTextSection(),
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: Container(
              width: 40,
              height: 40,
              decoration: AppTheme.glassDecoration(
                opacity: 0.08,
                borderRadius: 12,
              ),
              child: const Icon(
                Icons.arrow_back_rounded,
                color: AppTheme.textPrimary,
                size: 20,
              ),
            ),
          ),
          const Spacer(),
          Text(
            'Scan Results',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const Spacer(),
          GestureDetector(
            onTap: _shareResults,
            child: Container(
              width: 40,
              height: 40,
              decoration: AppTheme.glassDecoration(
                opacity: 0.08,
                borderRadius: 12,
              ),
              child: const Icon(
                Icons.share_rounded,
                color: AppTheme.textSecondary,
                size: 20,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScoreCard() {
    final status = widget.result.overallStatus;
    final statusColor = AppTheme.statusColor(status);

    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(28),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                statusColor.withValues(alpha: 0.15),
                statusColor.withValues(alpha: 0.05),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: statusColor.withValues(alpha: 0.25),
            ),
            boxShadow: [
              BoxShadow(
                color: statusColor.withValues(alpha: 0.1),
                blurRadius: 40,
                spreadRadius: -10,
              ),
            ],
          ),
          child: Column(
            children: [
              // Animated score ring
              AnimatedBuilder(
                animation: _scoreAnimation,
                builder: (context, _) {
                  return SizedBox(
                    width: 120,
                    height: 120,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        // Background ring
                        SizedBox(
                          width: 120,
                          height: 120,
                          child: CircularProgressIndicator(
                            value: 1.0,
                            strokeWidth: 8,
                            color: Colors.white.withValues(alpha: 0.08),
                          ),
                        ),
                        // Progress ring
                        SizedBox(
                          width: 120,
                          height: 120,
                          child: CircularProgressIndicator(
                            value: _scoreAnimation.value,
                            strokeWidth: 8,
                            color: statusColor,
                            strokeCap: StrokeCap.round,
                          ),
                        ),
                        // Score text
                        Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              '${widget.result.compliantCount}',
                              style: TextStyle(
                                color: statusColor,
                                fontSize: 36,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            Text(
                              '/ ${widget.result.totalFields}',
                              style: const TextStyle(
                                color: AppTheme.textMuted,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(height: 20),
              // Status badge
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  gradient: AppTheme.statusGradient(status),
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: statusColor.withValues(alpha: 0.3),
                      blurRadius: 16,
                      spreadRadius: -4,
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      AppTheme.statusIcon(status),
                      color: Colors.white,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      AppTheme.statusLabel(status),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              // Summary text
              Text(
                _getSummaryText(),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFieldsHeader() {
    final foundCount =
        widget.result.fields.where((f) => f.isFound).length;
    final missingCount =
        widget.result.fields.where((f) => f.isMissing).length;
    final illegibleCount =
        widget.result.fields.where((f) => f.isIllegible).length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Field Details',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _buildMiniStat('Found', foundCount, AppTheme.compliant),
            const SizedBox(width: 10),
            _buildMiniStat('Missing', missingCount, AppTheme.nonCompliant),
            if (illegibleCount > 0) ...[
              const SizedBox(width: 10),
              _buildMiniStat('Illegible', illegibleCount, AppTheme.partial),
            ],
          ],
        ),
      ],
    );
  }

  Widget _buildMiniStat(String label, int count, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$count',
            style: TextStyle(
              color: color,
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: color.withValues(alpha: 0.8),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFieldsList() {
    // Sort: missing/illegible first, then found
    final sortedFields = List<FieldResult>.from(widget.result.fields)
      ..sort((a, b) {
        final order = {'MISSING': 0, 'ILLEGIBLE': 1, 'FOUND': 2};
        return (order[a.status] ?? 3).compareTo(order[b.status] ?? 3);
      });

    return Column(
      children: sortedFields.asMap().entries.map((entry) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: ComplianceCard(
            field: entry.value,
            index: entry.key,
          ),
        );
      }).toList(),
    );
  }

  Widget _buildRawTextSection() {
    if (widget.result.rawText == null || widget.result.rawText!.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GestureDetector(
          onTap: () => setState(() => _showRawText = !_showRawText),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: AppTheme.glassDecoration(
              opacity: 0.04,
              borderRadius: 14,
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.text_snippet_rounded,
                  color: AppTheme.textMuted,
                  size: 20,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Raw OCR Text',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: AppTheme.textSecondary,
                        ),
                  ),
                ),
                AnimatedRotation(
                  turns: _showRawText ? 0.5 : 0,
                  duration: const Duration(milliseconds: 300),
                  child: const Icon(
                    Icons.expand_more_rounded,
                    color: AppTheme.textMuted,
                    size: 20,
                  ),
                ),
              ],
            ),
          ),
        ),
        AnimatedCrossFade(
          firstChild: const SizedBox.shrink(),
          secondChild: Container(
            width: double.infinity,
            margin: const EdgeInsets.only(top: 8),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.cardDark,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: Colors.white.withValues(alpha: 0.05),
              ),
            ),
            child: SelectableText(
              widget.result.rawText ?? '',
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 12,
                fontFamily: 'monospace',
                height: 1.6,
              ),
            ),
          ),
          crossFadeState: _showRawText
              ? CrossFadeState.showSecond
              : CrossFadeState.showFirst,
          duration: const Duration(milliseconds: 300),
        ),
      ],
    );
  }

  String _getSummaryText() {
    final r = widget.result;
    if (r.isCompliant) {
      return 'All ${r.totalFields} mandatory fields were detected on this label. '
          'The product appears to comply with Legal Metrology Rules.';
    } else if (r.isNonCompliant) {
      return 'None of the mandatory fields could be detected. '
          'Please ensure the label is clearly visible and well-lit.';
    } else {
      final missing = r.totalFields - r.compliantCount;
      return '$missing of ${r.totalFields} mandatory fields are missing or illegible. '
          'See details below for specific recommendations.';
    }
  }

  void _shareResults() {
    final r = widget.result;
    final text = StringBuffer();
    text.writeln('🏷️ Label Compliance Report');
    text.writeln('Status: ${AppTheme.statusLabel(r.overallStatus)}');
    text.writeln('Score: ${r.compliantCount}/${r.totalFields}');
    text.writeln('');
    for (final field in r.fields) {
      final icon = field.isFound ? '✅' : '❌';
      text.writeln('$icon ${field.displayName}: ${field.value ?? "Not found"}');
    }
    text.writeln('');
    text.writeln('Scanned at: ${r.scannedAt}');
    text.writeln('OCR Engine: ${r.ocrEngine}');

    // TODO: Use share_plus to share this text
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Report copied to clipboard'),
        backgroundColor: AppTheme.accentPrimary,
      ),
    );
  }
}
