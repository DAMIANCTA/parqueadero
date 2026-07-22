import React, { useCallback, useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError, Member, enrollMyFace, getMyAuthorizedDrivers } from "../services/apiClient";
import { FaceCaptureCamera } from "../components/FaceCaptureCamera";
import { GhostButton, PersonRow, StatusBadge, TopBar, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "ConductoresAutorizados">;

const MAX_AUTHORIZED_DRIVERS = 3;

export default function AuthorizedDriversScreen({ navigation }: Props) {
  const { user, token } = useAuth();
  const [people, setPeople] = useState<Member[]>([]);
  const [plate, setPlate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [enrolling, setEnrolling] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const response = await getMyAuthorizedDrivers(token);
      setPeople(response.authorized_people);
      setPlate(response.vehicle?.plate_text ?? null);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo cargar la información.";
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

  const onFaceCaptured = async (uri: string) => {
    setCameraOpen(false);
    setEnrolling(true);
    try {
      await enrollMyFace(token!, { uri, fileName: "face.jpg", mimeType: "image/jpeg" });
      Alert.alert("Listo", "Tu rostro fue registrado correctamente.");
      load();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo registrar tu rostro.";
      Alert.alert("Intenta de nuevo", message);
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <TopBar
          title="Conductores"
          subtitle={plate ? `Perfiles autorizados para la placa ${plate}` : "Aún no tienes un vehículo registrado"}
          onBack={() => navigation.goBack()}
        />

        <UceCard>
          <View style={styles.headRow}>
            <Text style={styles.cardTitle}>Activos</Text>
            <StatusBadge
              label={`${people.length} de ${MAX_AUTHORIZED_DRIVERS} permitidos`}
              bg={colors.greenBg}
              fg="#1D7A34"
            />
          </View>
          {loading ? (
            <Text style={styles.emptyText}>Cargando…</Text>
          ) : people.length === 0 ? (
            <Text style={styles.emptyText}>No hay conductores autorizados todavía.</Text>
          ) : (
            <View style={{ gap: 9 }}>
              {people.map((person) => {
                const isMe = person.user_id === user?.id;
                return (
                  <View key={person.id}>
                    <PersonRow
                      name={person.full_name}
                      role={isMe ? "Propietario · Tú" : "Conductor Autorizado"}
                      highlight={isMe}
                      right={
                        person.has_face_profile ? (
                          <StatusBadge label="Rostro registrado" bg={colors.greenBg} fg="#1D7A34" />
                        ) : (
                          <StatusBadge label="Sin rostro" bg={colors.amberBg} fg="#A86A13" />
                        )
                      }
                    />
                    {isMe && !person.has_face_profile ? (
                      <View style={{ marginTop: 8 }}>
                        <GhostButton
                          label="Registrar mi rostro"
                          onPress={() => setCameraOpen(true)}
                        />
                      </View>
                    ) : null}
                  </View>
                );
              })}
            </View>
          )}
        </UceCard>

        <UceCard style={styles.infoCard}>
          <Text style={styles.infoText}>
            ℹ️ Cada placa admite hasta {MAX_AUTHORIZED_DRIVERS} conductores autorizados. Agregar o quitar
            conductores estará disponible próximamente.
          </Text>
        </UceCard>
      </ScrollView>
      <FaceCaptureCamera visible={cameraOpen} onCancel={() => setCameraOpen(false)} onCaptured={onFaceCaptured} />
      {enrolling ? (
        <View style={styles.enrollingOverlay}>
          <Text style={styles.enrollingText}>Registrando tu rostro…</Text>
        </View>
      ) : null}
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
    marginBottom: 12,
  },
  cardTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 16.5,
    color: colors.navy,
  },
  emptyText: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: colors.muted,
  },
  infoCard: {
    backgroundColor: "#EEF2F9",
    shadowOpacity: 0,
    elevation: 0,
  },
  infoText: {
    fontFamily: fonts.regular,
    fontSize: 12,
    color: "#51617C",
    lineHeight: 18,
  },
  enrollingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.4)",
    alignItems: "center",
    justifyContent: "center",
  },
  enrollingText: {
    fontFamily: fonts.semiBold,
    fontSize: 14,
    color: "#fff",
  },
});
