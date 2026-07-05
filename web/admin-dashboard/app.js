const demoUsers = [
  { username: "super.admin", password: "demo1234!", role: "superadmin", name: "Super Admin" },
  { username: "admin.university", password: "demo1234!", role: "admin_university", name: "Admin Universidad" },
  { username: "security.agent", password: "demo1234!", role: "security", name: "Seguridad Central" },
  { username: "cashier.user", password: "demo1234!", role: "cashier", name: "Secretaria Caja" },
  { username: "auditor.user", password: "demo1234!", role: "auditor", name: "Auditor Interno" },
  { username: "gate.operator", password: "demo1234!", role: "gate_operator", name: "Operador de Puerta" }
];

const roleViews = {
  superadmin: ["overview", "universities", "campuses", "gates", "vehicles", "authorized", "sessions", "payments", "incidents", "audit"],
  admin_university: ["overview", "universities", "campuses", "gates", "vehicles", "authorized", "sessions", "payments", "incidents"],
  security: ["overview", "gates", "vehicles", "authorized", "sessions", "incidents"],
  cashier: ["payments"],
  gate_operator: ["overview", "gates", "sessions"],
  auditor: ["audit"],
  student: [],
  teacher: [],
  employee: [],
  visitor: []
};

const viewLabels = {
  overview: "Resumen",
  universities: "Universidades",
  campuses: "Campus",
  gates: "Puertas",
  vehicles: "Vehiculos",
  authorized: "Personas autorizadas",
  sessions: "Sesiones de parqueo",
  payments: "Pagos pendientes",
  incidents: "Incidentes",
  audit: "Auditoria"
};

const dataset = {
  universities: [
    { name: "Universidad Demo Andina", status: "Activa", campuses: 2, gates: 6, policy: "Operacion multi-campus" },
    { name: "Instituto Tecnologico del Pacifico", status: "Activa", campuses: 1, gates: 2, policy: "Control visitante y personal" }
  ],
  campuses: [
    { name: "Campus Central", university: "Universidad Demo Andina", city: "Quito", gates: 4, status: "Activo" },
    { name: "Campus Norte", university: "Universidad Demo Andina", city: "Quito", gates: 2, status: "Activo" },
    { name: "Campus Costero", university: "Instituto Tecnologico del Pacifico", city: "Manta", gates: 2, status: "Activo" }
  ],
  gates: [
    { name: "Puerta Norte", campus: "Campus Central", university: "Universidad Demo Andina", device: "Android Gate-01", mode: "Entrada y salida", barrier: "Online" },
    { name: "Puerta Sur", campus: "Campus Central", university: "Universidad Demo Andina", device: "iPhone Gate-02", mode: "Salida", barrier: "Online" },
    { name: "Puerta Biblioteca", campus: "Campus Norte", university: "Universidad Demo Andina", device: "Android Gate-03", mode: "Entrada", barrier: "Mantenimiento" }
  ],
  vehicles: [
    { plate: "ABC1234", type: "Sedan", ownerGroup: "Estudiantes", authorizedCount: 2, permit: "Vigente" },
    { plate: "PBC9087", type: "SUV", ownerGroup: "Docentes", authorizedCount: 1, permit: "Vigente" },
    { plate: "VIS4432", type: "Hatchback", ownerGroup: "Visitantes", authorizedCount: 0, permit: "Temporal" }
  ],
  authorizedPeople: [
    { name: "Daniela Rojas", role: "Student", plate: "ABC1234", permit: "2026-12-31", access: "Campus Central / Norte", biometric: "Perfil facial validado" },
    { name: "Marco Velasco", role: "Employee", plate: "ABC1234", permit: "2026-11-15", access: "Campus Central", biometric: "Perfil facial validado" },
    { name: "Patricia Molina", role: "Teacher", plate: "PBC9087", permit: "2026-10-01", access: "Campus Central", biometric: "Perfil facial validado" }
  ],
  sessions: [
    { plate: "VIS4432", personType: "Visitor", gateIn: "Puerta Norte", enteredAt: "2026-07-05 08:12", elapsed: "2h 14m", paymentStatus: "Pending", sessionStatus: "Inside" },
    { plate: "ABC1234", personType: "Student", gateIn: "Puerta Biblioteca", enteredAt: "2026-07-05 07:41", elapsed: "2h 45m", paymentStatus: "Exempt", sessionStatus: "Inside" },
    { plate: "PBC9087", personType: "Teacher", gateIn: "Puerta Norte", enteredAt: "2026-07-05 06:55", elapsed: "3h 31m", paymentStatus: "Exempt", sessionStatus: "Inside" }
  ],
  payments: [
    { plate: "VIS4432", visitor: "Visitante temporal", elapsed: "2h 14m", amount: "$3.00", status: "Pending", qr: "QR-VIS-001", gate: "Puerta Sur" },
    { plate: "TRS1102", visitor: "Visitante evento", elapsed: "4h 10m", amount: "$5.00", status: "Pending", qr: "QR-TRS-008", gate: "Puerta Norte" },
    { plate: "LKM2200", visitor: "Proveedor", elapsed: "55m", amount: "$2.00", status: "Paid", qr: "QR-LKM-003", gate: "Puerta Sur" }
  ],
  incidents: [
    { code: "INC-104", plate: "VIS4432", category: "Pago pendiente", severity: "High", status: "Abierto", gate: "Puerta Sur", time: "2026-07-05 10:18" },
    { code: "INC-105", plate: "ZZZ1901", category: "Liveness bajo", severity: "Medium", status: "En revision", gate: "Puerta Norte", time: "2026-07-05 09:54" },
    { code: "INC-106", plate: "ABC1234", category: "Dispositivo sin red", severity: "Low", status: "Resuelto", gate: "Puerta Biblioteca", time: "2026-07-05 08:47" }
  ],
  audit: [
    { at: "2026-07-05 10:18", actor: "security.agent", role: "Security", action: "incident.created", service: "parking-service", result: "denied" },
    { at: "2026-07-05 10:06", actor: "cashier.user", role: "Cashier", action: "payment.completed", service: "payment-service", result: "success" },
    { at: "2026-07-05 09:58", actor: "super.admin", role: "Superadmin", action: "gate.updated", service: "university-service", result: "success" }
  ]
};

