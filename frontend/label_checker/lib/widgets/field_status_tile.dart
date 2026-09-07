import 'package:flutter/material.dart';
import '../models/scan_result.dart';
import '../theme/app_theme.dart';

/// Compact tile for showing field status in history/summary views.
class FieldStatusTile extends StatelessWidget {
  final FieldResult field;

  const FieldStatusTile({super.key, required this.field});

  @override
  Widget build(BuildContext context) {
    final statusColor = AppTheme.statusColor(field.status);
    final statusIcon = AppTheme.statusIcon(field.status);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: statusColor.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: statusColor.withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(statusIcon, color: statusColor, size: 16),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              field.displayName,
              style: const TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

/// A history list item card showing scan summary.
class ScanHistoryCard extends StatelessWidget {
  final ScanHistoryItem item;
  final VoidCallback? onTap;

  const ScanHistoryCard({
    super.key,
    required this.item,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final statusColor = AppTheme.statusColor(item.overallStatus);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: AppTheme.glassDecoration(
          opacity: 0.06,
          borderRadius: 14,
          borderColor: statusColor.withValues(alpha: 0.15),
        ),
        child: Row(
          children: [
            // Status badge
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                gradient: AppTheme.statusGradient(item.overallStatus),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Center(
                child: Text(
                  '${item.compliantCount}/${item.totalFields}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),
            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    AppTheme.statusLabel(item.overallStatus),
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatDate(item.scannedAt),
                    style: const TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            // Arrow
            const Icon(
              Icons.chevron_right_rounded,
              color: AppTheme.textMuted,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays < 1) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${date.day}/${date.month}/${date.year}';
  }
}
