import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import * as SecureStore from "expo-secure-store";

import {
  AuthenticatedUser,
  ApiError,
  RegisterPayload,
  getMe,
  login as apiLogin,
  register as apiRegister,
} from "../services/apiClient";

const TOKEN_KEY = "ucepark_driver_token";

type AuthContextValue = {
  token: string | null;
  user: AuthenticatedUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const savedToken = await SecureStore.getItemAsync(TOKEN_KEY);
        if (savedToken) {
          const me = await getMe(savedToken);
          setToken(savedToken);
          setUser(me);
        }
      } catch (error) {
        if (error instanceof ApiError) {
          await SecureStore.deleteItemAsync(TOKEN_KEY);
        }
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await apiLogin(username, password);
    await SecureStore.setItemAsync(TOKEN_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  };

  const register = async (payload: RegisterPayload) => {
    const response = await apiRegister(payload);
    await SecureStore.setItemAsync(TOKEN_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({ token, user, isLoading, login, register, logout }),
    [token, user, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return context;
}
