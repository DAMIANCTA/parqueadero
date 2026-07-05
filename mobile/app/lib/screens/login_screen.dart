import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../state/parking_app_scope.dart';
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
  final _apiClient = ApiClient();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
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
        displayName: _usernameController.text.trim().isEmpty ? 'Operador' : _usernameController.text.trim(),
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(SetupScreen.routeName);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Error de conexion con el backend.';
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
            constraints: const BoxConstraints(maxWidth: 420),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Smart Parking University', style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  Text('Ingreso de operador para control de puerta.', style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 24),
                  TextField(
                    controller: _usernameController,
                    decoration: const InputDecoration(labelText: 'Usuario', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _passwordController,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Clave', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  if (_error != null) ...[
                    Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                    const SizedBox(height: 12),
                  ],
                  FilledButton(
                    onPressed: _loading ? null : _login,
                    child: _loading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Entrar'),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'La sesion del operador se mantiene solo en memoria. No se almacenan tokens en texto plano.',
                    style: Theme.of(context).textTheme.bodySmall,
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
