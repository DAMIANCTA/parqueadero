import React, { useState } from "react";
import { Alert, ScrollView, StyleSheet, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { ApiError, updateMyVehicle } from "../services/apiClient";
import { PrimaryButton, SelectField, TextField, TopBar, UceCard } from "../components/ui";
import { colors } from "../theme/theme";
import { CAR_BRANDS, CAR_BRAND_NAMES, CAR_COLORS } from "../data/vehicleCatalog";
import { PLATE_REGEX, maskPlateInput } from "../utils/plate";
import type { RootStackParamList } from "../navigation/RootNavigator";

type Props = NativeStackScreenProps<RootStackParamList, "EditarVehiculo">;

export default function EditVehicleScreen({ navigation, route }: Props) {
  const { token } = useAuth();
  const { vehicle } = route.params;
  const [plate, setPlate] = useState(maskPlateInput(vehicle.plate_text));
  const [brand, setBrand] = useState(vehicle.brand);
  const [model, setModel] = useState(vehicle.model);
  const [color, setColor] = useState(vehicle.color);
  const [plateError, setPlateError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const brandModels = CAR_BRANDS[brand] ?? [];

  const onSubmit = async () => {
    if (!PLATE_REGEX.test(plate)) {
      setPlateError("Usa el formato AAA-1234.");
      return;
    }
    setLoading(true);
    try {
      await updateMyVehicle(token!, { plate_text: plate, brand, model, color });
      Alert.alert("Listo", "Tu vehículo fue actualizado.");
      navigation.goBack();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "No se pudo actualizar el vehículo.";
      Alert.alert("Error", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <TopBar title="Editar Vehículo" subtitle="Actualiza la placa o los detalles" onBack={() => navigation.goBack()} />
        <UceCard>
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
            options={brandModels}
            value={model}
            onChange={setModel}
            disabled={!brand}
          />
          <SelectField label="Color" placeholder="Selecciona un color" options={CAR_COLORS} value={color} onChange={setColor} />
          <PrimaryButton label="Guardar cambios" onPress={onSubmit} loading={loading} />
        </UceCard>
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
});
