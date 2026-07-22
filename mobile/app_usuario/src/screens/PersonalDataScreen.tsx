import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { TopBar, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "DatosPersonales">;

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

export default function PersonalDataScreen({ navigation }: Props) {
  const { user } = useAuth();

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <TopBar title="Datos Personales" subtitle="Tu información registrada" onBack={() => navigation.goBack()} />
        <UceCard>
          <InfoRow label="Nombres completos" value={user?.full_name ?? "-"} />
          <InfoRow label="Usuario" value={user?.username ?? "-"} />
          <InfoRow label="Correo institucional" value={user?.email ?? "-"} />
          <InfoRow label="Cédula" value={user?.document_number ?? "-"} />
          <InfoRow label="Teléfono" value={user?.phone ?? "-"} />
        </UceCard>
        <Text style={styles.note}>
          Estos datos se registraron al crear tu cuenta. Si necesitas corregir algo, contacta a seguridad de la UCE.
        </Text>
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
  row: {
    paddingVertical: 11,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  label: {
    fontFamily: fonts.bold,
    fontSize: 11.5,
    color: colors.muted,
    marginBottom: 3,
  },
  value: {
    fontFamily: fonts.semiBold,
    fontSize: 15,
    color: colors.ink,
  },
  note: {
    fontFamily: fonts.regular,
    fontSize: 12,
    color: colors.muted,
    textAlign: "center",
  },
});