const appState = {
  user: null,
  activeView: "overview",
  error: ""
};

function boot() {
  const saved = sessionStorage.getItem("adminDashboardUser");
  if (saved) {
    appState.user = JSON.parse(saved);
    appState.activeView = firstAvailableView(appState.user.role);
  }
  render();
}

function render() {
  const root = document.getElementById("app");
  root.innerHTML = "";
  if (!appState.user) {
    root.appendChild(renderLogin());
    return;
  }
  root.appendChild(renderDashboard());
}

function renderLogin() {
  const shell = createElement("div", { className: "login-shell" });
  const layout = createElement("div", { className: "login-layout" });
  const panel = createElement("section", { className: "login-panel" });
  const preview = createElement("aside", { className: "login-preview" });

  panel.append(
    createElement("p", { className: "brand-kicker", text: "Smart Parking University" }),
    createElement("h1", { className: "login-title", text: "Dashboard administrativo" }),
    createElement("p", {
      className: "login-copy",
      text: "Interfaz operativa mobile-first para universidades, campus, puertas, sesiones, pagos, incidentes y auditoria."
    })
  );

  const form = createElement("form", { className: "login-form" });
  const userInput = createElement("input", {
    className: "text-input",
    type: "text",
    name: "username",
    placeholder: "Usuario demo"
  });
  const passwordInput = createElement("input", {
    className: "text-input",
    type: "password",
    name: "password",
    placeholder: "Clave demo"
  });

  form.append(
    field("Usuario", userInput),
    field("Clave", passwordInput),
    createElement("button", { className: "primary-action", type: "submit", text: "Ingresar" })
  );

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const username = userInput.value.trim();
    const password = passwordInput.value;
    const found = demoUsers.find((item) => item.username === username && item.password === password);
    if (!found) {
      appState.error = "Credenciales demo no validas.";
      render();
      return;
    }
    appState.user = { username: found.username, role: found.role, name: found.name };
    appState.activeView = firstAvailableView(found.role);
    appState.error = "";
    sessionStorage.setItem("adminDashboardUser", JSON.stringify(appState.user));
    render();
  });

  const chips = createElement("div", { className: "demo-chip-row" });
  demoUsers.forEach((item) => {
    const chip = createElement("button", {
      className: "demo-chip",
      type: "button",
      text: humanizeRole(item.role)
    });
    chip.addEventListener("click", () => {
      userInput.value = item.username;
      passwordInput.value = item.password;
    });
    chips.appendChild(chip);
  });

  panel.append(
    form,
    createElement("p", { className: "section-copy", text: "Perfiles demo:" }),
    chips,
    createElement("div", {
      className: "info-banner",
      text: "Este dashboard no expone fotos, embeddings ni evidencia biometrica completa. Solo muestra informacion operativa minima segun el rol."
    })
  );

  if (appState.error) {
    panel.appendChild(createElement("div", { className: "error-banner", text: appState.error }));
  }

  const previewHero = createElement("div", { className: "preview-hero" });
  previewHero.append(
    createElement("p", { className: "brand-kicker", text: "Operacion en vivo" }),
    createElement("h2", { className: "section-title", text: "Control multiuniversidad para puertas y parqueaderos" }),
    createElement("p", {
      className: "section-copy",
      text: "La vista administrativa separa pagos, seguridad, operacion y auditoria para reducir exposicion innecesaria de datos."
    }),
    metricGrid([
      ["Universidades activas", "2"],
      ["Puertas monitoreadas", "8"],
      ["Sesiones abiertas", "30"],
      ["Pagos pendientes", "3"]
    ]),
    listNote([
      "Secretaria: ve placa, tiempo, monto y estado de pago.",
      "Seguridad: ve incidentes y estado operativo.",
      "Auditor: consulta eventos y trazabilidad.",
      "Sin datos biometricos completos en esta interfaz."
    ])
  );

  preview.appendChild(previewHero);
  layout.append(panel, preview);
  shell.appendChild(layout);
  return shell;
}

