import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../services/api_client.dart';
import '../state/parking_app_scope.dart';
import '../theme/ucepark_theme.dart';
import '../widgets/ucepark_brand_header.dart';
import 'setup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  static const routeName = '/login';

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController(text: 'gate.operator');
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
      AppConfig.setApiBaseUrl(_apiBaseUrlController.text);
      final isHealthy = await _apiClient.checkHealth();
      if (!mounted) return;
      if (!isHealthy) {
        setState(() {
          _error = 'No se pudo validar conectividad con el API.';
          _loading = false;
        });
        return;
      }

      ParkingAppScope.of(context).login(
        username: _usernameController.text.trim(),
        displayName: _usernameController.text.trim().isEmpty
            ? 'Operador'
            : _usernameController.text.trim(),
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(SetupScreen.routeName);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Error de conexión con el backend.';
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
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const UceParkBrandHeader(
                        subtitle: 'Universidad Central del Ecuador',
                      ),
                      const SizedBox(height: 20),
                      Text(
                        'Ingreso de operador para control de puerta',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Accede con credenciales institucionales y valida la conectividad del gateway antes de operar.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 24),
                      TextField(
                        controller: _usernameController,
                        decoration: const InputDecoration(labelText: 'Usuario'),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _passwordController,
                        obscureText: true,
                        decoration: const InputDecoration(labelText: 'Clave'),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _apiBaseUrlController,
                        keyboardType: TextInputType.url,
                        decoration: const InputDecoration(
                          labelText: 'API base URL',
                          helperText:
                              'Ejemplo Android instalado: http://192.168.100.11:8000',
                        ),
                      ),
                      const SizedBox(height: 16),
                      if (_error != null) ...[
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: UceParkColors.danger.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color: UceParkColors.danger
                                    .withValues(alpha: 0.26)),
                          ),
                          child: Text(
                            _error!,
                            style: TextStyle(
                                color: Theme.of(context).colorScheme.error),
                          ),
                        ),
                        const SizedBox(height: 12),
                      ],
                      FilledButton(
                        onPressed: _loading ? null : _login,
                        child: _loading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Text('Entrar'),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'La sesión del operador se mantiene solo en memoria. No se almacenan tokens en texto plano.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
