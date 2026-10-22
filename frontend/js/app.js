const elements = {
  alert: document.querySelector("#alert"),
  loginScreen: document.querySelector("#login-screen"),
  appShell: document.querySelector("#app-shell"),
  loginForm: document.querySelector("#login-form"),
  loginRole: document.querySelector("#login-role"),
  loginUsername: document.querySelector("#login-username"),
  loginUsernameLabel: document.querySelector("#login-username-label"),
  loginPassword: document.querySelector("#login-password"),
  logoutButton: document.querySelector("#logout-button"),
  authStatus: document.querySelector("#auth-status"),
  roleDescription: document.querySelector("#role-description"),
  connectionStatus: document.querySelector("#connection-status"),
  adminView: document.querySelector("#admin-view"),
  voterView: document.querySelector("#voter-view"),
  totalVotes: document.querySelector("#total-votes"),
  votersWhoVoted: document.querySelector("#voters-who-voted"),
  totalCandidates: document.querySelector("#total-candidates"),
  resultsList: document.querySelector("#results-list"),
  voterResultsList: document.querySelector("#voter-results-list"),
  votersTable: document.querySelector("#voters-table"),
  candidatesTable: document.querySelector("#candidates-table"),
  voterSelect: document.querySelector("#voter-select"),
  candidateSelect: document.querySelector("#candidate-select"),
  voterForm: document.querySelector("#voter-form"),
  candidateForm: document.querySelector("#candidate-form"),
  voteForm: document.querySelector("#vote-form"),
  refreshButton: document.querySelector("#refresh-button"),
  voterRefreshButton: document.querySelector("#voter-refresh-button"),
};

function showAlert(message) {
  elements.alert.textContent = message;
  elements.alert.classList.remove("hidden");
}

function clearAlert() {
  elements.alert.textContent = "";
  elements.alert.classList.add("hidden");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderResults(statistics, target) {
  target.innerHTML = statistics.candidates.length
    ? statistics.candidates.map((candidate) => `
      <div class="result-row">
        <div class="result-meta">
          <strong>${escapeHtml(candidate.candidate_name)}</strong>
          <small>${candidate.votes} voto(s) · ${candidate.percentage.toFixed(2)}%</small>
        </div>
        <div class="progress"><div class="progress-bar" style="width: ${candidate.percentage}%"></div></div>
      </div>
    `).join("")
    : '<p class="empty-state">Aún no hay candidatos registrados.</p>';
}

function renderAdminData(statistics, voters, candidates) {
  elements.totalVotes.textContent = statistics.total_votes;
  elements.votersWhoVoted.textContent = statistics.voters_who_voted;
  elements.totalCandidates.textContent = statistics.candidates.length;
  renderResults(statistics, elements.resultsList);
  elements.votersTable.innerHTML = voters.length
    ? voters.map((voter) => `<tr><td>${escapeHtml(voter.name)}</td><td>${escapeHtml(voter.email)}</td><td><span class="badge ${voter.has_voted ? "success" : "pending"}">${voter.has_voted ? "Ya votó" : "Pendiente"}</span></td></tr>`).join("")
    : '<tr><td colspan="3">No hay votantes registrados.</td></tr>';
  elements.candidatesTable.innerHTML = candidates.length
    ? candidates.map((candidate) => `<tr><td>${escapeHtml(candidate.name)}</td><td>${escapeHtml(candidate.party || "Sin partido")}</td><td>${candidate.votes}</td></tr>`).join("")
    : '<tr><td colspan="3">No hay candidatos registrados.</td></tr>';
}

function populateCandidateSelect(candidates) {
  elements.candidateSelect.innerHTML = `<option value="">Selecciona un candidato</option>${candidates.map((candidate) => `<option value="${candidate.id}">${escapeHtml(candidate.name)} - ${escapeHtml(candidate.party || "Sin partido")}</option>`).join("")}`;
}

async function loadAdminView() {
  const [statistics, voters, candidates] = await Promise.all([
    apiRequest("/votes/statistics"),
    apiRequest("/voters?skip=0&limit=100"),
    apiRequest("/candidates?skip=0&limit=100"),
  ]);
  renderAdminData(statistics, voters, candidates);
}

async function loadVoterView() {
  const [statistics, candidates] = await Promise.all([
    apiRequest("/votes/statistics"),
    apiRequest("/candidates?skip=0&limit=100"),
  ]);
  renderResults(statistics, elements.voterResultsList);
  populateCandidateSelect(candidates);
  elements.voterSelect.innerHTML = `<option value="${sessionStorage.getItem("votaciones_voter_id")}">Usuario autenticado</option>`;
}

async function loadCurrentView() {
  clearAlert();
  try {
    if (currentRole() === "admin") await loadAdminView();
    if (currentRole() === "voter") await loadVoterView();
    elements.connectionStatus.textContent = "API conectada";
  } catch (error) {
    elements.connectionStatus.textContent = "API no disponible";
    showAlert(error.message);
  }
}

function showAuthenticatedView() {
  const role = currentRole();
  const authenticated = isAuthenticated() && (role === "admin" || role === "voter");
  elements.loginScreen.classList.toggle("hidden", authenticated);
  elements.appShell.classList.toggle("hidden", !authenticated);
  elements.logoutButton.classList.toggle("hidden", !authenticated);
  elements.adminView.classList.toggle("hidden", role !== "admin");
  elements.voterView.classList.toggle("hidden", role !== "voter");
  elements.authStatus.textContent = role === "admin" ? "Administrador" : "Votante";
  elements.roleDescription.textContent = role === "admin" ? "Gestión completa del sistema" : "Emisión de voto personal";
}

elements.loginRole.addEventListener("change", () => {
  const voter = elements.loginRole.value === "voter";
  elements.loginUsernameLabel.textContent = voter ? "Email" : "Usuario";
  elements.loginUsername.placeholder = voter ? "correo@ejemplo.com" : "Usuario";
  elements.loginUsername.value = voter ? "" : "admin";
  elements.loginPassword.value = voter ? "" : "admin123";
});

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await login(elements.loginUsername.value, elements.loginPassword.value);
    showAuthenticatedView();
    await loadCurrentView();
  } catch (error) {
    showAlert(error.message);
  }
});

elements.logoutButton.addEventListener("click", () => {
  logout();
  showAuthenticatedView();
  clearAlert();
});

elements.voterForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await apiRequest("/voters", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(elements.voterForm))) });
    elements.voterForm.reset();
    await loadAdminView();
  } catch (error) {
    showAlert(error.message);
  }
});

elements.candidateForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(elements.candidateForm));
  if (!payload.party) payload.party = null;
  try {
    await apiRequest("/candidates", { method: "POST", body: JSON.stringify(payload) });
    elements.candidateForm.reset();
    await loadAdminView();
  } catch (error) {
    showAlert(error.message);
  }
});

elements.voteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await apiRequest("/votes", {
      method: "POST",
      body: JSON.stringify({ voter_id: Number(elements.voterSelect.value), candidate_id: Number(elements.candidateSelect.value) }),
    });
    elements.voteForm.reset();
    await loadVoterView();
  } catch (error) {
    showAlert(error.message);
  }
});

elements.refreshButton?.addEventListener("click", loadAdminView);
elements.voterRefreshButton?.addEventListener("click", loadVoterView);

showAuthenticatedView();
if (isAuthenticated()) loadCurrentView();
