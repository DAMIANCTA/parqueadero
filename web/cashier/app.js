const state = {
  token: null,
  roles: [],
  currentSession: null,
};

const els = {
  gatewayUrl: document.getElementById("gatewayUrl"),
  authUrl: document.getElementById("authUrl"),
  username: document.getElementById("username"),
  password: document.getElementById("password"),
  loginBtn: document.getElementById("loginBtn"),
  sessionBadge: document.getElementById("sessionBadge"),
  plateInput: document.getElementById("plateInput"),
  searchBtn: document.getElementById("searchBtn"),
  searchMessage: document.getElementById("searchMessage"),
  sessionCard: document.getElementById("sessionCard"),
  sessionId: document.getElementById("sessionId"),
  sessionPlate: document.getElementById("sessionPlate"),
  entryTime: document.getElementById("entryTime"),
  duration: document.getElementById("duration"),
  amount: document.getElementById("amount"),
  paymentStatus: document.getElementById("paymentStatus"),
  amountInput: document.getElementById("amountInput"),
  paymentMethod: document.getElementById("paymentMethod"),
  notesInput: document.getElementById("notesInput"),
  payBtn: document.getElementById("payBtn"),
  paymentHint: document.getElementById("paymentHint"),
  receiptCard: document.getElementById("receiptCard"),
  receiptNumber: document.getElementById("receiptNumber"),
  receiptSessionId: document.getElementById("receiptSessionId"),
  receiptPlate: document.getElementById("receiptPlate"),
  receiptAmount: document.getElementById("receiptAmount"),
  receiptMethod: document.getElementById("receiptMethod"),
  receiptPaidAt: document.getElementById("receiptPaidAt"),
  receiptAudit: document.getElementById("receiptAudit"),
};

els.loginBtn.addEventListener("click", login);
els.searchBtn.addEventListener("click", searchByPlate);
els.payBtn.addEventListener("click", registerPayment);

function normalizePlate(value) {
  return value.trim().toUpperCase().replaceAll(" ", "").replaceAll("-", "");
}

function gateway(path) {
  return `${els.gatewayUrl.value.trim().replace(/\/$/, "")}${path}`;
}

function auth(path) {
  return `${els.authUrl.value.trim().replace(/\/$/, "")}${path}`;
}

async function login() {
  setStatus("Autenticando...");
  try {
    const response = await fetch(auth("/auth/token"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: els.username.value.trim(),
        password: els.password.value,
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || "No se pudo iniciar sesion.");
    }
    state.token = body.access_token;
    state.roles = body.roles || [];
    setStatus(`Sesion activa: ${els.username.value.trim()} (${state.roles.join(", ")})`, false);
    els.paymentHint.textContent = "Rol autenticado. Ya puedes registrar pagos si tienes payments.pay.";
  } catch (error) {
    state.token = null;
    state.roles = [];
    setStatus(error.message || "Error de autenticacion.", true);
  }
}

async function searchByPlate() {
  const plate = normalizePlate(els.plateInput.value);
  if (!plate) {
    els.searchMessage.textContent = "Ingresa una placa para buscar.";
    return;
  }

  els.searchMessage.textContent = "Consultando sesion activa...";
  hideReceipt();
  try {
    const headers = {};
    if (state.token) {
      headers.Authorization = `Bearer ${state.token}`;
    }
    const response = await fetch(gateway(`/payments/by-plate/${encodeURIComponent(plate)}`), { headers });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(parseDetail(body.detail) || "No se encontro sesion activa.");
    }
    state.currentSession = body;
    renderSession(body);
    els.searchMessage.textContent = "Sesion activa encontrada.";
  } catch (error) {
    state.currentSession = null;
    els.sessionCard.classList.add("hidden");
    els.searchMessage.textContent = error.message || "No se pudo consultar la sesion.";
  }
}

async function registerPayment() {
  if (!state.currentSession) {
    els.paymentHint.textContent = "Busca primero una sesion activa.";
    return;
  }
  if (!state.token) {
    els.paymentHint.textContent = "Debes iniciar sesion como cashier o admin.";
    return;
  }

  const payload = {
    session_id: state.currentSession.session_id,
    plate_text: state.currentSession.plate_text,
    amount: Number.parseFloat(els.amountInput.value),
    payment_method: els.paymentMethod.value,
    cashier_user_id: els.username.value.trim(),
    notes: els.notesInput.value.trim() || "Pago en secretaria",
  };

  els.paymentHint.textContent = "Registrando pago...";
  try {
    const response = await fetch(gateway("/payments/register-cash-payment"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(parseDetail(body.detail) || "No se pudo registrar el pago.");
    }

    state.currentSession = body.session;
    renderSession(body.session);
    renderReceipt(body, payload.payment_method, payload.amount);
    els.paymentHint.textContent = "Pago registrado correctamente.";
  } catch (error) {
    hideReceipt();
    els.paymentHint.textContent = error.message || "No se pudo registrar el pago.";
  }
}

function renderSession(session) {
  els.sessionCard.classList.remove("hidden");
  els.sessionId.textContent = session.session_id;
  els.sessionPlate.textContent = session.plate_text;
  els.entryTime.textContent = formatDateTime(session.entry_time);
  els.duration.textContent = `${session.duration_minutes} min`;
  els.amount.textContent = `${session.currency} ${Number(session.amount).toFixed(2)}`;
  els.paymentStatus.textContent = session.payment_status;
  els.amountInput.value = Number(session.amount).toFixed(2);
}

function renderReceipt(response, paymentMethod, amount) {
  els.receiptCard.classList.remove("hidden");
  els.receiptNumber.textContent = response.receipt_number || "-";
  els.receiptSessionId.textContent = response.session?.session_id || "-";
  els.receiptPlate.textContent = response.session?.plate_text || "-";
  els.receiptAmount.textContent = `${response.session?.currency || "USD"} ${Number(amount).toFixed(2)}`;
  els.receiptMethod.textContent = paymentMethod;
  els.receiptPaidAt.textContent = formatDateTime(response.paid_at);
  els.receiptAudit.textContent = response.audit_log_id || "-";
}

function hideReceipt() {
  els.receiptCard.classList.add("hidden");
}

function setStatus(message, isError = false) {
  els.sessionBadge.textContent = message;
  els.sessionBadge.className = `badge${isError ? " muted" : ""}`;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function parseDetail(detail) {
  if (!detail) {
    return "";
  }
  if (typeof detail === "string") {
    try {
      const parsed = JSON.parse(detail);
      if (parsed.detail) {
        return parsed.detail;
      }
    } catch (_) {
      return detail;
    }
    return detail;
  }
  return detail.detail || "";
}