function renderDashboard() {
  const availableViews = roleViews[appState.user.role] || [];
  const shell = createElement("div", { className: "app-shell" });
  shell.appendChild(renderTopbar());
  shell.appendChild(renderNavStrip(availableViews));

  const workspace = createElement("div", { className: "workspace" });
  workspace.appendChild(renderSidebar(availableViews));
  const content = createElement("main", { className: "content" });
  const stack = createElement("div", { className: "content-stack" });
  stack.appendChild(renderView(appState.activeView));
  content.appendChild(stack);
  workspace.appendChild(content);
  shell.appendChild(workspace);
  return shell;
}

function renderTopbar() {
  const topbar = createElement("header", { className: "topbar" });
  const row = createElement("div", { className: "topbar-row" });
  const left = createElement("div");
  left.append(
    createElement("h1", { className: "topbar-title", text: "Smart Parking University" }),
    createElement("p", { className: "section-copy", text: "Panel operativo con visibilidad limitada por rol." })
  );

  const right = createElement("div", { className: "topbar-actions" });
  right.append(
    createElement("span", { className: "role-badge", text: humanizeRole(appState.user.role) }),
    createElement("span", { className: "status-badge status-neutral", text: appState.user.name })
  );
  const logout = createElement("button", { className: "logout-button", type: "button", text: "Salir" });
  logout.addEventListener("click", () => {
    sessionStorage.removeItem("adminDashboardUser");
    appState.user = null;
    appState.activeView = "overview";
    appState.error = "";
    render();
  });
  right.appendChild(logout);

  row.append(left, right);
  topbar.appendChild(row);
  return topbar;
}

function renderNavStrip(availableViews) {
  const strip = createElement("div", { className: "nav-strip" });
  const inner = createElement("div", { className: "nav-strip-inner" });
  availableViews.forEach((view) => inner.appendChild(createNavButton(view)));
  strip.appendChild(inner);
  return strip;
}

