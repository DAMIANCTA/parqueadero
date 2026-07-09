const DEFAULT_API_BASE_URL =
  window.location.origin && window.location.origin.startsWith("http")
    ? window.location.origin
    : "http://localhost:8000";

const state = {
  section: "dashboard",
  apiBaseUrl: localStorage.getItem("smartParkingAdminApiBaseUrl") || DEFAULT_API_BASE_URL,
  auth: {
    token: sessionStorage.getItem("smartParkingAdminToken"),
    username: sessionStorage.getItem("smartParkingAdminUsername") || "cashier.user",
    password: "",
    roles: JSON.parse(sessionStorage.getItem("smartParkingAdminRoles") || "[]"),
  },
  dashboard: null,
  activeSessions: [],
  sessionHistory: [],
  auditEvents: [],
  members: [],
  vehicles: [],
  permits: [],
  faceProfiles: [],
  cashierPlateQuery: "",
  currentSession: null,
  cashierMessage: "",
  receiptMessage: "",
  memberMessage: "",
  vehicleMessage: "",
  faceMessage: "",
  permitMessage: "",
  globalMessage: "",
};

function api(path) {
  return `${state.apiBaseUrl.replace(/\/$/, "")}${path}`;
}

function authHeaders() {
  return state.auth.token ? { Authorization: `Bearer ${state.auth.token}` } : {};
}

function setSection(section) {
  state.section = section;
  render();
}

function boot() {
  render();
  refreshOverview();
}

async function refreshOverview() {
  const jobs = [
    loadDashboardSummary(),
    loadActiveSessions(),
    loadSessionHistory(),
    loadAuditEvents(),
  ];
  if (state.auth.token) {
    jobs.push(loadMembers(), loadVehicles(), loadMonthlyPermits(), loadFaceProfiles());
  }
  await Promise.allSettled(jobs);
  render();
}

async function loadDashboardSummary() {
  const response = await fetch(api("/admin/dashboard-summary"));
  state.dashboard = await response.json();
}

async function loadActiveSessions() {
  const response = await fetch(api("/admin/active-sessions"));
  const body = await response.json();
  state.activeSessions = body.items || [];
}

async function loadSessionHistory() {
  const response = await fetch(api("/admin/session-history"));
  const body = await response.json();
  state.sessionHistory = body.items || [];
}

async function loadAuditEvents() {
  const response = await fetch(api("/admin/audit-events"));
  const body = await response.json();
  state.auditEvents = body.items || [];
}

async function loadMembers() {
  if (!state.auth.token) {
    state.members = [];
    return;
  }
  const response = await fetch(api("/members"), { headers: authHeaders() });
  const body = await response.json();
  state.members = body.items || [];
}

async function loadVehicles() {
  if (!state.auth.token) {
    state.vehicles = [];
    return;
  }
  const response = await fetch(api("/vehicles"), { headers: authHeaders() });
  const body = await response.json();
  state.vehicles = body.items || [];
}

async function loadMonthlyPermits() {
  if (!state.auth.token) {
    state.permits = [];
    return;
  }
  const response = await fetch(api("/permits/monthly"), { headers: authHeaders() });
  const body = await response.json();
  state.permits = body.items || [];
}

async function loadFaceProfiles() {
  if (!state.auth.token) {
    state.faceProfiles = [];
    return;
  }
  const response = await fetch(api("/members/faces"), { headers: authHeaders() });
  const body = await response.json();
  state.faceProfiles = body.items || [];
}

