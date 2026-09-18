import 'dart:async';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'services/fcm_service.dart';
import 'services/pairing_service.dart';
import 'screens/pairing_screen.dart';
import 'screens/dashboard_screen.dart';

const String kSupabaseUrl = 'https://vdaqzfyijonojuwzwpyb.supabase.co';
const String kSupabaseAnonKey =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkYXF6Znlpam9ub2p1d3p3cHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk2MjAzNjIsImV4cCI6MjEwNTE5NjM2Mn0.8be3HTOvti0FnOy5lX08gW5JnuyDFeq2OoeW5Lf0p9s';

void main() {
  runZonedGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();
    runApp(const ElectroStoreRootApp());
  }, (error, stack) {
    debugPrint("Global Error: $error\n$stack");
  });
}

class ElectroStoreRootApp extends StatelessWidget {
  const ElectroStoreRootApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'E-Store ERP',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF121824),
        primaryColor: const Color(0xFF0284C7),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF0284C7),
          secondary: Color(0xFF10B981),
          surface: Color(0xFF1E293B),
        ),
      ),
      home: const AppStartupFlow(),
    );
  }
}

class AppStartupFlow extends StatefulWidget {
  const AppStartupFlow({Key? key}) : super(key: key);

  @override
  State<AppStartupFlow> createState() => _AppStartupFlowState();
}

class _AppStartupFlowState extends State<AppStartupFlow> {
  bool _isInitializing = true;
  bool _isPaired = false;
  String? _initError;

  @override
  void initState() {
    super.initState();
    _performBootstrap();
  }

  Future<void> _performBootstrap() async {
    try {
      // 1. Firebase Initialize
      try {
        await Firebase.initializeApp();
      } catch (e) {
        debugPrint("Firebase init note: $e");
      }

      // 2. Supabase Initialize
      try {
        await Supabase.initialize(
          url: kSupabaseUrl,
          anonKey: kSupabaseAnonKey,
        );
      } catch (e) {
        debugPrint("Supabase init note: $e");
      }

      // 3. FCM Push Services
      try {
        final fcm = FCMService();
        await fcm.initialize();
      } catch (e) {
        debugPrint("FCM init note: $e");
      }

      // 4. Device Pairing Check
      bool paired = false;
      try {
        final pairingService = DevicePairingService();
        paired = await pairingService.isDevicePaired();
      } catch (e) {
        debugPrint("Pairing check note: $e");
      }

      if (!mounted) return;
      setState(() {
        _isPaired = paired;
        _isInitializing = false;
      });
    } catch (err) {
      if (!mounted) return;
      setState(() {
        _initError = err.toString();
        _isInitializing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isInitializing) {
      return Scaffold(
        backgroundColor: const Color(0xFF121824),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF0284C7).withOpacity(0.3),
                      blurRadius: 24,
                      spreadRadius: 4,
                    )
                  ],
                ),
                child: const Icon(Icons.flash_on, size: 56, color: Color(0xFF38BDF8)),
              ),
              const SizedBox(height: 24),
              const Text(
                "E-Store ERP",
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                "Realtime Cloud Synchronizer",
                style: TextStyle(fontSize: 13, color: Colors.grey),
              ),
              const SizedBox(height: 32),
              const SizedBox(
                width: 28,
                height: 28,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF38BDF8)),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (_initError != null) {
      return Scaffold(
        backgroundColor: const Color(0xFF121824),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.warning_amber_rounded, size: 48, color: Colors.amber),
                const SizedBox(height: 16),
                const Text("Startup Notice", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text(_initError!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey, fontSize: 13)),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _isInitializing = true;
                      _initError = null;
                    });
                    _performBootstrap();
                  },
                  child: const Text("Retry"),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return _isPaired ? const DashboardScreen() : const PairingScreen();
  }
}
