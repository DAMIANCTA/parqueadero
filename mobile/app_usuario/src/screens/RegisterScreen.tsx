import React, { useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/apiClient";
import { PrimaryButton, TextField, TopBar, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "Register">;

const USERNAME_REGEX = /^[a-zA-Z0-9._%+-]+$/;
const EMAIL_DOMAIN = "@uce.edu.ec";
const MIN_PASSWORD_LENGTH = 6;
const DOCUMENT_LENGTH = 10;
const PHONE_LENGTH = 10;
const PHONE_PREFIX = "09";

type FieldErrors = Partial<
  Record<"fullName" | "documentNumber" | "phone" | "username" | "password" | "confirmPassword", string>
>;

function maskDigitsOnly(raw: string, maxLength: number): string {
  return raw.replace(/\D/g, "").slice(0, maxLength);
}

function maskPhoneInput(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  const rest = digits.startsWith(PHONE_PREFIX) ? digits.slice(PHONE_PREFIX.length) : digits;
  return (PHONE_PREFIX + rest).slice(0, PHONE_LENGTH);
}

export default function RegisterScreen({ navigation }: Props) {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [documentNumber, setDocumentNumber] = useState("");
  const [phone, setPhone] = useState(PHONE_PREFIX);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  const clearError = (field: keyof FieldErrors) => {
    setErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev));
  };

  const validate = (): FieldErrors => {
    const next: FieldErrors = {};
    if (!fullName.trim()) next.fullName = "Ingresa tu nombre completo.";
    if (documentNumber.length !== DOCUMENT_LENGTH) next.documentNumber = `Debe tener ${DOCUMENT_LENGTH} dígitos.`;
    if (phone.length !== PHONE_LENGTH) next.phone = `Debe tener ${PHONE_LENGTH} dígitos (${PHONE_PREFIX}XXXXXXXX).`;
    if (!username.trim()) {
      next.username = "Ingresa tu usuario institucional.";
    } else if (!USERNAME_REGEX.test(username.trim())) {
      next.username = "Usa solo letras, números, puntos o guiones.";
    }
    if (!password) {
      next.password = "Ingresa una contraseña.";
    } else if (password.length < MIN_PASSWORD_LENGTH) {
      next.password = `Debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
    }
    if (!confirmPassword) {
      next.confirmPassword = "Confirma tu contraseña.";
    } else if (password !== confirmPassword) {
      next.confirmPassword = "Las contraseñas no coinciden.";
    }
    return next;
  };

  const onSubmit = async () => {
    const fieldErrors = validate();
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0) {
      return;
    }
    const normalizedUsername = username.trim().toLowerCase();
    setLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        document_number: documentNumber,
        phone,
        username: normalizedUsername,
        password,
        confirm_password: confirmPassword,
        email: `${normalizedUsername}${EMAIL_DOMAIN}`,
      });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo conectar con el servidor.";
      Alert.alert("No se pudo completar el registro", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <TopBar
          title="Crear Cuenta"
          subtitle="Completa tus datos para registrarte"
          onBack={() => navigation.goBack()}
        />
        <UceCard style={{ marginTop: spacingTop }}>
          <TextField
            label="Nombres completos"
            icon="👤"
            placeholder="Diego Castro"
            value={fullName}
            onChangeText={(v) => {
              setFullName(v);
              clearError("fullName");
            }}
            error={errors.fullName}
          />
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <TextField
                label="Cédula"
                placeholder="1712345678"
                keyboardType="number-pad"
                maxLength={DOCUMENT_LENGTH}
                value={documentNumber}
                onChangeText={(v) => {
                  setDocumentNumber(maskDigitsOnly(v, DOCUMENT_LENGTH));
                  clearError("documentNumber");
                }}
                error={errors.documentNumber}
              />
            </View>
            <View style={{ flex: 1 }}>
              <TextField
                label="Teléfono"
                placeholder="09XXXXXXXX"
                keyboardType="phone-pad"
                maxLength={PHONE_LENGTH}
                value={phone}
                onChangeText={(v) => {
                  setPhone(maskPhoneInput(v));
                  clearError("phone");
                }}
                error={errors.phone}
              />
            </View>
          </View>
          <TextField
            label="Usuario institucional"
            icon="👤"
            placeholder="dcastro"
            suffix={EMAIL_DOMAIN}
            autoCapitalize="none"
            autoCorrect={false}
            value={username}
            onChangeText={(v) => {
              setUsername(v);
              clearError("username");
            }}
            error={errors.username}
          />
          <TextField
            label="Contraseña"
            icon="🔒"
            placeholder="••••••••"
            secureTextEntry
            autoCapitalize="none"
            autoCorrect={false}
            textContentType="password"
            value={password}
            onChangeText={(v) => {
              setPassword(v);
              clearError("password");
              clearError("confirmPassword");
            }}
            error={errors.password}
          />
          <TextField
            label="Confirmar contraseña"
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
          <PrimaryButton label="Crear Cuenta" onPress={onSubmit} loading={loading} />
          <Text style={styles.terms}>
            Al registrarte aceptas el reglamento de parqueaderos de la UCE.
          </Text>
        </UceCard>
        <View style={styles.footer}>
          <Text style={styles.footerText}>¿Ya tienes cuenta? </Text>
          <TouchableOpacity onPress={() => navigation.navigate("Login")}>
            <Text style={styles.footerLink}>Inicia sesión</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const spacingTop = 18;

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bgApp,
  },
  content: {
    flexGrow: 1,
    padding: 18,
    paddingTop: 58,
  },
  row: {
    flexDirection: "row",
    gap: 10,
  },
  terms: {
    fontFamily: fonts.regular,
    fontSize: 11.5,
    color: colors.muted,
    textAlign: "center",
    marginTop: 12,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    marginTop: 18,
  },
  footerText: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: colors.muted,
  },
  footerLink: {
    fontFamily: fonts.bold,
    fontSize: 12.5,
    color: colors.blue,
  },
});