function renderSidebar(availableViews) {
  const sidebar = createElement("aside", { className: "sidebar" });
  sidebar.append(
    createElement("h2", { text: "Navegacion" }),
    createElement("p", { text: "Vista segura para operaciones universitarias." })
  );
  const nav = createElement("div", { className: "sidebar-nav" });
  availableViews.forEach((view) => nav.appendChild(createNavButton(view)));
  sidebar.appendChild(nav);
  return sidebar;
}

function createNavButton(view) {
  const button = createElement("button", {
    className: `nav-button${appState.activeView === view ? " active" : ""}`,
    type: "button",
    text: viewLabels[view]
  });
  button.addEventListener("click", () => {
    appState.activeView = view;
    render();
  });
  return button;
}

function renderView(view) {
  switch (view) {
    case "overview":
      return renderOverview();
    case "universities":
      return renderUniversities();
    case "campuses":
      return renderCampuses();
    case "gates":
      return renderGates();
    case "vehicles":
      return renderVehicles();
    case "authorized":
      return renderAuthorizedPeople();
    case "sessions":
      return renderSessions();
    case "payments":
      return renderPayments();
    case "incidents":
      return renderIncidents();
    case "audit":
      return renderAudit();
    default:
      return baseSection("Vista no disponible", "No hay contenido para este rol.", createElement("div", { className: "empty-state", text: "Seleccione otra vista." }));
  }
}

function renderOverview() {
  return baseSection(
    "Resumen operativo",
    "KPIs rapidos para operacion diaria de parqueaderos universitarios.",
    summaryGrid([
      ["Universidades", String(dataset.universities.length)],
      ["Puertas activas", String(dataset.gates.filter((item) => item.barrier === "Online").length)],
      ["Pagos pendientes", String(dataset.payments.filter((item) => item.status === "Pending").length)],
      ["Incidentes abiertos", String(dataset.incidents.filter((item) => item.status !== "Resuelto").length)]
    ]),
    createElement("div", {
      className: "info-banner",
      text: "La interfaz web opera como panel administrativo ligero. Los datos biometricos permanecen fuera de esta vista."
    })
  );
}

function renderUniversities() {
  return baseSection(
    "Universidades",
    "Configuracion general por institucion.",
    renderCardGrid(dataset.universities.map((item) =>
      entityCard(item.name, item.policy, [
        detail("Estado", statusBadge(item.status)),
        detail("Campus", String(item.campuses)),
        detail("Puertas", String(item.gates)),
        detail("Politica", item.policy)
      ])
    ))
  );
}

function renderCampuses() {
  return baseSection(
    "Campus",
    "Distribucion operativa por sede.",
    renderCardGrid(dataset.campuses.map((item) =>
      entityCard(item.name, item.university, [
        detail("Ciudad", item.city),
        detail("Puertas", String(item.gates)),
        detail("Estado", statusBadge(item.status)),
        detail("Universidad", item.university)
      ])
    ))
  );
}

function renderGates() {
  return baseSection(
    "Puertas",
    "Monitoreo de dispositivos y estado de barrera.",
    renderCardGrid(dataset.gates.map((item) =>
      entityCard(item.name, `${item.university} / ${item.campus}`, [
        detail("Dispositivo", item.device),
        detail("Modo", item.mode),
        detail("Estado barrera", statusBadge(item.barrier)),
        detail("Campus", item.campus)
      ])
    ))
  );
}

function renderVehicles() {
  return baseSection(
    "Vehiculos",
    "Placas registradas y vigencia operativa.",
    renderTable(
      ["Placa", "Tipo", "Grupo", "Autorizados", "Permiso"],
      dataset.vehicles.map((item) => [item.plate, item.type, item.ownerGroup, String(item.authorizedCount), statusBadge(item.permit)])
    )
  );
}

function renderAuthorizedPeople() {
  const canSeeBiometricFlag = ["superadmin", "admin_university", "security"].includes(appState.user.role);
  const headers = canSeeBiometricFlag
    ? ["Persona", "Rol", "Placa", "Permiso hasta", "Acceso", "Biometria"]
    : ["Persona", "Rol", "Placa", "Permiso hasta", "Acceso"];
  const rows = dataset.authorizedPeople.map((item) => {
    const base = [item.name, item.role, item.plate, item.permit, item.access];
    if (canSeeBiometricFlag) base.push("Solo estado operativo");
    return base;
  });

  return baseSection(
    "Personas autorizadas",
    "Relacion entre placas y personas habilitadas. Nunca se exponen fotos ni embeddings desde este panel.",
    renderTable(headers, rows),
    createElement("div", {
      className: "restricted-banner",
      text: "La columna de biometria muestra unicamente un estado operativo resumido para roles administrativos o de seguridad."
    })
  );
}

