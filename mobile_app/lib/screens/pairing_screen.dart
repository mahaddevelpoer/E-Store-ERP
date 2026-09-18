import 'package:flutter/material.dart';
import '../services/pairing_service.dart';
import '../services/fcm_service.dart';
import 'dashboard_screen.dart';

class PairingScreen extends StatefulWidget {
  const PairingScreen({Key? key}) : super(key: key);

  @override
  State<PairingScreen> createState() => _PairingScreenState();
}

class _PairingScreenState extends State<PairingScreen> {
  final TextEditingController _codeController = TextEditingController();
  final DevicePairingService _pairingService = DevicePairingService();
  final FCMService _fcmService = FCMService();
  bool _isLoading = false;
  String? _errorMessage;

  void _pairDevice() async {
    final code = _codeController.text.trim();
    if (code.length != 6) {
      setState(() => _errorMessage = "Please enter valid 6-digit code");
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final token = await _fcmService.getFCMToken() ?? "sample_fcm_token_dev";
    final success = await _pairingService.verifyPairingCode(code, token, "Owner Phone");

    setState(() => _isLoading = false);

    if (success) {
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
      );
    } else {
      setState(() => _errorMessage = "Invalid or expired 6-digit code. Check Desktop POS screen.");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121824),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.flash_on, size: 72, color: Color(0xFF38BDF8)),
              const SizedBox(height: 16),
              const Text(
                "ElectroStore Mobile",
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 8),
              const Text(
                "Enter 6-Digit Code from Desktop POS",
                style: TextStyle(fontSize: 14, color: Colors.grey),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _codeController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, letterSpacing: 8, color: Color(0xFF10B981)),
                decoration: InputDecoration(
                  counterText: "",
                  filled: true,
                  fillColor: const Color(0xFF1E293B),
                  hintText: "123456",
                  hintStyle: TextStyle(color: Colors.grey.shade600),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent, fontSize: 13)),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0284C7),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _isLoading ? null : _pairDevice,
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text("PAIR DEVICE NOW", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