async function loginCashier(event) {
  event.preventDefault();
  state.cashierMessage = "Autenticando...";
  render();
  try {
    const response = await fetch(api("/auth/token"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: state.auth.username,
        password: state.auth.password,
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo iniciar sesion."));
    }
    state.auth.token = body.access_token;
    state.auth.roles = body.roles || [];
    sessionStorage.setItem("smartParkingAdminToken", state.auth.token);
    sessionStorage.setItem("smartParkingAdminUsername", state.auth.username);
    sessionStorage.setItem("smartParkingAdminRoles", JSON.stringify(state.auth.roles));
    state.cashierMessage = `Sesion activa: ${state.auth.username} (${state.auth.roles.join(", ") || "sin roles"})`;
    await refreshOverview();
  } catch (error) {
    state.auth.token = null;
    state.auth.roles = [];
    sessionStorage.removeItem("smartParkingAdminToken");
    sessionStorage.removeItem("smartParkingAdminRoles");
    state.cashierMessage = localizeBackendMessage(error.message || "No se pudo iniciar sesion.");
  }
  render();
}

function logoutCashier() {
  state.auth.token = null;
  state.auth.roles = [];
  state.auth.password = "";
  state.currentSession = null;
  state.cashierMessage = "Sesion cerrada.";
  state.receiptMessage = "";
  state.members = [];
  state.vehicles = [];
  state.permits = [];
  state.faceProfiles = [];
  sessionStorage.removeItem("smartParkingAdminToken");
  sessionStorage.removeItem("smartParkingAdminUsername");
  sessionStorage.removeItem("smartParkingAdminRoles");
  render();
}

async function createMember(event) {
  event.preventDefault();
  if (!state.auth.token) {
    state.memberMessage = "Inicia sesion como admin para registrar miembros.";
    render();
    return;
  }
  const form = event.currentTarget;
  const payload = {
    university_id: form.university_id.value.trim() || "11111111-1111-1111-1111-111111111111",
    document_id: form.document_id.value.trim(),
    institutional_id: form.institutional_id.value.trim(),
    full_name: form.full_name.value.trim(),
    email: form.email.value.trim(),
    role_type: form.role_type.value,
    status: form.status.value,
  };
  state.memberMessage = "Registrando miembro...";
  render();
  try {
    const response = await fetch(api("/members"), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo registrar el miembro."));
    }
    state.memberMessage = `Miembro registrado: ${body.full_name}`;
    form.reset();
    form.university_id.value = "11111111-1111-1111-1111-111111111111";
    form.status.value = "ACTIVE";
    form.role_type.value = "STUDENT";
    await Promise.allSettled([loadMembers(), loadVehicles(), loadMonthlyPermits()]);
  } catch (error) {
    state.memberMessage = error.message || "No se pudo registrar el miembro.";
  }
  render();
}

async function createVehicle(event) {
  event.preventDefault();
  if (!state.auth.token) {
    state.vehicleMessage = "Inicia sesion como admin para registrar vehiculos.";
    render();
    return;
  }
  const form = event.currentTarget;
  const payload = {
    university_id: form.university_id.value.trim() || "11111111-1111-1111-1111-111111111111",
    plate_text: normalizePlate(form.plate_text.value),
    brand: form.brand.value.trim(),
    model: form.model.value.trim(),
    color: form.color.value.trim(),
    status: form.status.value,
  };
  state.vehicleMessage = "Registrando vehiculo...";
  render();
  try {
    const response = await fetch(api("/vehicles"), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo registrar el vehiculo."));
    }
    state.vehicleMessage = `Vehiculo registrado: ${body.plate_text}`;
    form.reset();
    form.university_id.value = "11111111-1111-1111-1111-111111111111";
    form.status.value = "ACTIVE";
    await loadVehicles();
  } catch (error) {
    state.vehicleMessage = error.message || "No se pudo registrar el vehiculo.";
  }
  render();
}

async function authorizeVehiclePerson(event) {
  event.preventDefault();
  if (!state.auth.token) {
    state.vehicleMessage = "Inicia sesion como admin para autorizar personas.";
    render();
    return;
  }
  const form = event.currentTarget;
  const vehicleId = form.vehicle_id.value;
  const payload = {
    person_id: form.person_id.value,
    is_owner: form.is_owner.checked,
    status: "ACTIVE",
  };
  if (!vehicleId || !payload.person_id) {
    state.vehicleMessage = "Selecciona vehiculo y persona para crear la autorizacion.";
    render();
    return;
  }
  state.vehicleMessage = "Creando autorizacion...";
  render();
  try {
    const response = await fetch(api(`/vehicles/${encodeURIComponent(vehicleId)}/authorize-person`), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo autorizar la placa."));
    }
    const vehicle = state.vehicles.find((item) => item.id === body.vehicle_id);
    const member = state.members.find((item) => item.id === body.person_id);
    state.vehicleMessage = `Autorizacion creada: ${vehicle?.plate_text || body.vehicle_id} -> ${member?.full_name || body.person_id}`;
    await Promise.allSettled([loadVehicles(), loadMembers()]);
  } catch (error) {
    state.vehicleMessage = error.message || "No se pudo autorizar la placa.";
  }
  render();
}

async function uploadFaceAndEnroll(event) {
  event.preventDefault();
  if (!state.auth.token) {
    state.faceMessage = "Inicia sesion como admin para registrar rostros.";
    render();
    return;
  }
  const form = event.currentTarget;
  const memberId = form.member_id.value;
  const plateText = normalizePlate(form.plate_text.value || "FACEENROLL");
  const qualityScoreHint = Number.parseFloat(form.quality_score_hint.value || "0.9");
  const file = form.face_file.files?.[0];
  if (!memberId || !file) {
    state.faceMessage = "Selecciona miembro y archivo de rostro.";
    render();
    return;
  }
  state.faceMessage = "Subiendo evidencia de rostro...";
  render();
  try {
    const uploadData = new FormData();
    uploadData.append("image_type", "face_entry");
    uploadData.append("plate", plateText || "FACEENROLL");
    uploadData.append("file", file);
    const uploadResponse = await fetch(api("/evidence/upload"), {
      method: "POST",
      body: uploadData,
    });
    const uploadBody = await uploadResponse.json();
    if (!uploadResponse.ok) {
      throw new Error(localizeBackendMessage(parseDetail(uploadBody.detail) || "No se pudo subir la imagen del rostro."));
    }

    state.faceMessage = "Enrolando rostro en face-service...";
    render();
    const enrollResponse = await fetch(api(`/members/${encodeURIComponent(memberId)}/faces/enroll`), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        face_image_id: uploadBody.image_id,
        quality_score_hint: Number.isFinite(qualityScoreHint) ? qualityScoreHint : 0.9,
      }),
    });
    const enrollBody = await enrollResponse.json();
    if (!enrollResponse.ok) {
      throw new Error(localizeBackendMessage(parseDetail(enrollBody.detail) || "No se pudo enrolar el rostro."));
    }
    const member = state.members.find((item) => item.id === memberId);
    state.faceMessage = `Rostro registrado correctamente para ${member?.full_name || memberId}. Image ID: ${uploadBody.image_id}`;
    form.reset();
    form.quality_score_hint.value = "0.90";
    await loadFaceProfiles();
  } catch (error) {
    state.faceMessage = error.message || "No se pudo registrar el rostro.";
  }
  render();
}

