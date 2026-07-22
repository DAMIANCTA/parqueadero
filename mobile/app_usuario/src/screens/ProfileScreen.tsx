import React, { useCallback, useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CompositeNavigationProp, useFocusEffect, useNavigation } from "@react-navigation/native";
import type { MaterialTopTabNavigationProp } from "@react-navigation/material-top-tabs";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError, Vehicle, getMyVehicles } from "../services/apiClient";
import { PlateChip, StatusBadge, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { TabsParamList } from "../navigation/TabsNavigator";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Nav = CompositeNavigationProp<
  MaterialTopTabNavigationProp<TabsParamList>,
  NativeStackNavigationProp<RootStackParamList>
>;

export default function ProfileScreen() {
  const { user, token, logout } = useAuth();
  const navigation = useNavigation<Nav>();
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const vehicles = await getMyVehicles(token);
      setVehicle(vehicles.items[0] ?? null);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo cargar el vehículo.";
      Alert.alert("Error", message);
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const stub = () => Alert.alert("Próximamente", "Esta función aún no está disponible.");

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <UceCard style={styles.profileCard}>
        <View style={styles.avatar} />
        <View style={{ flex: 1 }}>
          <Text style={styles.name}>{user?.full_name}</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <View style={styles.badgeRow}>
            <StatusBadge label="Conductor" bg="#E7EEFB" fg={colors.blue} />
            <StatusBadge label="Cuenta verificada" bg={colors.greenBg} fg="#1D7A34" />
          </View>
        </View>
      </UceCard>

      <UceCard>
        <View style={styles.headRow}>
          <Text style={styles.cardTitle}>Mi Vehículo</Text>
          <TouchableOpacity
            onPress={() => {
              if (vehicle) {
                navigation.navigate("EditarVehiculo", { vehicle });
              } else {
                Alert.alert("Sin vehículo", "Registra tu vehículo desde Inicio primero.");
              }
            }}
          >
            <Text style={styles.link}>Editar ›</Text>
          </TouchableOpacity>
        </View>
        {vehicle ? (
          <View style={styles.vehicleRow}>
            <PlateChip plate={vehicle.plate_text} small />
            <View>
              <Text style={styles.vehicleName}>
                {vehicle.brand} {vehicle.model}
              </Text>
              <Text style={styles.vehicleDetail}>Color: {vehicle.color}</Text>
            </View>
          </View>
        ) : (
          <Text style={styles.emptyText}>Aún no registras un vehículo.</Text>
        )}
      </UceCard>

      <UceCard style={styles.optionsCard}>
        <Option icon="👤" label="Datos personales" onPress={() => navigation.navigate("DatosPersonales")} />
        <Option icon="👥" label="Conductores autorizados" onPress={() => navigation.navigate("ConductoresAutorizados")} />
        <Option icon="🚗" label="Mis vehículos" onPress={() => navigation.navigate("MisVehiculos")} />
        <Option icon="🔔" label="Notificaciones" onPress={() => navigation.navigate("Notificaciones")} />
        <Option icon="🔒" label="Cambiar contraseña" onPress={() => navigation.navigate("CambiarContrasena")} />
        <Option icon="❓" label="Ayuda y reglamento" onPress={stub} last />
      </UceCard>

      <UceCard style={styles.optionsCard}>
        <Option icon="⏻" label="Cerrar sesión" danger onPress={logout} last />
      </UceCard>

      <Text style={styles.version}>UCEPark v1.0.0</Text>
    </ScrollView>
  );
}

function Option({
  icon,
  label,
  onPress,
  danger,
  last,
}: {
  icon: string;
  label: string;
  onPress: () => void;
  danger?: boolean;
  last?: boolean;
}) {
  return (
    <TouchableOpacity
      style={[styles.option, last ? null : styles.optionBorder]}
      onPress={onPress}
    >
      <View style={[styles.optionIcon, danger ? { backgroundColor: colors.redBg } : null]}>
        <Text>{icon}</Text>
      </View>
      <Text style={[styles.optionLabel, danger ? { color: colors.red } : null]}>{label}</Text>
      <Text style={styles.chevron}>›</Text>
    </TouchableOpacity>
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
  profileCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#C7D3E6",
    borderWidth: 3,
    borderColor: "#fff",
  },
  name: {
    fontFamily: fonts.extraBold,
    fontSize: 18,
    color: colors.navy,
  },
  email: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: colors.muted,
  },
  badgeRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 6,
  },
  cardTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 16.5,
    color: colors.navy,
  },
  headRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  link: {
    fontFamily: fonts.semiBold,
    fontSize: 13,
    color: colors.blue,
  },
  vehicleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  vehicleName: {
    fontFamily: fonts.extraBold,
    fontSize: 13,
    color: colors.navy,
  },
  vehicleDetail: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: "#51617C",
    marginTop: 2,
  },
  emptyText: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: colors.muted,
  },
  optionsCard: {
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  option: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 13,
  },
  optionBorder: {
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  optionIcon: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: "#EEF2F9",
    alignItems: "center",
    justifyContent: "center",
  },
  optionLabel: {
    flex: 1,
    fontFamily: fonts.semiBold,
    fontSize: 14,
    color: colors.ink,
  },
  chevron: {
    color: "#B6C0CF",
    fontFamily: fonts.extraBold,
  },
  version: {
    textAlign: "center",
    fontFamily: fonts.regular,
    fontSize: 11,
    color: colors.muted,
  },
});
