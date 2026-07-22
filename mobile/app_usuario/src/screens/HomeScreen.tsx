import React, { useCallback, useState } from "react";
import { Alert, Image, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useFocusEffect, useNavigation } from "@react-navigation/native";
import type { MaterialTopTabNavigationProp } from "@react-navigation/material-top-tabs";

import { useAuth } from "../context/AuthContext";
import { FaceCaptureCamera } from "../components/FaceCaptureCamera";
import {
  AccessHistoryItem,
  ApiError,
  Member,
  Vehicle,
  enrollMyFace,
  getMyActiveSession,
  getMyAuthorizedDrivers,
  getMyHistory,
  getMyVehicles,
  registerMyVehicle,
} from "../services/apiClient";
import { GhostButton, HistoryRow, PersonRow, PlateChip, PrimaryButton, SelectField, TextField, UceCard } from "../components/ui";
import { colors, fonts, spacing } from "../theme/theme";
import { CAR_BRANDS, CAR_BRAND_NAMES, CAR_COLORS } from "../data/vehicleCatalog";
import { PLATE_REGEX, maskPlateInput } from "../utils/plate";
import type { TabsParamList } from "../navigation/TabsNavigator";

type Nav = MaterialTopTabNavigationProp<TabsParamList>;

export default function HomeScreen() {
  const { user, token } = useAuth();
  const navigation = useNavigation<Nav>();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [authorizedPeople, setAuthorizedPeople] = useState<Member[]>([]);
  const [activeSession, setActiveSession] = useState<boolean>(false);
  const [recentHistory, setRecentHistory] = useState<AccessHistoryItem[]>([]);
  const [setupStep, setSetupStep] = useState<"idle" | "vehicle" | "face">("idle");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const vehicles = await getMyVehicles(token);
      const myVehicle = vehicles.items[0] ?? null;
      setVehicle(myVehicle);

      if (myVehicle) {
        const [drivers, session, history] = await Promise.all([
          getMyAuthorizedDrivers(token),
          getMyActiveSession(token),
          getMyHistory(token, 3),
        ]);
        setAuthorizedPeople(drivers.authorized_people);
        setActiveSession(session.active);
        setRecentHistory(history.items);
      } else {
        setAuthorizedPeople([]);
        setActiveSession(false);
        setRecentHistory([]);
      }
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo cargar la información.";
      Alert.alert("Error", message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  if (loading) {
    return (
      <View style={styles.screen}>
        <Text style={styles.loadingText}>Cargando…</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View>
        <Text style={styles.greeting}>¡Hola, {user?.full_name}!</Text>
        <Text style={styles.subGreeting}>Bienvenido al sistema de Parqueo UCE</Text>
      </View>

      {vehicle ? (
        <>
          <UceCard>
            <Text style={styles.cardTitle}>Perfiles Permitidos para esta Placa</Text>
            {authorizedPeople.length === 0 ? (
              <Text style={styles.emptyText}>Aún no hay conductores autorizados.</Text>
            ) : (
              <View style={{ gap: 8 }}>
                {authorizedPeople.map((person) => (
                  <PersonRow
                    key={person.id}
                    name={person.full_name}
                    role={person.user_id === user?.id ? "Propietario" : "Conductor Autorizado"}
                    highlight={person.user_id === user?.id}
                  />
                ))}
              </View>
            )}
          </UceCard>

          <UceCard>
            <Text style={styles.cardTitle}>Vehículo Registrado</Text>
            <Text style={styles.vehicleSub}>
              🚗 {vehicle.brand} {vehicle.model}
              {vehicle.color ? ` · ${vehicle.color}` : ""}
            </Text>
            <PlateChip plate={vehicle.plate_text} small />
          </UceCard>

          <UceCard>
            <View style={styles.headRow}>
              <Text style={styles.cardTitle}>Historial Reciente</Text>
              <TouchableOpacity onPress={() => navigation.navigate("Historial")}>
                <Text style={styles.link}>Ver historial ›</Text>
              </TouchableOpacity>
            </View>
            {recentHistory.length === 0 ? (
              <Text style={styles.emptyText}>Todavía no tienes movimientos.</Text>
            ) : (
              <View style={{ gap: 6 }}>
                {recentHistory.map((item) => (
                  <HistoryRow
                    key={item.session_id}
                    type={item.exit_time ? "OUT" : "IN"}
                    plate={item.plate_text}
                    meta={(item.exit_time ?? item.entry_time ?? "").slice(0, 16).replace("T", " ")}
                  />
                ))}
              </View>
            )}
          </UceCard>

          <UceCard>
            <View style={styles.headRow}>
              <Text style={styles.cardTitle}>Estado de Vehículo</Text>
            </View>
            <View
              style={[
                styles.statusBanner,
                { backgroundColor: activeSession ? colors.redBg : colors.greenBg },
              ]}
            >
              <Text style={styles.statusIcon}>🚗</Text>
              <View>
                <Text style={[styles.statusTitle, { color: activeSession ? colors.red : colors.green }]}>
                  {activeSession ? "En Parqueo" : "Fuera del Parqueo"}
                </Text>
                <Text style={styles.statusBody}>
                  {activeSession
                    ? "Tu vehículo se encuentra dentro de la institución."
                    : "Tu vehículo no se encuentra dentro de la institución."}
                </Text>
              </View>
            </View>
          </UceCard>
        </>
      ) : (
        <UceCard>
          {setupStep === "face" ? (
            <>
              <Text style={styles.cardTitle}>Registra tu rostro</Text>
              <FaceEnrollmentStep
                token={token!}
                onDone={() => {
                  setSetupStep("idle");
                  load();
                }}
              />
            </>
          ) : (
            <>
              <Text style={styles.cardTitle}>Registra tu vehículo</Text>
              <Text style={styles.emptyText}>
                Aún no tienes un vehículo registrado. Regístralo para ver tu estado e historial.
              </Text>
              {setupStep === "vehicle" ? (
                <RegisterVehicleForm token={token!} onDone={() => setSetupStep("face")} />
              ) : (
                <PrimaryButton label="Registrar mi vehículo" onPress={() => setSetupStep("vehicle")} />
              )}
            </>
          )}
        </UceCard>
      )}
    </ScrollView>
  );
}

function RegisterVehicleForm({ token, onDone }: { token: string; onDone: () => void }) {
  const [plate, setPlate] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [color, setColor] = useState("");
  const [plateError, setPlateError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const onSubmit = async () => {
    if (!PLATE_REGEX.test(plate)) {
      setPlateError("Usa el formato AAA-1234.");
      return;
    }
    if (!brand || !model || !color) {
      Alert.alert("Faltan datos", "Selecciona marca, modelo y color.");
      return;
    }
    setLoading(true);
    try {
      await registerMyVehicle(token, { plate_text: plate, brand, model, color });
      onDone();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo registrar el vehículo.";
      Alert.alert("Error", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ marginTop: spacing.sm }}>
      <TextField
        label="Placa"
        placeholder="AAA-1234"
        autoCapitalize="characters"
        maxLength={8}
        value={plate}
        onChangeText={(v) => {
          setPlate(maskPlateInput(v));
          setPlateError(undefined);
        }}
        error={plateError}
      />
      <SelectField
        label="Marca"
        placeholder="Selecciona una marca"
        options={CAR_BRAND_NAMES}
        value={brand}
        onChange={(value) => {
          setBrand(value);
          setModel("");
        }}
      />
      <SelectField
        label="Modelo"
        placeholder={brand ? "Selecciona un modelo" : "Primero selecciona una marca"}
        options={brand ? CAR_BRANDS[brand] : []}
        value={model}
        onChange={setModel}
        disabled={!brand}
      />
      <SelectField label="Color" placeholder="Selecciona un color" options={CAR_COLORS} value={color} onChange={setColor} />
      <PrimaryButton label="Guardar vehículo" onPress={onSubmit} loading={loading} />
    </View>
  );
}

function FaceEnrollmentStep({ token, onDone }: { token: string; onDone: () => void }) {
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const onConfirm = async () => {
    if (!photoUri) return;
    setLoading(true);
    try {
      await enrollMyFace(token, { uri: photoUri, fileName: "face.jpg", mimeType: "image/jpeg" });
      Alert.alert("Listo", "Tu rostro fue registrado correctamente.");
      onDone();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo registrar tu rostro.";
      // Se limpia la foto para forzar una nueva toma en vez de reintentar
      // subiendo la misma imagen que ya fue rechazada.
      setPhotoUri(null);
      Alert.alert("Intenta de nuevo", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ marginTop: spacing.sm, alignItems: "center", gap: 12 }}>
      <Text style={styles.emptyText}>
        Toma una foto de tu rostro para que seguridad pueda verificarte en la garita.
      </Text>
      {photoUri ? <Image source={{ uri: photoUri }} style={styles.facePreview} /> : null}
      <View style={{ width: "100%", gap: 10 }}>
        <PrimaryButton label={photoUri ? "Tomar otra foto" : "Tomar foto"} onPress={() => setCameraOpen(true)} />
        {photoUri ? (
          <PrimaryButton label="Confirmar y continuar" onPress={onConfirm} loading={loading} />
        ) : null}
        <GhostButton label="Hacerlo después" onPress={onDone} />
      </View>
      <FaceCaptureCamera
        visible={cameraOpen}
        onCancel={() => setCameraOpen(false)}
        onCaptured={(uri) => {
          setPhotoUri(uri);
          setCameraOpen(false);
        }}
      />
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
  loadingText: {
    marginTop: 80,
    textAlign: "center",
    fontFamily: fonts.regular,
    color: colors.muted,
  },
  greeting: {
    fontFamily: fonts.extraBold,
    fontSize: 25,
    color: colors.navy,
  },
  subGreeting: {
    fontFamily: fonts.regular,
    fontSize: 14,
    color: colors.muted,
    marginTop: 3,
  },
  cardTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 14,
    color: colors.navy,
    marginBottom: 9,
  },
  headRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 9,
  },
  link: {
    fontFamily: fonts.semiBold,
    fontSize: 11.5,
    color: colors.blue,
  },
  emptyText: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: colors.muted,
  },
  facePreview: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: colors.chip,
  },
  vehicleSub: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: "#51617C",
    marginBottom: 9,
  },
  statusBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderRadius: 14,
    padding: 12,
  },
  statusIcon: {
    fontSize: 22,
    width: 42,
    height: 42,
    textAlign: "center",
    textAlignVertical: "center",
  },
  statusTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 16.5,
  },
  statusBody: {
    fontFamily: fonts.regular,
    fontSize: 11,
    color: "#51617C",
    marginTop: 2,
  },
});