function renderSessions() {
  return baseSection(
    "Sesiones de parqueo",
    "Sesiones activas y estado de validacion.",
    renderTable(
      ["Placa", "Tipo", "Puerta de ingreso", "Ingreso", "Tiempo", "Pago", "Estado"],
      dataset.sessions.map((item) => [
        item.plate,
        item.personType,
        item.gateIn,
        item.enteredAt,
        item.elapsed,
        statusBadge(item.paymentStatus),
        statusBadge(item.sessionStatus)
      ])
    )
  );
}

function renderPayments() {
  const isCashier = appState.user.role === "cashier";
  const headers = isCashier
    ? ["Placa", "Tiempo", "Monto", "Estado de pago"]
    : ["Placa", "Visitante", "Tiempo", "Monto", "Estado de pago", "QR", "Puerta"];
  const rows = dataset.payments.map((item) => (
    isCashier
      ? [item.plate, item.elapsed, item.amount, statusBadge(item.status)]
      : [item.plate, item.visitor, item.elapsed, item.amount, statusBadge(item.status), item.qr, item.gate]
  ));

  return baseSection(
    "Pagos pendientes",
    isCashier
      ? "Vista reducida para secretaria: placa, tiempo, monto y estado de pago."
      : "Control de cobro para visitas y proveedores.",
    renderTable(headers, rows),
    isCashier
      ? createElement("div", { className: "restricted-banner", text: "Este rol no ve biometria, incidencias, QR completo ni trazas de auditoria." })
      : createElement("div", { className: "info-banner", text: "Los pagos se muestran con informacion operativa minima para caja." })
  );
}

function renderIncidents() {
  return baseSection(
    "Incidentes",
    "Eventos de rechazo, liveness bajo, problemas de pago o fallos operativos.",
    renderTable(
      ["Codigo", "Placa", "Categoria", "Severidad", "Estado", "Puerta", "Fecha"],
      dataset.incidents.map((item) => [
        item.code,
        item.plate,
        item.category,
        severityBadge(item.severity),
        statusBadge(item.status),
        item.gate,
        item.time
      ])
    )
  );
}

function renderAudit() {
  if (!["auditor", "superadmin"].includes(appState.user.role)) {
    return baseSection(
      "Auditoria",
      "Consulta restringida.",
      createElement("div", {
        className: "restricted-banner",
        text: "Solo auditor y superadmin pueden consultar el log completo de auditoria."
      })
    );
  }

  return baseSection(
    "Auditoria",
    "Trazabilidad resumida por actor, servicio y resultado.",
    renderTable(
      ["Fecha", "Actor", "Rol", "Accion", "Servicio", "Resultado"],
      dataset.audit.map((item) => [
        item.at,
        item.actor,
        item.role,
        item.action,
        item.service,
        statusBadge(item.result)
      ])
    )
  );
}

function baseSection(title, copy, ...children) {
  const section = createElement("section", { className: "surface-panel" });
  section.append(
    createElement("p", { className: "section-kicker", text: "Vista" }),
    createElement("h2", { className: "section-title", text: title }),
    createElement("p", { className: "section-copy", text: copy })
  );
  children.forEach((child) => section.appendChild(child));
  return section;
}

function renderCardGrid(cards) {
  const grid = createElement("div", { className: "list-grid" });
  cards.forEach((card) => grid.appendChild(card));
  return grid;
}

function entityCard(title, subtitle, details) {
  const card = createElement("article", { className: "entity-card" });
  const topline = createElement("div", { className: "entity-topline" });
  topline.appendChild(createElement("h3", { className: "entity-title", text: title }));
  card.append(topline, createElement("p", { className: "entity-subtitle", text: subtitle }));
  const grid = createElement("dl", { className: "detail-grid" });
  details.forEach((item) => grid.appendChild(item));
  card.appendChild(grid);
  return card;
}

