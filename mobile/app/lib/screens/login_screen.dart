import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../services/api_client.dart';
import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/ucepark_brand_header.dart';
import '../widgets/uce_widgets.dart';
import 'setup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  static const routeName = '/login';

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController(text: 'security.uce');
  final _passwordController = TextEditingController();
  final _apiBaseUrlController =
      TextEditingController(text: AppConfig.apiBaseUrl);
  final _apiClient = ApiClient();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _apiBaseUrlController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final normalizedApiBaseUrl = _apiBaseUrlController.text.trim();
      AppConfig.setApiBaseUrl(normalizedApiBaseUrl);
      final isHealthy = await _apiClient.checkHealth();
      if (!mounted) return;
      if (!isHealthy) {
        setState(() {
          _error = 'No se pudo validar conectividad con el API.';
          _loading = false;
        });
        return;
      }

      final username = _usernameController.text.trim();
      final login = await _apiClient.login(
        username: username,
        password: _passwordController.text,
      );
      if (!mounted) return;

      final appScope = ParkingAppScope.of(context);
      appScope.persistApiBaseUrl(normalizedApiBaseUrl);
      appScope.persistAuthToken(login.accessToken);
      appScope.login(username: username, displayName: login.fullName);

      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(SetupScreen.routeName);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString().replaceFirst('Exception: ', '');
        _loading = false;
      });
      return;
    }

    if (!mounted) return;
    setState(() {
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const UceParkBrandHeader(centered: true),
                  const SizedBox(height: 10),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE7EEFB),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Text(
                      '🛡 MÓDULO GARITA',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                        color: UceParkColors.blue,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  UceCard(
                    padding: const EdgeInsets.fromLTRB(18, 20, 18, 20),
                    child: Column(
                      children: [
                        TextField(
                          controller: _usernameController,
                          decoration: const InputDecoration(
                            labelText: 'Usuario del guardia',
                            prefixIcon: Icon(Icons.person_outline),
                          ),
                        ),
                        const SizedBox(height: 13),
                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: const InputDecoration(
                            labelText: 'Contraseña',
                            prefixIcon: Icon(Icons.lock_outline),
                            helperText: 'Demo: security.uce / demo1234!',
                          ),
                        ),
                        const SizedBox(height: 13),
                        TextField(
                          controller: _apiBaseUrlController,
                          keyboardType: TextInputType.url,
                          decoration: const InputDecoration(
                            labelText: 'API base URL',
                            prefixIcon: Icon(Icons.wifi),
                            helperText:
                                'Ejemplo Android instalado: http://192.168.100.11:8000',
                          ),
                        ),
                        if (_error != null) ...[
                          const SizedBox(height: 13),
                          Container(
                            padding: const EdgeInsets.all(12),
                            width: double.infinity,
                            decoration: BoxDecoration(
                              color: UceParkColors.dangerBg,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                  color: UceParkColors.danger
                                      .withValues(alpha: 0.26)),
                            ),
                            child: Text(
                              _error!,
                              style: const TextStyle(
                                  color: UceParkColors.dangerDark),
                            ),
                          ),
                        ],
                        const SizedBox(height: 16),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton(
                            onPressed: _loading ? null : _login,
                            child: _loading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2, color: Colors.white),
                                  )
                                : const Text('📡 Conectar e iniciar turno'),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
                  const Text.rich(
                    TextSpan(
                      text: 'El celular debe estar en la ',
                      children: [
                        TextSpan(
                          text: 'misma red WiFi',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            color: UceParkColors.navy,
                          ),
                        ),
                        TextSpan(text: ' que el servidor del parqueadero.'),
                      ],
                    ),
                    textAlign: TextAlign.center,
                    style:
                        TextStyle(fontSize: 12.5, color: UceParkColors.muted),
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
