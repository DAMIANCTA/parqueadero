import React, { useState } from "react";
import { Alert, ScrollView, StyleSheet, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError, changePassword } from "../services/apiClient";
import { PrimaryButton, TextField, TopBar, UceCard } from "../components/ui";
import { colors } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "CambiarContrasena">;

const MIN_PASSWORD_LENGTH = 6;

type FieldErrors = Partial<Record<"currentPassword" | "newPassword" | "confirmPassword", string>>;

export default function ChangePasswordScreen({ navigation }: Props) {
  const { token, logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  const clearError = (field: keyof FieldErrors) => {
    setErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev));
  };

  const validate = (): FieldErrors => {
    const next: FieldErrors = {};
    if (!currentPassword) next.currentPassword = "Ingresa tu contraseña actual.";
    if (!newPassword) {
      next.newPassword = "Ingresa una nueva contraseña.";
    } else if (newPassword.length < MIN_PASSWORD_LENGTH) {
      next.newPassword = `Debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
    }
    if (!confirmPassword) {
      next.confirmPassword = "Confirma tu nueva contraseña.";
    } else if (newPassword !== confirmPassword) {
      next.confirmPassword = "Las contraseñas no coinciden.";
    }
    return next;
  };

  const onSubmit = async () => {
    const fieldErrors = validate();
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0) return;
    setLoading(true);
    try {
      await changePassword(token!, {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmPassword,
      });
      Alert.alert("Listo", "Tu contraseña fue actualizada. Vuelve a iniciar sesión.", [
        { text: "OK", onPress: () => logout() },
      ]);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo cambiar la contraseña.";
      Alert.alert("Error", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <TopBar title="Cambiar Contraseña" subtitle="Actualiza tu contraseña de acceso" onBack={() => navigation.goBack()} />
        <UceCard>
          <TextField
            label="Contraseña actual"
            icon="🔒"
            placeholder="••••••••"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            textContentType="password"
            value={currentPassword}
            onChangeText={(v) => {
              setCurrentPassword(v);
              clearError("currentPassword");
            }}
            error={errors.currentPassword}
          />
          <TextField
            label="Nueva contraseña"
            icon="🔒"
            placeholder="••••••••"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            textContentType="password"
            value={newPassword}
            onChangeText={(v) => {
              setNewPassword(v);
              clearError("newPassword");
              clearError("confirmPassword");
            }}
            error={errors.newPassword}
          />
          <TextField
            label="Confirmar nueva contraseña"
            icon="🔒"
            placeholder="••••••••"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            textContentType="password"
            value={confirmPassword}
            onChangeText={(v) => {
              setConfirmPassword(v);
              clearError("confirmPassword");
            }}
            error={errors.confirmPassword}
          />
          <PrimaryButton label="Guardar nueva contraseña" onPress={onSubmit} loading={loading} />
        </UceCard>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bgApp,
  },
  content: {
    padding: 18,
    paddingTop: 58,
    gap: 14,
  },
});