function renderTable(headers, rows) {
  if (!rows.length) {
    return createElement("div", { className: "empty-state", text: "No hay registros para mostrar." });
  }
  const panel = createElement("div", { className: "table-panel" });
  const wrap = createElement("div", { className: "data-table-wrap" });
  const table = createElement("table", { className: "data-table" });
  const thead = createElement("thead");
  const headerRow = createElement("tr");
  headers.forEach((header) => headerRow.appendChild(createElement("th", { text: header })));
  thead.appendChild(headerRow);
  const tbody = createElement("tbody");
  rows.forEach((row) => {
    const tr = createElement("tr");
    row.forEach((cell) => {
      const td = createElement("td");
      if (cell instanceof Node) {
        td.appendChild(cell);
      } else {
        td.textContent = cell;
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.append(thead, tbody);
  wrap.appendChild(table);
  panel.append(wrap, createElement("p", { className: "table-caption", text: "Mock operativo para exposicion y futuras integraciones con FastAPI." }));
  return panel;
}

function summaryGrid(items) {
  const grid = createElement("div", { className: "summary-grid" });
  items.forEach(([label, value]) => {
    const card = createElement("div", { className: "summary-item" });
    card.append(createElement("span", { className: "metric-label", text: label }), createElement("strong", { text: value }));
    grid.appendChild(card);
  });
  return grid;
}

function metricGrid(items) {
  const grid = createElement("div", { className: "preview-grid" });
  items.forEach(([label, value]) => {
    const card = createElement("div", { className: "metric-card" });
    card.append(createElement("span", { className: "metric-label", text: label }), createElement("span", { className: "metric-value", text: value }));
    grid.appendChild(card);
  });
  return grid;
}

function listNote(items) {
  const list = createElement("ul", { className: "preview-list" });
  items.forEach((item) => list.appendChild(createElement("li", { text: item })));
  return list;
}

function field(label, input) {
  const wrapper = createElement("label", { className: "field-label" });
  wrapper.append(createElement("span", { text: label }), input);
  return wrapper;
}

function detail(label, value) {
  const item = createElement("div", { className: "detail-row" });
  item.append(createElement("dt", { text: label }));
  const dd = createElement("dd");
  if (value instanceof Node) {
    dd.appendChild(value);
  } else {
    dd.textContent = value;
  }
  item.appendChild(dd);
  return item;
}

function statusBadge(value) {
  return createElement("span", { className: `status-badge ${inferStatusTone(value)}`, text: value });
}

function severityBadge(value) {
  const tone = value === "High" ? "status-danger" : value === "Medium" ? "status-warning" : "status-neutral";
  return createElement("span", { className: `status-badge ${tone}`, text: value });
}

function inferStatusTone(value) {
  const normalized = String(value).toLowerCase();
  if (["activa", "activo", "online", "inside", "paid", "vigente", "success", "resuelto", "validated", "exempt"].includes(normalized)) {
    return "status-success";
  }
  if (["pending", "pago pendiente", "mantenimiento", "en revision", "temporal"].includes(normalized)) {
    return "status-warning";
  }
  if (["denied", "blocked", "fallido", "abierto"].includes(normalized)) {
    return "status-danger";
  }
  return "status-neutral";
}

function firstAvailableView(role) {
  const views = roleViews[role] || [];
  return views[0] || "overview";
}

function humanizeRole(role) {
  const labels = {
    superadmin: "Superadmin",
    admin_university: "Admin universidad",
    security: "Seguridad",
    cashier: "Secretaria",
    gate_operator: "Operador de puerta",
    auditor: "Auditor"
  };
  return labels[role] || role;
}

function createElement(tag, options = {}) {
  const element = document.createElement(tag);
  if (options.className) element.className = options.className;
  if (options.text !== undefined) element.textContent = options.text;
  if (options.type) element.type = options.type;
  if (options.name) element.name = options.name;
  if (options.placeholder) element.placeholder = options.placeholder;
  return element;
}

boot();