async function createMonthlyPermit(event) {
  event.preventDefault();
  if (!state.auth.token) {
    state.permitMessage = "Inicia sesion como cashier o admin para registrar permisos mensuales.";
    render();
    return;
  }
  const form = event.currentTarget;
  const payload = {
    university_id: form.university_id.value.trim() || "11111111-1111-1111-1111-111111111111",
    person_id: form.person_id.value,
    vehicle_id: form.vehicle_id.value,
    start_date: form.start_date.value,
    end_date: form.end_date.value,
    amount: Number.parseFloat(form.amount.value || "0"),
    payment_method: form.payment_method.value,
    status: form.status.value,
  };
  if (!payload.person_id || !payload.vehicle_id) {
    state.permitMessage = "Selecciona miembro y vehiculo para registrar el permiso.";
    render();
    return;
  }
  state.permitMessage = "Registrando permiso mensual...";
  render();
  try {
    const response = await fetch(api("/permits/monthly"), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo registrar el permiso mensual."));
    }
    const member = state.members.find((item) => item.id === body.person_id);
    state.permitMessage = `Permiso mensual registrado para ${member?.full_name || body.person_id}.`;
    form.reset();
    form.university_id.value = "11111111-1111-1111-1111-111111111111";
    form.status.value = "VALID";
    await loadMonthlyPermits();
  } catch (error) {
    state.permitMessage = error.message || "No se pudo registrar el permiso mensual.";
  }
  render();
}

async function searchSessionByPlate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const plate = normalizePlate(form.querySelector('input[name="plate"]').value || state.cashierPlateQuery);
  if (!plate) {
    state.cashierMessage = "Ingresa una placa para buscar.";
    render();
    return;
  }

  state.cashierPlateQuery = plate;
  state.currentSession = null;
  state.cashierMessage = "Consultando sesion activa...";
  state.receiptMessage = "";
  render();
  try {
    const response = await fetch(api(`/payments/by-plate/${encodeURIComponent(plate)}`), {
      headers: authHeaders(),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo consultar la sesion."));
    }
    if (!body.found) {
      state.currentSession = null;
      state.cashierMessage = "No hay sesion activa para esta placa.";
    } else {
      state.currentSession = body;
      state.cashierMessage = body.payment_status === "PAID" ? "Pago registrado." : "Sesion activa encontrada.";
    }
  } catch (error) {
    state.currentSession = null;
    state.cashierMessage = localizeBackendMessage(error.message || "No se pudo consultar la sesion.");
  }
  render();
}

