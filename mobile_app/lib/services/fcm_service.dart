import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class FCMService {
  FirebaseMessaging? _firebaseMessaging;
  final FlutterLocalNotificationsPlugin _localNotificationsPlugin = FlutterLocalNotificationsPlugin();
  bool _isInitialized = false;

  Future<void> initialize() async {
    try {
      _firebaseMessaging = FirebaseMessaging.instance;

      // Request permission (Android 13+ and iOS)
      await _firebaseMessaging?.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );

      // Initialize local notifications
      const AndroidInitializationSettings androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
      const InitializationSettings initSettings = InitializationSettings(android: androidSettings);
      await _localNotificationsPlugin.initialize(initSettings);

      // Create notification channel for modern Android
      const AndroidNotificationChannel channel = AndroidNotificationChannel(
        'electrostore_channel',
        'Sales & Stock Alerts',
        description: 'Real-time sales and low stock notifications',
        importance: Importance.max,
      );

      await _localNotificationsPlugin
          .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(channel);

      // Listen for foreground push notifications
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        if (message.notification != null) {
          _showNotification(
            message.notification!.title ?? 'ElectroStore Alert',
            message.notification!.body ?? '',
          );
        }
      });

      _isInitialized = true;
    } catch (e) {
      // Gracefully handle if Google Play Services or permissions are disabled
      print("FCMService initialization notice: $e");
    }
  }

  Future<String?> getFCMToken() async {
    try {
      if (_firebaseMessaging == null) {
        _firebaseMessaging = FirebaseMessaging.instance;
      }
      return await _firebaseMessaging?.getToken();
    } catch (e) {
      return "mobile_token_${DateTime.now().millisecondsSinceEpoch}";
    }
  }

  Future<void> _showNotification(String title, String body) async {
    try {
      const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
        'electrostore_channel',
        'Sales & Stock Alerts',
        channelDescription: 'Real-time sales and low stock notifications',
        importance: Importance.max,
        priority: Priority.high,
        icon: '@mipmap/ic_launcher',
      );
      const NotificationDetails details = NotificationDetails(android: androidDetails);
      await _localNotificationsPlugin.show(0, title, body, details);
    } catch (e) {
      print("Local notification show error: $e");
    }
  }
}
