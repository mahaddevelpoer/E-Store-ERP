import 'dart:async';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'services/fcm_service.dart';
import 'services/pairing_service.dart';
import 'screens/pairing_screen.dart';
import 'screens/dashboard_screen.dart';

const String kSupabaseUrl = 'https://vdaqzfyijonojuwzwpyb.supabase.co';
const String kSupabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkYXF6Znlpam9ub2p1d3p3cHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk2MjAzNjIsImV4cCI6MjEwNTE5NjM2Mn0.8be3HTOvti0FnOy5lX08gW5JnuyDFeq2OoeW5Lf0p9s';

void main() async {
  runZonedGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();

    // 1. Initialize Firebase safely
    try {
      await Firebase.initializeApp();
    } catch (e) {
      print("Firebase initialize warning: $e");
    }

    // 2. Initialize Supabase with verified credentials
    try {
      await Supabase.initialize(
        url: kSupabaseUrl,
        anonKey: kSupabaseAnonKey,
      );
    } catch (e) {
      print("Supabase initialize warning: $e");
    }

    // 3. Initialize FCM Services
    final FCMService fcmService = FCMService();
    try {
      await fcmService.initialize();
    } catch (e) {
      print("FCM initialize warning: $e");
    }

    // 4. Check if device is paired locally
    bool isPaired = false;
    try {
      final DevicePairingService pairingService = DevicePairingService();
      isPaired = await pairingService.isDevicePaired();
    } catch (e) {
      print("Pairing check notice: $e");
    }

    runApp(ElectroStoreMobileApp(isPaired: isPaired));
  }, (error, stack) {
    print("App Global Exception: $error\n$stack");
  });
}

class ElectroStoreMobileApp extends StatelessWidget {
  final bool isPaired;
  const ElectroStoreMobileApp({Key? key, required this.isPaired}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'E-Store ERP',
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
