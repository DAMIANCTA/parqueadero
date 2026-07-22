import React, { useCallback, useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError, Vehicle, getMyVehicles } from "../services/apiClient";
import { PlateChip, TopBar, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "MisVehiculos">;

export default function MyVehiclesScreen({ navigation }: Props) {
  const { token } = useAuth();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const response = await getMyVehicles(token);
      setVehicles(response.items);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo cargar tu vehículo.";
      Alert.alert("Error", message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <TopBar title="Mis Vehículos" subtitle="Placas registradas a tu nombre" onBack={() => navigation.goBack()} />
        {loading ? (
          <Text style={styles.emptyText}>Cargando…</Text>
        ) : vehicles.length === 0 ? (
          <UceCard>
            <Text style={styles.emptyText}>Aún no tienes un vehículo registrado.</Text>
          </UceCard>
        ) : (
          vehicles.map((vehicle) => (
            <UceCard key={vehicle.id}>
              <View style={styles.headRow}>
                <Text style={styles.cardTitle}>
                  {vehicle.brand} {vehicle.model}
                </Text>
                <TouchableOpacity onPress={() => navigation.navigate("EditarVehiculo", { vehicle })}>
                  <Text style={styles.link}>Editar ›</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.detail}>Color: {vehicle.color}</Text>
              <View style={{ marginTop: 10 }}>
                <PlateChip plate={vehicle.plate_text} small />
              </View>
            </UceCard>
          ))
        )}
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
  headRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  cardTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 15,
    color: colors.navy,
  },
  link: {
    fontFamily: fonts.semiBold,
    fontSize: 13,
    color: colors.blue,
  },
  detail: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: "#51617C",
  },
  emptyText: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: colors.muted,
    textAlign: "center",
  },
});
