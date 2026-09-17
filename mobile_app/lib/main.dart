import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'services/fcm_service.dart';
import 'services/pairing_service.dart';
import 'screens/pairing_screen.dart';
import 'screens/dashboard_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Supabase
  await Supabase.initialize(
    url: 'https://YOUR_SUPABASE_PROJECT_URL.supabase.co',
    anonKey: 'YOUR_SUPABASE_ANON_KEY',
  );

  // Initialize FCM Services
  final FCMService fcmService = FCMService();
  await fcmService.initialize();

  // Check if device is paired
  final DevicePairingService pairingService = DevicePairingService();
  final bool isPaired = await pairingService.isDevicePaired();

  runApp(ElectroStoreMobileApp(isPaired: isPaired));
}

class ElectroStoreMobileApp extends StatelessWidget {
  final bool isPaired;
  const ElectroStoreMobileApp({Key? key, required this.isPaired}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ElectroStore Manager',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF121824),
        primaryColor: const Color(0xFF0284C7),
      ),
      home: isPaired ? const DashboardScreen() : const PairingScreen(),
    );
  }
}
