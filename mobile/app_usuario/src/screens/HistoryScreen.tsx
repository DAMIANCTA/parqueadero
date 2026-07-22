import React, { useCallback, useMemo, useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";

import { useAuth } from "../context/AuthContext";
import { AccessHistoryItem, ApiError, getMyHistory } from "../services/apiClient";
import { GhostButton, HistoryRow, TopBar } from "../components/ui";
import { colors, fonts } from "../theme/theme";

type Filter = "ALL" | "IN" | "OUT";

type FlatEvent = {
  key: string;
  type: "IN" | "OUT";
  plate: string;
  time: string;
};

function flattenHistory(items: AccessHistoryItem[]): FlatEvent[] {
  const events: FlatEvent[] = [];
  for (const item of items) {
    if (item.entry_time) {
      events.push({ key: `${item.session_id}-in`, type: "IN", plate: item.plate_text, time: item.entry_time });
    }
    if (item.exit_time) {
      events.push({ key: `${item.session_id}-out`, type: "OUT", plate: item.plate_text, time: item.exit_time });
    }
  }
  return events.sort((a, b) => b.time.localeCompare(a.time));
}

function formatDateLabel(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString("es-EC", { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
}

function formatTime(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleTimeString("es-EC", { hour: "2-digit", minute: "2-digit" });
}

export default function HistoryScreen() {
  const { token } = useAuth();
  const [events, setEvents] = useState<FlatEvent[]>([]);
  const [filter, setFilter] = useState<Filter>("ALL");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const history = await getMyHistory(token, 200);
      setEvents(flattenHistory(history.items));
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo cargar el historial.";
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

  const filtered = useMemo(() => {
    if (filter === "ALL") return events;
    return events.filter((event) => event.type === filter);
  }, [events, filter]);

  const grouped = useMemo(() => {
    const groups = new Map<string, FlatEvent[]>();
    for (const event of filtered) {
      const dayKey = event.time.slice(0, 10);
      const list = groups.get(dayKey) ?? [];
      list.push(event);
      groups.set(dayKey, list);
    }
    return Array.from(groups.entries());
  }, [filtered]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <TopBar title="Historial" subtitle="Tus ingresos y salidas" />

      <View style={styles.chips}>
        <Chip label="Todos" active={filter === "ALL"} onPress={() => setFilter("ALL")} />
        <Chip label="Ingresos" active={filter === "IN"} onPress={() => setFilter("IN")} />
        <Chip label="Salidas" active={filter === "OUT"} onPress={() => setFilter("OUT")} />
      </View>

      {loading ? (
        <Text style={styles.emptyText}>Cargando…</Text>
      ) : grouped.length === 0 ? (
        <Text style={styles.emptyText}>No hay movimientos para mostrar.</Text>
      ) : (
        grouped.map(([day, dayEvents]) => (
          <View key={day} style={{ gap: 8 }}>
            <Text style={styles.dateLabel}>{formatDateLabel(day)}</Text>
            <View style={{ gap: 8 }}>
              {dayEvents.map((event) => (
                <HistoryRow key={event.key} type={event.type} plate={event.plate} meta={formatTime(event.time)} />
              ))}
            </View>
          </View>
        ))
      )}

      <GhostButton
        label="⬇  Descargar reporte (PDF)"
        onPress={() => Alert.alert("Próximamente", "La descarga de reportes aún no está disponible.")}
      />
    </ScrollView>
  );
}

function Chip({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <TouchableOpacity style={[styles.chip, active ? styles.chipActive : null]} onPress={onPress}>
      <Text style={[styles.chipText, active ? styles.chipTextActive : null]}>{label}</Text>
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
    gap: 10,
  },
  chips: {
    flexDirection: "row",
    gap: 8,
  },
  chip: {
    backgroundColor: "#fff",
    borderWidth: 1.5,
    borderColor: colors.line,
    paddingHorizontal: 13,
    paddingVertical: 7,
    borderRadius: 20,
  },
  chipActive: {
    backgroundColor: colors.navy2,
    borderColor: colors.navy2,
  },
  chipText: {
    fontFamily: fonts.bold,
    fontSize: 12.5,
    color: "#51617C",
  },
  chipTextActive: {
    color: "#fff",
  },
  dateLabel: {
    fontFamily: fonts.extraBold,
    fontSize: 12,
    color: "#8493A8",
    letterSpacing: 0.6,
    textTransform: "uppercase",
    marginTop: 4,
  },
  emptyText: {
    fontFamily: fonts.regular,
    fontSize: 13,
    color: colors.muted,
    textAlign: "center",
    marginTop: 24,
  },
});