async function registerPayment(event) {
  event.preventDefault();
  if (!state.currentSession) {
    state.cashierMessage = "Busca una sesion activa antes de registrar pago.";
    render();
    return;
  }
  if (!state.auth.token) {
    state.cashierMessage = "Inicia sesion como cashier o admin para registrar pagos.";
    render();
    return;
  }

  const form = event.currentTarget;
  const amount = Number.parseFloat(form.querySelector('input[name="amount"]').value);
  const paymentMethod = form.querySelector('select[name="paymentMethod"]').value;
  const notes = form.querySelector('textarea[name="notes"]').value.trim();

  state.cashierMessage = "Registrando pago...";
  render();
  try {
    const response = await fetch(api("/payments/register-cash-payment"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({
        session_id: state.currentSession.session_id,
        plate_text: state.currentSession.plate_text,
        amount,
        payment_method: paymentMethod,
        cashier_user_id: state.auth.username,
        notes: notes || "Pago en secretaria",
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(localizeBackendMessage(parseDetail(body.detail) || "No se pudo registrar el pago."));
    }
    state.currentSession = body.session;
    state.cashierMessage = "Pago registrado correctamente.";
    state.receiptMessage = `Comprobante ${body.receipt_number || "-"} generado.`;
    await refreshOverview();
  } catch (error) {
    state.cashierMessage = localizeBackendMessage(error.message || "No se pudo registrar el pago.");
  }
  render();
}

function saveApiBaseUrl(event) {
  event.preventDefault();
  const value = event.currentTarget.querySelector('input[name="apiBaseUrl"]').value.trim();
  if (!value) {
    state.globalMessage = "Ingresa una URL valida para el API Gateway.";
    render();
    return;
  }
  state.apiBaseUrl = value.replace(/\/$/, "");
  localStorage.setItem("smartParkingAdminApiBaseUrl", state.apiBaseUrl);
  state.globalMessage = "API Gateway actualizado.";
  render();
  refreshOverview();
}

function openCashierForPlate(plate) {
  state.section = "cashier";
  state.cashierPlateQuery = plate;
  state.currentSession = null;
  state.cashierMessage = `Placa seleccionada: ${plate}. Busca para cargar la sesion.`;
  render();
  const inputNode = document.querySelector('input[name="plate"]');
  if (inputNode) {
    inputNode.value = plate;
  }
}

function render() {
  const root = document.getElementById("app");
  root.innerHTML = "";
  root.appendChild(buildShell());
}

function buildShell() {
  return el("div", { className: "app-shell" }, [buildSidebar(), buildContent()]);
}

function buildSidebar() {
  const buttons = [
    ["dashboard", "Dashboard"],
    ["cashier", "Caja / Pagos"],
    ["active", "Sesiones activas"],
    ["history", "Historial"],
    ["members", "Miembros"],
    ["vehicles", "Vehiculos"],
    ["faces", "Rostros"],
    ["permits", "Permisos"],
    ["audit", "Auditoria"],
    ["settings", "Configuracion"],
  ].map(([key, label]) =>
    el("button", {
      className: `nav-button${state.section === key ? " active" : ""}`,
      type: "button",
      text: label,
      onclick: () => setSection(key),
    }),
  );

  return el("aside", { className: "sidebar" }, [
    el("div", { className: "brand" }, [
      el("h1", { text: "Smart Parking University" }),
      el("p", { text: "Portal unificado para administracion y caja del parqueadero." }),
    ]),
    el("div", { className: "nav-list" }, buttons),
    el("p", {
      className: "sidebar-note",
      text: "La pagina se sirve desde el API Gateway y deja las pantallas antiguas como respaldo.",
    }),
  ]);
}

function buildContent() {
  return el("section", { className: "content" }, [buildTopbar(), el("main", { className: "workspace" }, [buildSection()])]);
}

function buildTopbar() {
  const labels = {
    dashboard: ["Dashboard", "Indicadores operativos, cobros y salidas del dia."],
    cashier: ["Caja / Pagos", "Busca sesiones activas por placa y registra pagos congelando el monto."],
    active: ["Sesiones activas", "Vehiculos actualmente dentro del parqueadero."],
    history: ["Historial", "Sesiones ya cerradas con salida registrada."],
    members: ["Miembros universidad", "Registro de estudiantes, docentes y personal con estado activo."],
    vehicles: ["Vehiculos autorizados", "Registro de placas institucionales y asignacion a personas."],
    faces: ["Rostros registrados", "Carga evidencia de rostro y enrola contra face-service."],
    permits: ["Permisos mensuales", "Gestiona pagos o permisos vigentes para miembros universitarios."],
    audit: ["Auditoria", "Eventos importantes emitidos por los servicios."],
    settings: ["Configuracion", "API Gateway, credenciales de caja y verificacion rapida."],
  };
  const [title, subtitle] = labels[state.section];
  return el("header", { className: "topbar" }, [
    el("div", {}, [el("h2", { text: title }), el("p", { text: subtitle })]),
    el("div", { className: "topbar-actions" }, [
      el("span", { className: "badge neutral", text: state.apiBaseUrl }),
      el("span", {
        className: `badge ${state.auth.token ? "success" : "warn"}`,
        text: state.auth.token ? `Caja autenticada: ${state.auth.username}` : "Caja sin autenticar",
      }),
    ]),
  ]);
}

function buildSection() {
  if (state.section === "dashboard") return buildDashboardSection();
  if (state.section === "cashier") return buildCashierSection();
  if (state.section === "active") return buildActiveSection();
  if (state.section === "history") return buildHistorySection();
  if (state.section === "members") return buildMembersSection();
  if (state.section === "vehicles") return buildVehiclesSection();
  if (state.section === "faces") return buildFacesSection();
  if (state.section === "permits") return buildPermitsSection();
  if (state.section === "audit") return buildAuditSection();
  return buildSettingsSection();
}

function buildDashboardSection() {
  const summary = state.dashboard || {};
  return el("div", { className: "grid" }, [
    el("section", { className: "metrics" }, [
      metric("Sesiones activas", summary.active_sessions ?? "-"),
      metric("Vehiculos dentro", summary.vehicles_inside ?? "-"),
      metric("Pagos pendientes", summary.pending_payments ?? "-"),
      metric("Pagos realizados", summary.paid_today ?? "-"),
      metric("Ingresos del dia", money(summary.revenue_today)),
      metric("Salidas autorizadas", summary.authorized_exits_today ?? "-"),
      metric("Salidas rechazadas", summary.rejected_exits_today ?? "-"),
      metric("Historial cerrado", state.sessionHistory.length),
    ]),
    el("div", { className: "grid two" }, [buildActivePreview(), buildPendingPreview()]),
  ]);
}

function buildActivePreview() {
  return el("section", { className: "card" }, [
    sectionHeader("Vehiculos dentro", "Vista rapida de sesiones activas."),
    state.activeSessions.length
      ? table(
          ["Placa", "Entrada", "Tiempo", "Pago"],
          state.activeSessions.slice(0, 5).map((item) => [
            item.plate_text,
            formatDateTime(item.entry_time),
            `${item.duration_minutes} min`,
            statusPill(item.payment_status),
          ]),
        )
      : el("p", { className: "empty-state", text: "No hay sesiones activas en este momento." }),
  ]);
}

function buildPendingPreview() {
  const pending = state.activeSessions.filter((item) => item.payment_status === "PENDING").slice(0, 5);
  return el("section", { className: "card" }, [
    sectionHeader("Cobros pendientes", "Visitantes con pago aun no registrado."),
    pending.length
      ? table(
          ["Placa", "Monto", "Tiempo", "Accion"],
          pending.map((item) => [
            item.plate_text,
            money(item.amount, item.currency),
            `${item.duration_minutes} min`,
            actionButton("Ver en caja", () => openCashierForPlate(item.plate_text)),
          ]),
        )
      : el("p", { className: "empty-state", text: "No hay pagos pendientes." }),
  ]);
}

function buildCashierSection() {
  return el("div", { className: "grid two" }, [
    el("section", { className: "panel" }, [
      sectionHeader("Acceso de caja", "Puedes abrir el portal sin login, pero registrar pagos requiere autenticacion."),
      buildLoginForm(),
      el("div", { className: "card" }, [
        el("h3", { text: "Buscar sesion por placa" }),
        el("p", { className: "helper", text: "Consulta solo sesiones activas con estado INSIDE." }),
        buildSearchForm(),
      ]),
      state.cashierMessage ? el("p", { className: "helper", text: state.cashierMessage }) : null,
    ].filter(Boolean)),
    el("section", { className: "grid" }, [
      el("section", { className: "panel" }, [
        sectionHeader("Sesion activa", state.currentSession ? "Detalle de cobro y estado congelado despues del pago." : "Busca una placa para ver la sesion."),
        state.currentSession ? buildSessionDetails(state.currentSession) : el("p", { className: "empty-state", text: "No hay sesion seleccionada." }),
      ]),
      state.currentSession
        ? el("section", { className: "panel" }, [
            sectionHeader("Registrar pago", "El monto se mantiene fijo despues del pago."),
            buildPaymentForm(state.currentSession),
            state.receiptMessage ? el("p", { className: "helper", text: state.receiptMessage }) : null,
          ].filter(Boolean))
        : null,
    ].filter(Boolean)),
  ]);
}

function buildActiveSection() {
  return el("section", { className: "table-card" }, [
    panelHeader("Vehiculos INSIDE", "Actualiza la lista despues de nuevas entradas o pagos.", loadActiveSessions),
    state.activeSessions.length
      ? table(
          ["Placa", "Entrada", "Tiempo", "Pago", "Estado", "Detalle"],
          state.activeSessions.map((item) => [
            item.plate_text,
            formatDateTime(item.entry_time),
            `${item.duration_minutes} min`,
            statusPill(item.payment_status),
            statusPill(item.session_status),
            actionButton("Ver detalle", () => openCashierForPlate(item.plate_text)),
          ]),
        )
      : el("p", { className: "empty-state", text: "No hay vehiculos activos dentro del parqueadero." }),
  ]);
}

function buildHistorySection() {
  return el("section", { className: "table-card" }, [
    panelHeader("Historial OUTSIDE", "Sesiones cerradas que ya no aparecen como activas en caja.", loadSessionHistory),
    state.sessionHistory.length
      ? table(
          ["Placa", "Entrada", "Salida", "Monto pagado", "Metodo", "Estado"],
          state.sessionHistory.map((item) => [
            item.plate_text,
            formatDateTime(item.entry_time),
            formatDateTime(item.exit_time),
            item.paid_amount != null ? money(item.paid_amount, item.currency) : money(item.amount, item.currency),
            item.payment_method || "-",
            statusPill(item.session_status),
          ]),
        )
      : el("p", { className: "empty-state", text: "Todavia no hay sesiones cerradas." }),
  ]);
}

function buildAuditSection() {
  return el("section", { className: "panel" }, [
    panelHeader("Eventos de auditoria", "Entradas, pagos, salidas y cambios operativos recientes.", loadAuditEvents),
    state.auditEvents.length
      ? el(
          "div",
          { className: "audit-list" },
          state.auditEvents.slice(0, 50).map((item) =>
            el("article", { className: "audit-item" }, [
              el("strong", { text: `${item.method || "?"} ${item.path || "-"}` }),
              el("p", {
                className: "meta",
                text: `${item.service || "service"} respondio ${item.status_code ?? "-"} en ${item.duration_ms ?? "-"} ms`,
              }),
              el("div", { className: "audit-meta" }, [
                el("span", { text: formatTimestamp(item.timestamp) }),
                el("span", { text: item.actor_username || "usuario_sistema" }),
                el("span", { text: (item.actor_roles || []).join(", ") || "sin rol" }),
                el("span", { text: item.client_ip || "sin ip" }),
              ]),
            ]),
          ),
        )
      : el("p", { className: "empty-state", text: "Aun no hay eventos de auditoria disponibles." }),
  ]);
}

function buildMembersSection() {
  return el("div", { className: "grid two" }, [
    el("section", { className: "panel" }, [
      sectionHeader("Registrar miembro", "Solo administracion puede crear miembros universitarios."),
      buildMemberForm(),
      state.memberMessage ? el("p", { className: "helper", text: state.memberMessage }) : null,
    ].filter(Boolean)),
    el("section", { className: "table-card" }, [
      panelHeader("Miembros registrados", "Listado actual de estudiantes, docentes y personal.", async () => {
        await loadMembers();
      }),
      state.members.length
        ? table(
            ["Nombre", "Rol", "Documento", "Correo", "Estado"],
            state.members.map((item) => [
              item.full_name,
              statusPill(item.role_type),
              item.document_id,
              item.email,
              statusPill(item.status),
            ]),
          )
        : el("p", { className: "empty-state", text: "No hay miembros cargados o falta autenticacion." }),
    ]),
  ]);
}

function buildVehiclesSection() {
  return el("div", { className: "grid two" }, [
    el("section", { className: "panel" }, [
      sectionHeader("Registrar vehiculo", "Registra la placa y sus datos base."),
      buildVehicleForm(),
      el("div", { className: "card" }, [
        el("h3", { text: "Autorizar persona para placa" }),
        el("p", { className: "helper", text: "Una misma placa puede tener una o varias personas autorizadas." }),
        buildVehicleAuthorizationForm(),
      ]),
      state.vehicleMessage ? el("p", { className: "helper", text: state.vehicleMessage }) : null,
    ].filter(Boolean)),
    el("section", { className: "table-card" }, [
      panelHeader("Vehiculos registrados", "Consulta placas activas y modelos registrados.", async () => {
        await loadVehicles();
      }),
      state.vehicles.length
        ? table(
            ["Placa", "Marca", "Modelo", "Color", "Estado"],
            state.vehicles.map((item) => [
              item.plate_text,
              item.brand,
              item.model,
              item.color,
              statusPill(item.status),
            ]),
          )
        : el("p", { className: "empty-state", text: "No hay vehiculos registrados o falta autenticacion." }),
    ]),
  ]);
}

function buildFacesSection() {
  return el("div", { className: "grid two" }, [
    el("section", { className: "panel" }, [
      sectionHeader("Enrolar rostro", "Sube la evidencia a MinIO y luego registra el template en face-service."),
      buildFaceEnrollForm(),
      state.faceMessage ? el("p", { className: "helper", text: state.faceMessage }) : null,
    ].filter(Boolean)),
    el("section", { className: "table-card" }, [
      panelHeader("Rostros registrados", "Templates activos asociados a miembros.", async () => {
        await loadFaceProfiles();
      }),
      state.faceProfiles.length
        ? table(
            ["Miembro", "Image ID", "Template", "Provider", "Estado"],
            state.faceProfiles.map((item) => [
              memberNameById(item.person_id),
              item.face_image_id,
              item.template_id,
              item.provider,
              statusPill(item.status),
            ]),
          )
        : el("p", { className: "empty-state", text: "No hay rostros registrados o falta autenticacion." }),
    ]),
  ]);
}

function buildPermitsSection() {
  return el("div", { className: "grid two" }, [
    el("section", { className: "panel" }, [
      sectionHeader("Registrar permiso mensual", "Solo caja o administracion pueden registrar pago/permisos mensuales."),
      buildPermitForm(),
      state.permitMessage ? el("p", { className: "helper", text: state.permitMessage }) : null,
    ].filter(Boolean)),
    el("section", { className: "table-card" }, [
      panelHeader("Permisos vigentes", "Permisos cargados por persona y vehiculo.", async () => {
        await loadMonthlyPermits();
      }),
      state.permits.length
        ? table(
            ["Miembro", "Placa", "Inicio", "Fin", "Monto", "Estado"],
            state.permits.map((item) => [
              memberNameById(item.person_id),
              vehiclePlateById(item.vehicle_id),
              formatDateTime(item.start_date),
              formatDateTime(item.end_date),
              money(item.amount),
              statusPill(item.status),
            ]),
          )
        : el("p", { className: "empty-state", text: "No hay permisos registrados o falta autenticacion." }),
    ]),
  ]);
}

function buildSettingsSection() {
  return el("div", { className: "grid two" }, [
    el("section", { className: "panel" }, [
      sectionHeader("API Gateway", "Configura la URL base usada por el portal."),
      buildApiSettingsForm(),
    ]),
    el("section", { className: "panel" }, [
      sectionHeader("Verificacion local", "Rutas principales disponibles en el gateway."),
      el("div", { className: "grid" }, [
        el("span", { className: "badge neutral", text: `GET ${api("/health")}` }),
        el("span", { className: "badge neutral", text: `GET ${api("/admin/dashboard-summary")}` }),
        el("span", { className: "badge neutral", text: `GET ${api("/payments/by-plate/VISPEND")}` }),
        state.globalMessage ? el("p", { className: "helper", text: state.globalMessage }) : null,
      ].filter(Boolean)),
    ]),
  ]);
}

function buildLoginForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", loginCashier);
  form.append(
    el("div", { className: "grid two" }, [
      field("Usuario", input("text", "username", state.auth.username, (event) => {
        state.auth.username = event.target.value;
      })),
      field("Clave", input("password", "password", state.auth.password, (event) => {
        state.auth.password = event.target.value;
      })),
    ]),
    el("div", { className: "actions" }, [
      el("button", { className: "button primary", type: "submit", text: "Iniciar sesion caja" }),
      actionButton("Cerrar sesion", logoutCashier),
    ]),
  );
  return form;
}

function buildSearchForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", searchSessionByPlate);
  form.append(
    field(
      "Placa",
      input("text", "plate", state.cashierPlateQuery, (event) => {
        state.cashierPlateQuery = normalizePlate(event.target.value);
      }, "PBD5650"),
    ),
    el("div", { className: "actions" }, [
      el("button", { className: "button primary", type: "submit", text: "Buscar" }),
      actionButton("Refrescar portal", refreshOverview),
    ]),
  );
  return form;
}

function buildSessionDetails(session) {
  const paid = session.payment_status === "PAID";
  return el("div", { className: "grid" }, [
    el("dl", { className: "details" }, [
      detail("Sesion", session.session_id),
      detail("Placa", session.plate_text),
      detail("Estado sesion", session.session_status),
      detail("Entrada", formatDateTime(session.entry_time)),
      detail("Tiempo", `${session.duration_minutes ?? 0} min`),
      detail("Estado de pago", session.payment_status),
      detail("Monto calculado", money(session.amount, session.currency)),
      detail("Monto pagado", session.paid_amount != null ? money(session.paid_amount, session.currency) : "-"),
      detail("Hora de pago", formatDateTime(session.paid_at)),
      detail("Valido hasta", formatDateTime(session.payment_valid_until)),
      detail("Metodo", session.payment_method || "-"),
      detail("Recibo", session.receipt_number || "-"),
    ]),
    el("span", {
      className: `badge ${paid ? "success" : "warn"}`,
      text: paid ? "Pago registrado y monto congelado" : "Pendiente de pago en secretaria",
    }),
  ]);
}

function buildPaymentForm(session) {
  const disabled = session.payment_status === "PAID";
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", registerPayment);
  form.append(
    el("div", { className: "grid two" }, [
      field(
        "Metodo de pago",
        select(
          "paymentMethod",
          [
            ["cash", "Efectivo"],
            ["card", "Tarjeta"],
            ["transfer", "Transferencia"],
            ["mobile", "Pago movil"],
          ],
          session.payment_method || "cash",
          disabled,
        ),
      ),
      field(
        "Monto",
        input("number", "amount", session.amount ?? 0, null, "", disabled, {
          step: "0.01",
          min: "0",
        }),
      ),
    ]),
    field("Observaciones", textarea("notes", disabled ? session.notes || "Pago ya registrado" : "Pago en secretaria", disabled)),
    el("div", { className: "actions" }, [
      el("button", {
        className: "button primary",
        type: "submit",
        text: "Registrar pago",
        disabled,
      }),
      el("span", {
        className: `badge ${disabled ? "success" : "neutral"}`,
        text: disabled ? "La sesion ya esta pagada." : "Solo cashier y admin pueden registrar pago.",
      }),
    ]),
  );
  return form;
}

function buildApiSettingsForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", saveApiBaseUrl);
  form.append(
    field("API base URL", input("url", "apiBaseUrl", state.apiBaseUrl, null, "http://localhost:8000")),
    el("div", { className: "actions" }, [
      el("button", { className: "button primary", type: "submit", text: "Guardar configuracion" }),
      actionButton("Usar localhost", () => {
        state.apiBaseUrl = DEFAULT_API_BASE_URL;
        localStorage.setItem("smartParkingAdminApiBaseUrl", state.apiBaseUrl);
        state.globalMessage = "Se restauro la URL por defecto.";
        render();
        refreshOverview();
      }),
    ]),
  );
  return form;
}

function buildMemberForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", createMember);
  form.append(
    inputHidden("university_id", "11111111-1111-1111-1111-111111111111"),
    el("div", { className: "grid two" }, [
      field("Nombre completo", input("text", "full_name", "")),
      field("Correo institucional", input("email", "email", "")),
      field("Documento", input("text", "document_id", "")),
      field("ID institucional", input("text", "institutional_id", "")),
      field("Rol", select("role_type", [["STUDENT", "Estudiante"], ["TEACHER", "Profesor"], ["STAFF", "Personal"]], "STUDENT")),
      field("Estado", select("status", [["ACTIVE", "Activo"], ["INACTIVE", "Inactivo"]], "ACTIVE")),
    ]),
    el("div", { className: "actions" }, [el("button", { className: "button primary", type: "submit", text: "Registrar miembro" })]),
  );
  return form;
}

function buildVehicleForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", createVehicle);
  form.append(
    inputHidden("university_id", "11111111-1111-1111-1111-111111111111"),
    el("div", { className: "grid two" }, [
      field("Placa", input("text", "plate_text", "")),
      field("Marca", input("text", "brand", "")),
      field("Modelo", input("text", "model", "")),
      field("Color", input("text", "color", "")),
      field("Estado", select("status", [["ACTIVE", "Activo"], ["INACTIVE", "Inactivo"]], "ACTIVE")),
    ]),
    el("div", { className: "actions" }, [el("button", { className: "button primary", type: "submit", text: "Registrar vehiculo" })]),
  );
  return form;
}

function buildVehicleAuthorizationForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", authorizeVehiclePerson);
  form.append(
    el("div", { className: "grid two" }, [
      field("Vehiculo", vehicleSelect("vehicle_id")),
      field("Miembro", memberSelect("person_id")),
    ]),
    field("Propietario principal", checkbox("is_owner")),
    el("div", { className: "actions" }, [el("button", { className: "button primary", type: "submit", text: "Crear autorizacion" })]),
  );
  return form;
}

function buildFaceEnrollForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", uploadFaceAndEnroll);
  form.append(
    el("div", { className: "grid two" }, [
      field("Miembro", memberSelect("member_id")),
      field("Placa de referencia", input("text", "plate_text", "")),
      field("Calidad esperada", input("number", "quality_score_hint", "0.90", null, "", false, { step: "0.01", min: "0", max: "1" })),
      field("Archivo de rostro", input("file", "face_file", "", null, "", false, { accept: "image/*" })),
    ]),
    el("div", { className: "actions" }, [el("button", { className: "button primary", type: "submit", text: "Subir y enrolar rostro" })]),
  );
  return form;
}

function buildPermitForm() {
  const form = el("form", { className: "grid" });
  form.addEventListener("submit", createMonthlyPermit);
  form.append(
    inputHidden("university_id", "11111111-1111-1111-1111-111111111111"),
    el("div", { className: "grid two" }, [
      field("Miembro", memberSelect("person_id")),
      field("Vehiculo", vehicleSelect("vehicle_id")),
      field("Inicio", input("date", "start_date", "")),
      field("Fin", input("date", "end_date", "")),
      field("Monto", input("number", "amount", "15.00", null, "", false, { step: "0.01", min: "0" })),
      field("Metodo", select("payment_method", [["cash", "Efectivo"], ["transfer", "Transferencia"], ["card", "Tarjeta"], ["mobile", "Pago movil"]], "cash")),
      field("Estado", select("status", [["VALID", "VALID"], ["EXPIRED", "EXPIRED"], ["SUSPENDED", "SUSPENDED"]], "VALID")),
    ]),
    el("div", { className: "actions" }, [el("button", { className: "button primary", type: "submit", text: "Registrar permiso" })]),
  );
  return form;
}

