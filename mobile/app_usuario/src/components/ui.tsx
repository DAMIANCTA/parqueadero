import React, { useState } from "react";
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  TouchableOpacity,
  View,
} from "react-native";

import { colors, fonts, radii, spacing } from "../theme/theme";

export function UceCard({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: object;
}) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function TopBar({
  title,
  subtitle,
  onBack,
  right,
}: {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  right?: React.ReactNode;
}) {
  return (
    <View>
      <View style={styles.topBarRow}>
        {onBack ? (
          <TouchableOpacity style={styles.backBtn} onPress={onBack}>
            <Text style={styles.backBtnText}>{"‹"}</Text>
          </TouchableOpacity>
        ) : (
          <View style={{ width: 36 }} />
        )}
        <View style={{ flex: 1 }} />
        {right}
      </View>
      <Text style={styles.screenTitle}>{title}</Text>
      {subtitle ? <Text style={styles.screenSubtitle}>{subtitle}</Text> : null}
    </View>
  );
}

export function PrimaryButton({
  label,
  onPress,
  loading,
  disabled,
}: {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
}) {
  return (
    <TouchableOpacity
      style={[styles.btnBase, styles.btnPrimary, disabled ? styles.btnDisabled : null]}
      onPress={onPress}
      disabled={disabled || loading}
    >
      {loading ? (
        <ActivityIndicator color="#fff" />
      ) : (
        <Text style={styles.btnPrimaryText}>{label}</Text>
      )}
    </TouchableOpacity>
  );
}

export function GhostButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <TouchableOpacity style={[styles.btnBase, styles.btnGhost]} onPress={onPress}>
      <Text style={styles.btnGhostText}>{label}</Text>
    </TouchableOpacity>
  );
}

export function DangerGhostButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <TouchableOpacity style={[styles.btnBase, styles.btnDangerGhost]} onPress={onPress}>
      <Text style={styles.btnDangerGhostText}>{label}</Text>
    </TouchableOpacity>
  );
}

export function TextField({
  label,
  icon,
  error,
  suffix,
  ...inputProps
}: { label: string; icon?: string; error?: string; suffix?: string } & TextInputProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.input, error ? styles.inputError : null]}>
        {icon ? <Text style={styles.inputIcon}>{icon}</Text> : null}
        <TextInput
          style={styles.inputText}
          placeholderTextColor={colors.muted}
          {...inputProps}
        />
        {suffix ? <Text style={styles.inputSuffix}>{suffix}</Text> : null}
      </View>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
    </View>
  );
}

