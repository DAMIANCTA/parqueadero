package com.example.smart_parking_university_mobile

import android.content.Context
import android.os.Build
import android.os.PowerManager
import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Canal nativo usado por la pantalla "Garita fisica": mientras espera un
 * vehiculo se permite que la pantalla se apague sola (ahorro de bateria),
 * pero apenas llega un evento de presencia por MQTT hay que prender la
 * pantalla YA para que el guardia/conductor vea la captura en curso.
 * `wakelock_plus` (paquete Dart) solo puede EVITAR que la pantalla se
 * apague, no puede volver a encenderla si ya esta apagada - eso requiere
 * este codigo nativo.
 */
class MainActivity : FlutterActivity() {
    private val wakeScreenChannel = "ucepark/wake_screen"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, wakeScreenChannel)
            .setMethodCallHandler { call, result ->
                if (call.method == "wakeScreen") {
                    wakeScreen()
                    result.success(null)
                } else {
                    result.notImplemented()
                }
            }
    }

    private fun wakeScreen() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                    WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD
            )
        }

        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        @Suppress("DEPRECATION")
        val wakeLock = powerManager.newWakeLock(
            PowerManager.SCREEN_BRIGHT_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
            "ucepark:wake_screen"
        )
        wakeLock.acquire(10_000L)
    }
}