function panelHeader(title, copy, refreshHandler) {
  return el("div", { className: "section-header" }, [
    el("div", {}, [el("h3", { text: title }), el("p", { text: copy })]),
    actionButton("Actualizar", async () => {
      await refreshHandler();
      render();
    }),
  ]);
}

function sectionHeader(title, copy) {
  return el("div", { className: "section-header" }, [
    el("div", {}, [el("h3", { text: title }), el("p", { text: copy })]),
  ]);
}

function metric(label, value) {
  return el("article", { className: "metric" }, [
    el("span", { className: "label", text: label }),
    el("span", { className: "value", text: String(value ?? "-") }),
  ]);
}

function table(headers, rows) {
  const head = el("thead", {}, [
    el("tr", {}, headers.map((header) => el("th", { text: header }))),
  ]);
  const body = el("tbody");
  rows.forEach((row) => {
    body.appendChild(
      el(
        "tr",
        {},
        row.map((cell) => {
          const td = el("td");
          if (cell instanceof Node) {
            td.appendChild(cell);
          } else {
            td.textContent = cell ?? "-";
          }
          return td;
        }),
      ),
    );
  });
  return el("table", {}, [head, body]);
}

function field(label, control) {
  return el("label", { className: "field" }, [el("span", { text: label }), control]);
}

