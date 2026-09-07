import 'dart:ui';
import 'package:flutter/material.dart';
import '../models/scan_result.dart';
import '../theme/app_theme.dart';

/// Premium glassmorphic card for displaying a compliance field result.
/// Features animated expand/collapse for recommendations and a confidence bar.
class ComplianceCard extends StatefulWidget {
  final FieldResult field;
  final int index;

  const ComplianceCard({
    super.key,
    required this.field,
    required this.index,
  });

  @override
  State<ComplianceCard> createState() => _ComplianceCardState();
}

class _ComplianceCardState extends State<ComplianceCard>
    with SingleTickerProviderStateMixin {
  bool _isExpanded = false;
  late AnimationController _animController;
  late Animation<double> _expandAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _expandAnimation = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeInOutCubic,
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  void _toggleExpand() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _animController.forward();
      } else {
        _animController.reverse();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = AppTheme.statusColor(widget.field.status);
    final statusIcon = AppTheme.statusIcon(widget.field.status);

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: Duration(milliseconds: 400 + (widget.index * 80)),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(0, 30 * (1 - value)),
          child: Opacity(
            opacity: value,
            child: child,
          ),
        );
      },
      child: GestureDetector(
        onTap: widget.field.recommendation != null ? _toggleExpand : null,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              decoration: AppTheme.glassDecoration(
                opacity: 0.06,
                borderRadius: 16,
                borderColor: statusColor.withValues(alpha: 0.2),
              ),
              child: Column(
                children: [
                  // ── Main Content Row ──
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        // Status icon with glow
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            statusIcon,
                            color: statusColor,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 14),
                        // Field info
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.field.displayName,
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(fontSize: 14),
                              ),
                              const SizedBox(height: 4),
                              if (widget.field.value != null)
                                Text(
                                  widget.field.value!,
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodyMedium
                                      ?.copyWith(
                                        color: AppTheme.textSecondary,
                                      ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                )
                              else
                                Text(
                                  AppTheme.statusLabel(widget.field.status),
                                  style: TextStyle(
                                    color: statusColor,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                            ],
                          ),
                        ),
                        // Confidence indicator
                        Column(
                          children: [
                            Text(
                              '${(widget.field.confidence * 100).toInt()}%',
                              style: TextStyle(
                                color: statusColor,
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 4),
                            SizedBox(
                              width: 40,
                              height: 4,
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(2),
                                child: LinearProgressIndicator(
                                  value: widget.field.confidence,
                                  backgroundColor:
                                      Colors.white.withValues(alpha: 0.1),
                                  color: statusColor,
                                ),
                              ),
                            ),
                          ],
                        ),
                        if (widget.field.recommendation != null) ...[
                          const SizedBox(width: 8),
                          AnimatedRotation(
                            turns: _isExpanded ? 0.5 : 0,
                            duration: const Duration(milliseconds: 300),
                            child: const Icon(
                              Icons.expand_more_rounded,
                              color: AppTheme.textMuted,
                              size: 20,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  // ── Expandable Recommendation ──
                  SizeTransition(
                    sizeFactor: _expandAnimation,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: statusColor.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: statusColor.withValues(alpha: 0.15),
                          ),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              Icons.lightbulb_outline_rounded,
                              color: statusColor,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                widget.field.recommendation ?? '',
                                style: const TextStyle(
                                  color: AppTheme.textSecondary,
                                  fontSize: 12,
                                  height: 1.5,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
