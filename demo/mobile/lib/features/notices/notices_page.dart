import 'package:bankos_mobile/providers/notifications_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Lists the notices received while the app was open. Unread ones are marked.
class NoticesPage extends ConsumerWidget {
  /// Creates the notices screen.
  const NoticesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final List<AppNotice> notices = ref.watch(noticesProvider);
    final bool hasUnread = notices.any((AppNotice notice) => !notice.isRead);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Avisos'),
        actions: <Widget>[
          if (hasUnread)
            TextButton(
              onPressed: () =>
                  ref.read(noticesProvider.notifier).markAllAsRead(),
              child: const Text('Marcar leídos'),
            ),
          if (notices.isNotEmpty)
            TextButton(
              onPressed: () => ref.read(noticesProvider.notifier).clear(),
              child: const Text('Borrar todo'),
            ),
        ],
      ),
      body: notices.isEmpty
          ? const Center(child: Text('No tienes avisos nuevos'))
          : ListView.separated(
              itemCount: notices.length,
              separatorBuilder: (BuildContext context, int index) =>
                  const Divider(height: 1),
              itemBuilder: (BuildContext context, int index) {
                final AppNotice notice = notices[index];
                final ThemeData theme = Theme.of(context);
                return ListTile(
                  tileColor: notice.isRead
                      ? null
                      : theme.colorScheme.primaryContainer.withValues(
                          alpha: 0.35,
                        ),
                  leading: CircleAvatar(
                    child: Icon(
                      notice.isRead
                          ? (notice.isIncoming
                                ? Icons.call_received
                                : Icons.call_made)
                          : Icons.mark_email_unread,
                    ),
                  ),
                  title: Text(
                    notice.title,
                    style: TextStyle(
                      fontWeight: notice.isRead
                          ? FontWeight.normal
                          : FontWeight.bold,
                    ),
                  ),
                  subtitle: Text(notice.body),
                  trailing: Text(_timeLabel(notice.receivedAt)),
                  onTap: notice.isRead
                      ? null
                      : () => ref
                            .read(noticesProvider.notifier)
                            .markAsRead(notice.id),
                );
              },
            ),
    );
  }

  /// Formats the hour and minute of [time] as HH:mm.
  String _timeLabel(DateTime time) {
    final DateTime local = time.toLocal();
    final String hour = local.hour.toString().padLeft(2, '0');
    final String minute = local.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}