function detail(label, value) {
  return el("div", {}, [el("dt", { text: label }), el("dd", { text: value || "-" })]);
}

function actionButton(text, handler) {
  return el("button", { className: "button secondary", type: "button", text, onclick: handler });
}

function statusPill(status) {
  return el("span", {
    className: `status-pill ${String(status || "neutral").toLowerCase()}`,
    text: status || "-",
  });
}

function input(type, name, value, onInput, placeholder = "", disabled = false, extra = {}) {
  const node = el("input", { type, name, value: value ?? "", placeholder, disabled, ...extra });
  if (onInput) {
    node.addEventListener("input", onInput);
  }
  return node;
}

function inputHidden(name, value) {
  return el("input", { type: "hidden", name, value });
}

function checkbox(name, checked = false) {
  return el("input", { type: "checkbox", name, checked });
}

function select(name, options, value, disabled = false) {
  const node = el("select", { name, disabled });
  options.forEach(([optionValue, label]) => {
    const option = el("option", { value: optionValue, text: label });
    if (optionValue === value) {
      option.selected = true;
    }
    node.appendChild(option);
  });
  return node;
}

function memberSelect(name) {
  const options = [["", "Selecciona un miembro"]].concat(
    state.members.map((member) => [member.id, `${member.full_name} (${member.role_type})`]),
  );
  return select(name, options, "");
}

function vehicleSelect(name) {
  const options = [["", "Selecciona un vehiculo"]].concat(
    state.vehicles.map((vehicle) => [vehicle.id, `${vehicle.plate_text} - ${vehicle.brand} ${vehicle.model}`]),
  );
  return select(name, options, "");
}

function textarea(name, value, disabled = false) {
  const node = el("textarea", { name, disabled });
  node.value = value || "";
  return node;
}

function el(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attributes).forEach(([key, value]) => {
    if (value == null) return;
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "onclick") node.addEventListener("click", value);
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value);
  });
  const list = Array.isArray(children) ? children : [children];
  list.filter(Boolean).forEach((child) => {
    if (child instanceof Node) node.appendChild(child);
    else node.appendChild(document.createTextNode(String(child)));
  });
  return node;
}

function normalizePlate(value) {
  return String(value || "").trim().toUpperCase().replaceAll(" ", "").replaceAll("-", "");
}

function money(value, currency = "USD") {
  if (value == null || value === "") return "-";
  return `${currency} ${Number(value).toFixed(2)}`;
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function memberNameById(memberId) {
  return state.members.find((item) => item.id === memberId)?.full_name || memberId || "-";
}

function vehiclePlateById(vehicleId) {
  return state.vehicles.find((item) => item.id === vehicleId)?.plate_text || vehicleId || "-";
}

function formatTimestamp(value) {
  if (!value) return "-";
  return new Date(Number(value) * 1000).toLocaleString();
}

function parseDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") {
    try {
      const parsed = JSON.parse(detail);
      return parsed.detail || detail;
    } catch (_) {
      return detail;
    }
  }
  return detail.detail || "";
}

function localizeBackendMessage(message) {
  const text = String(message || "").trim();
  if (!text) return "Ocurrio un error inesperado.";
  if (text === "No active session found for this plate") return "No hay sesion activa para esta placa.";
  if (text.startsWith("Active session not found for plate")) return "No se encontro una sesion activa para esa placa.";
  if (text === "Cannot register payment for a closed session") {
    return "No se puede registrar un pago para una sesion ya cerrada.";
  }
  if (text === "Payment can only be registered when payment_status is PENDING") {
    return "Solo se puede registrar el pago cuando el estado es PENDING.";
  }
  if (text === "Provided amount does not match the calculated tariff") {
    return "El monto ingresado no coincide con la tarifa calculada.";
  }
  if (text === "Bearer token required") return "Debes iniciar sesion para realizar esta accion.";
  if (text.includes("Missing permissions")) return "Tu usuario no tiene permisos para registrar pagos.";
  return text;
}

boot();
