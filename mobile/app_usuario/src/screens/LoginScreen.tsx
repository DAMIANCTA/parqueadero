import React, { useState } from "react";
import {
  Alert,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/apiClient";
import { PrimaryButton, TextField, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "Login">;

export default function LoginScreen({ navigation }: Props) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async () => {
    if (!username || !password) {
      Alert.alert("Faltan datos", "Ingresa tu usuario y contraseña.");
      return;
    }
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo conectar con el servidor.";
      Alert.alert("No se pudo iniciar sesión", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Image
          source={require("../../assets/images/logo_lockup.png")}
          style={styles.logo}
          resizeMode="contain"
        />
        <UceCard>
          <TextField
            label="Usuario"
            icon="👤"
            placeholder="Ingresa tu usuario"
            autoCapitalize="none"
            value={username}
            onChangeText={setUsername}
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
            onChangeText={setPassword}
          />
          <TouchableOpacity
            style={styles.forgotLink}
            onPress={() => Alert.alert("Próximamente", "Esta función aún no está disponible.")}
          >
            <Text style={styles.forgotLinkText}>¿Olvidaste tu contraseña?</Text>
          </TouchableOpacity>
          <PrimaryButton label="Iniciar Sesión" onPress={onSubmit} loading={loading} />
        </UceCard>
        <View style={styles.footer}>
          <Text style={styles.footerText}>¿No tienes cuenta? </Text>
          <TouchableOpacity onPress={() => navigation.navigate("Register")}>
            <Text style={styles.footerLink}>Regístrate aquí</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bgApp,
  },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
  },
  logo: {
    height: 64,
    width: "100%",
    marginBottom: 28,
  },
  forgotLink: {
    alignSelf: "flex-end",
    marginBottom: 16,
  },
  forgotLinkText: {
    fontFamily: fonts.semiBold,
    fontSize: 12.5,
    color: colors.blue,
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
