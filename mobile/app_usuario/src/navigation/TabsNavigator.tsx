import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { createMaterialTopTabNavigator } from "@react-navigation/material-top-tabs";
import type { MaterialTopTabBarProps } from "@react-navigation/material-top-tabs";

import HomeScreen from "../screens/HomeScreen";
import HistoryScreen from "../screens/HistoryScreen";
import ProfileScreen from "../screens/ProfileScreen";
import { colors, fonts } from "../theme/theme";

export type TabsParamList = {
  Historial: undefined;
  Inicio: undefined;
  Perfil: undefined;
};

const Tab = createMaterialTopTabNavigator<TabsParamList>();

const TAB_ICONS: Record<string, string> = {
  Historial: "🕘",
  Inicio: "🏠",
  Perfil: "👤",
};

function CustomTabBar({ state, navigation }: MaterialTopTabBarProps) {
  return (
    <View style={styles.bar}>
      {state.routes.map((route, index) => {
        const focused = state.index === index;
        return (
          <TouchableOpacity
            key={route.key}
            onPress={() => navigation.navigate(route.name)}
            style={styles.itemSlot}
            activeOpacity={0.85}
          >
            <View style={[styles.pill, focused ? styles.pillActive : null]}>
              <Text style={styles.icon}>{TAB_ICONS[route.name]}</Text>
              <Text style={[styles.label, focused ? styles.labelActive : null]}>{route.name}</Text>
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

export default function TabsNavigator() {
  return (
    <Tab.Navigator
      initialRouteName="Inicio"
      tabBarPosition="bottom"
      tabBar={(props) => <CustomTabBar {...props} />}
      screenOptions={{ swipeEnabled: true, animationEnabled: true }}
    >
      <Tab.Screen name="Historial" component={HistoryScreen} />
      <Tab.Screen name="Inicio" component={HomeScreen} />
      <Tab.Screen name="Perfil" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: "row",
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: colors.line,
    paddingTop: 10,
    paddingBottom: 22,
    paddingHorizontal: 10,
  },
  itemSlot: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  pill: {
    alignItems: "center",
    gap: 3,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
  },
  pillActive: {
    backgroundColor: colors.navy2,
    marginTop: -14,
    shadowColor: colors.navy2,
    shadowOpacity: 0.4,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 6 },
    elevation: 6,
  },
  icon: {
    fontSize: 20,
  },
  label: {
    fontFamily: fonts.semiBold,
    fontSize: 11.5,
    color: "#7D8BA0",
  },
  labelActive: {
    color: "#fff",
  },
});