export function SelectField({
  label,
  value,
  placeholder,
  options,
  onChange,
  error,
  disabled,
}: {
  label: string;
  value: string;
  placeholder?: string;
  options: string[];
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TouchableOpacity
        style={[styles.input, error ? styles.inputError : null, disabled ? styles.inputDisabled : null]}
        onPress={() => !disabled && setOpen(true)}
        activeOpacity={disabled ? 1 : 0.8}
      >
        <Text style={value ? styles.inputText : styles.inputPlaceholder}>
          {value || placeholder || "Selecciona una opción"}
        </Text>
        <Text style={styles.selectChevron}>{"▾"}</Text>
      </TouchableOpacity>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
      <Modal visible={open} transparent animationType="fade" onRequestClose={() => setOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setOpen(false)}>
          <View style={styles.modalSheet}>
            <Text style={styles.modalTitle}>{label}</Text>
            <ScrollView style={{ maxHeight: 320 }}>
              {options.map((option) => (
                <TouchableOpacity
                  key={option}
                  style={styles.modalOption}
                  onPress={() => {
                    onChange(option);
                    setOpen(false);
                  }}
                >
                  <Text style={styles.modalOptionText}>{option}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

export function formatPlateWithDash(plate: string): string {
  const cleaned = plate.toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (cleaned.length <= 3) return cleaned;
  return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 7)}`;
}

export function PlateChip({ plate, small }: { plate: string; small?: boolean }) {
  return (
    <View style={[stylesPlate.plate, small ? stylesPlate.plateSmall : null]}>
      <Text style={stylesPlate.plateTop}>{"🇪🇨"} ECUADOR</Text>
      <Text style={[stylesPlate.plateNum, small ? stylesPlate.plateNumSmall : null]}>
        {formatPlateWithDash(plate)}
      </Text>
      <Text style={stylesPlate.plateBottom}>PICHINCHA</Text>
    </View>
  );
}

export function StatusBadge({
  label,
  bg,
  fg,
}: {
  label: string;
  bg: string;
  fg: string;
}) {
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color: fg }]}>{label}</Text>
    </View>
  );
}

export function PersonRow({
  name,
  role,
  highlight,
  right,
}: {
  name: string;
  role: string;
  highlight?: boolean;
  right?: React.ReactNode;
}) {
  return (
    <View style={[styles.person, highlight ? { backgroundColor: colors.greenBg } : null]}>
      <View style={styles.personAvatar} />
      <View style={{ flex: 1 }}>
        <Text style={styles.personName}>{name}</Text>
        <Text style={styles.personRole}>{role}</Text>
      </View>
      {right}
    </View>
  );
}

export function HistoryRow({
  type,
  plate,
  meta,
}: {
  type: "IN" | "OUT";
  plate: string;
  meta: string;
}) {
  const isIn = type === "IN";
  return (
    <View style={[styles.row, { backgroundColor: isIn ? colors.greenBg : colors.redBg }]}>
      <View style={[styles.rowIcon, { backgroundColor: isIn ? colors.green : colors.red }]}>
        <Text style={styles.rowIconText}>{isIn ? "↓" : "↑"}</Text>
      </View>
      <Text style={styles.rowLabel}>{isIn ? "Ingreso" : "Salida"}</Text>
      <Text style={styles.rowSep}>{"|"}</Text>
      <Text style={styles.rowPlate} numberOfLines={1}>
        {plate}
      </Text>
      <View style={{ flex: 1 }} />
      <Text style={styles.rowMeta}>{meta}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.card,
    padding: spacing.lg,
    shadowColor: colors.navy,
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  topBarRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
  },
  backBtnText: {
    fontFamily: fonts.bold,
    color: colors.navy,
    fontSize: 20,
  },
  screenTitle: {
    fontFamily: fonts.extraBold,
    color: colors.navy,
    fontSize: 25,
    marginTop: spacing.sm,
  },
  screenSubtitle: {
    fontFamily: fonts.regular,
    color: colors.muted,
    fontSize: 14,
    marginTop: 3,
  },
  btnBase: {
    width: "100%",
    paddingVertical: 14,
    borderRadius: radii.button,
    alignItems: "center",
    justifyContent: "center",
  },
  btnPrimary: {
    backgroundColor: colors.navy2,
  },
  btnPrimaryText: {
    color: "#fff",
    fontFamily: fonts.extraBold,
    fontSize: 15.5,
  },
  btnDisabled: {
    opacity: 0.6,
  },
  btnGhost: {
    backgroundColor: "#fff",
    borderWidth: 1.5,
    borderColor: colors.line,
  },
  btnGhostText: {
    color: colors.navy,
    fontFamily: fonts.bold,
    fontSize: 15,
  },
  btnDangerGhost: {
    backgroundColor: "#fff",
    borderWidth: 1.5,
    borderColor: "#F3CDCD",
  },
  btnDangerGhostText: {
    color: colors.red,
    fontFamily: fonts.bold,
    fontSize: 15,
  },
  field: {
    marginBottom: 13,
  },
  fieldLabel: {
    fontFamily: fonts.bold,
    fontSize: 12.5,
    color: colors.navy,
    marginBottom: 6,
  },
  input: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#fff",
    borderWidth: 1.5,
    borderColor: colors.line,
    borderRadius: radii.input,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  inputError: {
    borderColor: colors.red,
  },
  inputDisabled: {
    backgroundColor: "#F5F6F8",
  },
  inputIcon: {
    fontSize: 16,
  },
  inputText: {
    flex: 1,
    fontFamily: fonts.regular,
    fontSize: 14,
    color: colors.ink,
    padding: 0,
  },
  inputSuffix: {
    fontFamily: fonts.medium,
    fontSize: 13,
    color: colors.muted,
  },
  inputPlaceholder: {
    flex: 1,
    fontFamily: fonts.regular,
    fontSize: 14,
    color: colors.muted,
  },
  selectChevron: {
    color: colors.muted,
    fontSize: 14,
  },
  errorText: {
    fontFamily: fonts.medium,
    fontSize: 11.5,
    color: colors.red,
    marginTop: 5,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(20,30,50,0.45)",
    justifyContent: "flex-end",
  },
  modalSheet: {
    backgroundColor: "#fff",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 18,
    paddingBottom: 30,
  },
  modalTitle: {
    fontFamily: fonts.extraBold,
    fontSize: 15,
    color: colors.navy,
    marginBottom: 10,
  },
  modalOption: {
    paddingVertical: 13,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  modalOptionText: {
    fontFamily: fonts.medium,
    fontSize: 14.5,
    color: colors.ink,
  },
  badge: {
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 10,
    alignSelf: "flex-start",
  },
  badgeText: {
    fontFamily: fonts.extraBold,
    fontSize: 10.5,
  },
  person: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: colors.chip,
    borderRadius: 14,
    padding: 10,
  },
  personAvatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "#C7D3E6",
    borderWidth: 2,
    borderColor: "#fff",
  },
  personName: {
    fontFamily: fonts.extraBold,
    fontSize: 13.5,
    color: colors.navy,
  },
  personRole: {
    fontFamily: fonts.regular,
    fontSize: 11.5,
    color: colors.muted,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderRadius: 12,
    padding: 10,
  },
  rowIcon: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
  },
  rowIconText: {
    color: "#fff",
    fontFamily: fonts.extraBold,
    fontSize: 12,
  },
  rowLabel: {
    fontFamily: fonts.extraBold,
    fontSize: 11.5,
    color: colors.ink,
  },
  rowSep: {
    color: "#C3CBD8",
    marginHorizontal: 2,
  },
  rowPlate: {
    fontFamily: fonts.medium,
    fontSize: 11.5,
    color: colors.ink,
    flexShrink: 1,
  },
  rowMeta: {
    fontFamily: fonts.regular,
    fontSize: 11.5,
    color: "#51617C",
  },
});

const stylesPlate = StyleSheet.create({
  plate: {
    width: 190,
    alignSelf: "center",
    backgroundColor: "#EDEDED",
    borderWidth: 2.5,
    borderColor: "#555",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingTop: 6,
    paddingBottom: 8,
    alignItems: "center",
  },
  plateSmall: {
    width: 142,
  },
  plateTop: {
    fontSize: 9,
    fontFamily: fonts.extraBold,
    letterSpacing: 2,
    color: "#333",
  },
  plateNum: {
    fontSize: 30,
    fontFamily: fonts.extraBold,
    letterSpacing: 2,
    color: "#1A1A1A",
  },
  plateNumSmall: {
    fontSize: 19,
    letterSpacing: 1.5,
  },
  plateBottom: {
    fontSize: 8,
    fontFamily: fonts.bold,
    letterSpacing: 2.5,
    color: "#444",
  },
});
