const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "";

export type AuthenticatedUser = {
  id: string;
  username: string;
  full_name: string;
  email: string | null;
  document_number: string | null;
  phone: string | null;
  role: string;
  roles: string[];
  permissions: string[];
  university_id: string | null;
  status: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  roles: string[];
  permissions: string[];
  university_id: string | null;
  user: AuthenticatedUser;
};

export type Vehicle = {
  id: string;
  university_id: string;
  plate_text: string;
  brand: string;
  model: string;
  color: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type VehicleListResponse = {
  total: number;
  items: Vehicle[];
};

export type Member = {
  id: string;
  university_id: string;
  document_id: string;
  institutional_id: string;
  full_name: string;
  email: string;
  role_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  user_id: string | null;
  has_face_profile: boolean;
};

export type VehicleLookupResponse = {
  found: boolean;
  message: string;
  vehicle: Vehicle | null;
  authorized_people: Member[];
};

export type ActiveSessionResponse = {
  plate_text: string;
  active: boolean;
};

export type AccessHistoryItem = {
  session_id: string;
  session_status: string;
  access_type: string;
  plate_text: string;
  person_name: string | null;
  payment_status: string;
  entry_time: string | null;
  exit_time: string | null;
  entry_face_evidence_id: string | null;
  entry_plate_evidence_id: string | null;
  exit_face_evidence_id: string | null;
  exit_plate_evidence_id: string | null;
};

export type AccessHistoryListResponse = {
  total: number;
  items: AccessHistoryItem[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string | null } = {},
): Promise<T> {
  if (!API_BASE_URL) {
    throw new ApiError(
      "EXPO_PUBLIC_API_BASE_URL no esta configurado (ver .env.example)",
      0,
    );
  }
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : response.statusText;
    throw new ApiError(detail, response.status);
  }
  return data as T;
}

export function login(username: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", { method: "POST", body: { username, password } });
}

export type RegisterPayload = {
  username: string;
  password: string;
  confirm_password: string;
  full_name: string;
  document_number: string;
  phone: string;
  email?: string;
};

export function register(payload: RegisterPayload): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/register", { method: "POST", body: payload });
}

export function getMe(token: string): Promise<AuthenticatedUser & { sub: string }> {
  return request("/auth/me", { token });
}

export function getMyVehicles(token: string): Promise<VehicleListResponse> {
  return request("/vehicles/mine", { token });
}

export type RegisterVehiclePayload = {
  plate_text: string;
  brand: string;
  model: string;
  color: string;
};

export function registerMyVehicle(token: string, payload: RegisterVehiclePayload): Promise<Vehicle> {
  return request("/vehicles/mine", { method: "POST", body: payload, token });
}

export type UpdateVehiclePayload = Partial<RegisterVehiclePayload>;

export function updateMyVehicle(token: string, payload: UpdateVehiclePayload): Promise<Vehicle> {
  return request("/vehicles/mine", { method: "PATCH", body: payload, token });
}

export type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
};

export function changePassword(token: string, payload: ChangePasswordPayload): Promise<{ changed: boolean }> {
  return request("/auth/change-password", { method: "POST", body: payload, token });
}

export function getMyAuthorizedDrivers(token: string): Promise<VehicleLookupResponse> {
  return request("/vehicles/mine/authorized-drivers", { token });
}

export function getMyActiveSession(token: string): Promise<ActiveSessionResponse> {
  return request("/parking/mine/active-session", { token });
}

export function getMyHistory(token: string, limit = 100): Promise<AccessHistoryListResponse> {
  return request(`/parking/mine/history?limit=${limit}`, { token });
}

async function postPhoto<T>(
  path: string,
  token: string,
  photo: { uri: string; fileName?: string; mimeType?: string },
): Promise<T> {
  if (!API_BASE_URL) {
    throw new ApiError("EXPO_PUBLIC_API_BASE_URL no esta configurado (ver .env.example)", 0);
  }
  const formData = new FormData();
  // React Native's FormData accepts this {uri, name, type} shape for files,
  // which doesn't match the DOM Blob typing FormData.append expects.
  formData.append("file", {
    uri: photo.uri,
    name: photo.fileName ?? "photo.jpg",
    type: photo.mimeType ?? "image/jpeg",
  } as unknown as Blob);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : response.statusText;
    throw new ApiError(detail, response.status);
  }
  return data as T;
}

export async function enrollMyFace(
  token: string,
  photo: { uri: string; fileName?: string; mimeType?: string },
): Promise<void> {
  await postPhoto("/vehicles/mine/face", token, photo);
}

export type FaceLiveCheck = {
  detected: boolean;
  centered: boolean;
  quality_score: number | null;
  warnings: string[];
};

export function checkFaceLive(
  token: string,
  photo: { uri: string; fileName?: string; mimeType?: string },
): Promise<FaceLiveCheck> {
  return postPhoto<FaceLiveCheck>("/vehicles/mine/face/live-check", token, photo);
}
