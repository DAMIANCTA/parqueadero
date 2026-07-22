import React from "react";
import { ActivityIndicator, View } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { useAuth } from "../context/AuthContext";
import { colors } from "../theme/theme";
import type { Vehicle } from "../services/apiClient";
import LoginScreen from "../screens/LoginScreen";
import RegisterScreen from "../screens/RegisterScreen";
import AuthorizedDriversScreen from "../screens/AuthorizedDriversScreen";
import NotificationsScreen from "../screens/NotificationsScreen";
import PersonalDataScreen from "../screens/PersonalDataScreen";
import MyVehiclesScreen from "../screens/MyVehiclesScreen";
import EditVehicleScreen from "../screens/EditVehicleScreen";
import ChangePasswordScreen from "../screens/ChangePasswordScreen";
import TabsNavigator from "./TabsNavigator";

export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Tabs: undefined;
  ConductoresAutorizados: undefined;
  Notificaciones: undefined;
  DatosPersonales: undefined;
  MisVehiculos: undefined;
  EditarVehiculo: { vehicle: Vehicle };
  CambiarContrasena: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  const { isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.bgApp }}>
        <ActivityIndicator color={colors.navy} size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          <>
            <Stack.Screen name="Tabs" component={TabsNavigator} />
            <Stack.Screen name="ConductoresAutorizados" component={AuthorizedDriversScreen} />
            <Stack.Screen name="Notificaciones" component={NotificationsScreen} />
            <Stack.Screen name="DatosPersonales" component={PersonalDataScreen} />
            <Stack.Screen name="MisVehiculos" component={MyVehiclesScreen} />
            <Stack.Screen name="EditarVehiculo" component={EditVehicleScreen} />
            <Stack.Screen name="CambiarContrasena" component={ChangePasswordScreen} />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Register" component={RegisterScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
