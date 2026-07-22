import React from "react";
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { TopBar, UceCard } from "../components/ui";
import { colors, fonts } from "../theme/theme";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "Notificaciones">;

type SampleNotification = {
  id: string;
  icon: string;
  iconBg: string;
  title: string;
  body: string;
  time: string;
  day: string;
};

// Datos de ejemplo: todavia no existe un backend de notificaciones.
const SAMPLE_NOTIFICATIONS: SampleNotification[] = [
  {
    id: "1",
    icon: "✅",
    iconBg: colors.greenBg,
    title: "Ingreso registrado",
    body: "Tu vehículo ingresó al parqueadero Central.",
    time: "07:52 AM",
    day: "Hoy",
  },
  {
    id: "2",
    icon: "⚠️",
    iconBg: colors.amberBg,
    title: "Parqueadero Central casi lleno",
    body: "Quedan menos del 10% de plazas. Considera la sede Medicina o Cowork.",
    time: "07:15 AM",
    day: "Hoy",
  },
  {
    id: "3",
    icon: "🚗",
    iconBg: colors.redBg,
    title: "Salida registrada",
    body: "Tu vehículo salió del parqueadero Central.",
    time: "06:10 PM",
    day: "Ayer",
  },
  {
    id: "4",
    icon: "👥",
    iconBg: "#E7EEFB",
    title: "Conductor autorizado",
    body: "Un conductor autorizado utilizó el vehículo para ingresar.",
    time: "07:45 AM",
    day: "Ayer",
  },
  {
    id: "5",
    icon: "⏰",
    iconBg: colors.amberBg,
    title: "Renovación de permiso",
    body: "Tu permiso semestral vence pronto. Renuévalo desde Mi Perfil.",
    time: "08:00 AM",
    day: "13 Jul",
  },
];

export default function NotificationsScreen({ navigation }: Props) {
  const grouped = SAMPLE_NOTIFICATIONS.reduce<Record<string, SampleNotification[]>>((acc, item) => {
    acc[item.day] = acc[item.day] ?? [];
    acc[item.day].push(item);
    return acc;
  }, {});

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <TopBar
          title="Notificaciones"
          subtitle="Contenido de ejemplo — próximamente en vivo"
          onBack={() => navigation.goBack()}
          right={
            <TouchableOpacity onPress={() => Alert.alert("Próximamente", "Esta función aún no está disponible.")}>
              <Text style={styles.markRead}>Marcar leídas</Text>
            </TouchableOpacity>
          }
        />

        {Object.entries(grouped).map(([day, items]) => (
          <View key={day} style={{ gap: 8 }}>
            <Text style={styles.dateLabel}>{day}</Text>
            <View style={{ gap: 10 }}>
              {items.map((item) => (
                <UceCard key={item.id} style={styles.notif}>
                  <View style={[styles.notifIcon, { backgroundColor: item.iconBg }]}>
                    <Text>{item.icon}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.notifTitle}>{item.title}</Text>
                    <Text style={styles.notifBody}>{item.body}</Text>
                    <Text style={styles.notifTime}>{item.time}</Text>
                  </View>
                </UceCard>
              ))}
            </View>
          </View>
        ))}
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
  markRead: {
    fontFamily: fonts.semiBold,
    fontSize: 12,
    color: colors.blue,
  },
  dateLabel: {
    fontFamily: fonts.extraBold,
    fontSize: 12,
    color: "#8493A8",
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  notif: {
    flexDirection: "row",
    gap: 11,
    padding: 13,
  },
  notifIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  notifTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 13.5,
    color: colors.navy,
  },
  notifBody: {
    fontFamily: fonts.regular,
    fontSize: 12,
    color: "#51617C",
    marginTop: 2,
    lineHeight: 16,
  },
  notifTime: {
    fontFamily: fonts.regular,
    fontSize: 11,
    color: "#9AA7B8",
    marginTop: 4,
  },
});
