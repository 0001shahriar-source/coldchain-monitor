const API_BASE = '/api';
let authToken = localStorage.getItem('token') || '';
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');

let fridgesData = [];
let batchesData = [];

// Helper to escape HTML and prevent Stored XSS
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function init() {
  updateAuthUI();
  setupWebSocket();
  fetchDashboard();
  setInterval(fetchDashboard, 3000);

  // Check URL Query Parameters for direct QR code scanning from smartphone
  const urlParams = new URLSearchParams(window.location.search);
  const tabParam = urlParams.get('tab');
  const batchIdParam = urlParams.get('batchId');

  if (tabParam === 'publicQr') {
    switchTab('publicQr');
    if (batchIdParam) {
      const input = document.getElementById('publicBatchInput');
      if (input) {
        input.value = batchIdParam;
        fetchPublicQr();
      }
    }
  }
}

function openAddBatchModal() {
  if (!authToken) {
    alert('Please sign in as Admin or Pharmacist to register batches');
    openLoginModal();
    return;
  }
  if (currentUser && currentUser.role === 'Inspector') {
    alert('Inspectors have Read-Only audit access.');
    return;
  }
  document.getElementById('addBatchModal').classList.remove('hidden');
  document.getElementById('addBatchModal').classList.add('flex');
}

function closeAddBatchModal() {
  document.getElementById('addBatchModal').classList.add('hidden');
  document.getElementById('addBatchModal').classList.remove('flex');
}

async function submitNewBatch() {
  const id = document.getElementById('newBatchId').value.trim();
  const name = document.getElementById('newBatchName').value.trim();
  const fridgeId = document.getElementById('newBatchFridge').value;
  const expiryDate = document.getElementById('newBatchExpiry').value;

  if (!name || !expiryDate) {
    alert('Please provide vaccine name and expiry date');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/inventory/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ id, name, fridgeId, expiryDate })
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Batch ${data.id} registered successfully!`);
      closeAddBatchModal();
      fetchDashboard();
    } else {
      alert(data.error || 'Failed to register batch');
    }
  } catch (e) {
    alert('Network error connecting to backend');
  }
}

function updateAuthUI() {
  const userInfo = document.getElementById('userInfo');
  const loginBtn = document.getElementById('loginBtn');
  const userRole = document.getElementById('userRole');

  if (authToken && currentUser) {
    userInfo.classList.remove('hidden');
    userInfo.classList.add('flex');
    loginBtn.classList.add('hidden');
    userRole.textContent = `${currentUser.username} (${currentUser.role})`;

    // Hide mutating actions for Inspector role
    const isInspector = currentUser.role === 'Inspector';
    const regBatchBtn = document.querySelector('button[onclick="openAddBatchModal()"]');
    if (regBatchBtn) regBatchBtn.style.display = isInspector ? 'none' : 'flex';
  } else {
    userInfo.classList.add('hidden');
    loginBtn.classList.remove('hidden');
  }
}

function openLoginModal() {
  document.getElementById('loginModal').classList.remove('hidden');
  document.getElementById('loginModal').classList.add('flex');
  selectRolePreset('Admin');
}

function selectRolePreset(role) {
  const uInput = document.getElementById('loginUsername');
  const pInput = document.getElementById('loginPassword');
  
  const pills = {
    'Admin': document.getElementById('pill-admin'),
    'Pharmacist': document.getElementById('pill-pharmacist'),
    'Inspector': document.getElementById('pill-inspector')
  };

  // Reset pill styles
  Object.values(pills).forEach(p => {
    if (p) {
      p.className = 'role-pill py-1.5 text-xs font-medium rounded-lg transition text-slate-400 hover:text-white';
    }
  });

  // Activate selected pill and fill credentials
  if (role === 'Admin') {
    if (pills['Admin']) pills['Admin'].className = 'role-pill py-1.5 text-xs font-semibold rounded-lg transition bg-blue-600 text-white shadow';
    uInput.value = 'admin';
    pInput.value = 'admin123';
  } else if (role === 'Pharmacist') {
    if (pills['Pharmacist']) pills['Pharmacist'].className = 'role-pill py-1.5 text-xs font-semibold rounded-lg transition bg-blue-600 text-white shadow';
    uInput.value = 'pharmacist';
    pInput.value = 'pharma123';
  } else if (role === 'Inspector') {
    if (pills['Inspector']) pills['Inspector'].className = 'role-pill py-1.5 text-xs font-semibold rounded-lg transition bg-blue-600 text-white shadow';
    uInput.value = 'inspector';
    pInput.value = 'inspect123';
  }
}

function closeLoginModal() {
  document.getElementById('loginModal').classList.add('hidden');
  document.getElementById('loginModal').classList.remove('flex');
}

async function executeLogin() {
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
      authToken = data.token;
      currentUser = { username: data.username, role: data.role };
      localStorage.setItem('token', authToken);
      localStorage.setItem('user', JSON.stringify(currentUser));
      updateAuthUI();
      closeLoginModal();
      fetchDashboard();
    } else {
      alert(data.error || 'Authentication failed');
    }
  } catch (err) {
    alert('Server unreachable');
  }
}

function logout() {
  authToken = '';
  currentUser = null;
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  updateAuthUI();
}

function switchTab(tabId) {
  ['dashboard', 'inventory', 'ai', 'security', 'publicQr'].forEach(t => {
    document.getElementById(`tab-${t}`).classList.add('hidden');
    const btn = document.getElementById(`tabBtn-${t}`);
    btn.classList.remove('border-blue-500', 'text-blue-400');
    btn.classList.add('border-transparent', 'text-slate-400');
  });

  document.getElementById(`tab-${tabId}`).classList.remove('hidden');
  const activeBtn = document.getElementById(`tabBtn-${tabId}`);
  activeBtn.classList.add('border-blue-500', 'text-blue-400');
  activeBtn.classList.remove('border-transparent', 'text-slate-400');

  if (tabId === 'security') fetchAuditLogs();
  if (tabId === 'ai') fetchAiRecommendations();
  if (tabId === 'publicQr') fetchPublicQr();
}

async function fetchDashboard() {
  if (!authToken) return;
  try {
    const res = await fetch(`${API_BASE}/dashboard`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    if (res.status === 401 || res.status === 403) {
      logout();
      return;
    }
    const data = await res.json();
    fridgesData = data.fridges;
    batchesData = data.batches;

    renderFridges(data.fridges);
    renderBatches(data.batches);
    updateInventoryDropdowns(data.batches, data.fridges);
  } catch (err) {
    console.error('Error fetching dashboard', err);
  }
}

function renderFridges(fridges) {
  const container = document.getElementById('fridgeContainer');
  container.innerHTML = fridges.map(f => {
    let badgeColor = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    let statusLabel = 'Safe';
    if (f.temp > 8.0) {
      badgeColor = 'bg-red-500/10 text-red-400 border-red-500/20';
      statusLabel = 'Breach (>8°C)';
    } else if (f.temp > 6.0 || f.temp < 3.0) {
      badgeColor = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      statusLabel = 'Warning';
    }

    return `
      <div class="bg-slate-800/50 border border-slate-700/60 rounded-3xl p-6 backdrop-blur space-y-4 hover:border-slate-600 transition">
        <div class="flex justify-between items-start">
          <div>
            <span class="text-xs font-mono text-slate-400 uppercase">${f.id}</span>
            <h3 class="text-lg font-bold text-white">${f.name}</h3>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-semibold border ${badgeColor}">
            ${statusLabel}
          </span>
        </div>

        <div class="flex items-baseline space-x-2">
          <span class="text-4xl font-extrabold text-white tracking-tight">${f.temp.toFixed(1)}</span>
          <span class="text-xl font-bold text-slate-400">°C</span>
          <span class="text-xs text-slate-500 ml-2">Target: 2°C – 8°C</span>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-700/60 text-xs">
          <div class="bg-slate-900/60 p-2 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Compressor</span>
            <span class="font-bold ${f.compressor ? 'text-blue-400' : 'text-slate-400'}">
              <i class="fa-solid fa-fan mr-1 ${f.compressor ? 'animate-spin' : ''}"></i> ${f.compressor ? 'ACTIVE' : 'IDLE'}
            </span>
          </div>

          <div class="bg-slate-900/60 p-2 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Door State</span>
            <span class="font-bold ${f.doorOpen ? 'text-red-400' : 'text-emerald-400'}">
              <i class="fa-solid ${f.doorOpen ? 'fa-door-open' : 'fa-door-closed'} mr-1"></i> ${f.doorOpen ? 'OPEN' : 'CLOSED'}
            </span>
          </div>

          <div class="bg-slate-900/60 p-2 rounded-xl">
            <span class="text-slate-400 block mb-0.5">Power Supply</span>
            <span class="font-bold ${f.power === 'AC' ? 'text-emerald-400' : 'text-amber-400'}">
              <i class="fa-solid fa-plug mr-1"></i> ${f.power} (${f.battery}%)
            </span>
          </div>

          <div class="bg-slate-900/60 p-2 rounded-xl">
            <span class="text-slate-400 block mb-0.5">AI Health Score</span>
            <span class="font-bold text-purple-400">
              ${f.healthScore || 94}/100
            </span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderBatches(batches) {
  const tbody = document.getElementById('batchTableBody');
  tbody.innerHTML = batches.map(b => {
    let statusBadge = '<span class="px-2 py-0.5 rounded text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 font-bold">Safe</span>';
    if (b.status === 'Discard') {
      statusBadge = '<span class="px-2 py-0.5 rounded text-red-400 bg-red-500/10 border border-red-500/20 font-bold animate-pulse">Discard (Red LED ON)</span>';
    } else if (b.status === 'At Risk') {
      statusBadge = '<span class="px-2 py-0.5 rounded text-amber-400 bg-amber-500/10 border border-amber-500/20 font-bold">At Risk (&lt;20%)</span>';
    }

    const pct = b.remainingPct || 100;
    const barColor = pct < 20 ? 'bg-red-500' : pct < 50 ? 'bg-amber-500' : 'bg-emerald-500';

    return `
      <tr class="hover:bg-slate-800/40">
        <td class="p-3 font-mono font-medium text-slate-300">${b.id}</td>
        <td class="p-3 font-semibold text-white">${b.name}</td>
        <td class="p-3 text-slate-400">${b.fridgeId}</td>
        <td class="p-3">
          <div class="w-32 bg-slate-700/60 rounded-full h-2 mb-1 overflow-hidden">
            <div class="${barColor} h-2 rounded-full" style="width: ${pct}%"></div>
          </div>
          <span class="text-[10px] text-slate-400">${b.remainingMinutes}m left (${pct}%)</span>
        </td>
        <td class="p-3 text-slate-300">${b.exposureMinutes} mins</td>
        <td class="p-3">${statusBadge}</td>
        <td class="p-3 text-slate-400">${b.expiryDate}</td>
      </tr>
    `;
  }).join('');
}

function updateInventoryDropdowns(batches, fridges) {
  const moveBatch = document.getElementById('moveBatchSelect');
  const moveTarget = document.getElementById('moveTargetSelect');
  const resetBatch = document.getElementById('resetBatchSelect');

  if (moveBatch) {
    moveBatch.innerHTML = batches.map(b => `<option value="${b.id}">${b.name} (${b.id}) - in ${b.fridgeId}</option>`).join('');
  }
  if (moveTarget) {
    moveTarget.innerHTML = fridges.map(f => `<option value="${f.id}">${f.name} (${f.id})</option>`).join('');
  }
  if (resetBatch) {
    const discardBatches = batches.filter(b => b.status === 'Discard');
    if (discardBatches.length === 0) {
      resetBatch.innerHTML = '<option disabled>No discarded batches at 0%</option>';
    } else {
      resetBatch.innerHTML = discardBatches.map(b => `<option value="${b.id}">${b.name} (${b.id})</option>`).join('');
    }
  }
}

async function executeBatchMove() {
  const batchId = document.getElementById('moveBatchSelect').value;
  const targetFridgeId = document.getElementById('moveTargetSelect').value;

  const res = await fetch(`${API_BASE}/inventory/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ batchId, targetFridgeId })
  });

  if (res.ok) {
    alert('Batch moved successfully!');
    fetchDashboard();
  } else {
    const err = await res.json();
    alert(err.error || 'Failed to move batch');
  }
}

async function executeAdminReset() {
  const batchId = document.getElementById('resetBatchSelect').value;
  if (!batchId) return;

  const res = await fetch(`${API_BASE}/inventory/reset-discard`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ batchId })
  });

  if (res.ok) {
    alert(`Batch ${batchId} reset successfully. Red LED latch cleared.`);
    fetchDashboard();
  } else {
    const err = await res.json();
    alert(err.error || 'Only Admin role can perform discard overrides');
  }
}

async function fetchAuditLogs() {
  if (!authToken) return;
  const res = await fetch(`${API_BASE}/logs/audit`, {
    headers: { 'Authorization': `Bearer ${authToken}` }
  });
  const logs = await res.json();
  const tbody = document.getElementById('auditTableBody');
  tbody.innerHTML = logs.map(l => `
    <tr class="hover:bg-slate-800/40">
      <td class="p-3 text-slate-500">${l.index}</td>
      <td class="p-3 text-emerald-400 font-bold">${l.action}</td>
      <td class="p-3 text-slate-300">${l.details}</td>
      <td class="p-3 text-slate-400">${l.actor}</td>
      <td class="p-3 text-slate-500">${new Date(l.timestamp).toLocaleTimeString()}</td>
      <td class="p-3 text-slate-400 truncate max-w-xs font-mono" title="${l.hash}">${l.hash.slice(0, 16)}...</td>
    </tr>
  `).join('');
}

async function verifyChainIntegrity() {
  if (!authToken) return;
  const res = await fetch(`${API_BASE}/logs/verify-integrity`, {
    headers: { 'Authorization': `Bearer ${authToken}` }
  });
  const data = await res.json();
  const banner = document.getElementById('integrityResultBanner');
  banner.classList.remove('hidden');

  if (data.valid) {
    banner.className = 'p-4 rounded-xl text-xs font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-300';
    banner.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 mr-2"></i> All ${data.totalRecords} records verified! Hash chain is intact. No tampering detected.`;
  } else {
    banner.className = 'p-4 rounded-xl text-xs font-mono bg-red-500/10 border border-red-500/30 text-red-300';
    banner.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-red-400 mr-2"></i> Tampering Detected! ${data.reason}`;
  }
}

async function fetchAiRecommendations() {
  if (!authToken) return;
  const res = await fetch(`${API_BASE}/ai/recommendations`, {
    headers: { 'Authorization': `Bearer ${authToken}` }
  });
  const data = await res.json();

  // Forecast list
  const forecastList = document.getElementById('aiForecastList');
  forecastList.innerHTML = data.predictions.map(f => `
    <div class="p-3 bg-slate-900/60 rounded-xl flex justify-between items-center">
      <div>
        <span class="font-bold text-white">${f.name}</span>
        <span class="block text-slate-400">Current: ${f.temp}°C</span>
      </div>
      <div class="text-right">
        <span class="text-xs text-slate-400">In 30 Mins:</span>
        <div class="text-sm font-bold ${f.predictedTemp > 8.0 ? 'text-red-400' : 'text-emerald-400'}">
          ${f.predictedTemp}°C ${f.predictedTemp > 8.0 ? '(Breach Risk!)' : '(Safe)'}
        </div>
      </div>
    </div>
  `).join('');

  // Health list
  const healthList = document.getElementById('aiHealthList');
  healthList.innerHTML = data.predictions.map(f => `
    <div class="p-3 bg-slate-900/60 rounded-xl space-y-1">
      <div class="flex justify-between items-center">
        <span class="font-bold text-white">${f.name}</span>
        <span class="font-mono text-purple-400 font-bold">${f.healthScore}/100</span>
      </div>
      <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
        <div class="bg-purple-500 h-1.5 rounded-full" style="width: ${f.healthScore}%"></div>
      </div>
    </div>
  `).join('');

  // Recommendation banner
  const recBanner = document.getElementById('aiRecommendationBanner');
  const hasUnsafeFridge = data.predictions && data.predictions.some(f => (f.predictedTemp || f.temp) > 8.0 || (f.healthScore || 100) < 50);

  if (data.recommendations && data.recommendations.length > 0) {
    recBanner.innerHTML = data.recommendations.map(r => `
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <span class="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
            <i class="fa-solid fa-triangle-exclamation"></i> AI Proactive Relocation Required
          </span>
          <p class="text-xs text-slate-200 mt-1">Move <b>${escapeHtml(r.batchName)}</b> from <i>${escapeHtml(r.sourceFridgeName)}</i> &rarr; <b>${escapeHtml(r.targetFridgeName)}</b></p>
          <span class="text-[11px] text-slate-400">${escapeHtml(r.reason)}</span>
        </div>
        <button onclick="confirmAiRelocation('${escapeHtml(r.batchId)}', '${escapeHtml(r.targetFridgeId)}')" class="text-xs bg-purple-600 hover:bg-purple-500 text-white font-bold px-4 py-2 rounded-xl transition shadow-lg shadow-purple-600/30 whitespace-nowrap">
          1-Click Confirm Relocation
        </button>
      </div>
    `).join('');
  } else if (hasUnsafeFridge) {
    recBanner.innerHTML = `
      <div class="text-xs text-amber-300 flex items-center gap-2">
        <i class="fa-solid fa-triangle-exclamation text-amber-400"></i> Warning: Thermal stress detected on cooler, but no eligible safe destination unit has spare batch capacity!
      </div>
    `;
  } else {
    recBanner.innerHTML = `
      <div class="text-xs text-slate-300 flex items-center gap-2">
        <i class="fa-solid fa-check text-emerald-400"></i> No breach imminent. All fridges operating within safe predictive parameters.
      </div>
    `;
  }
}

async function confirmAiRelocation(batchId, targetFridgeId) {
  const res = await fetch(`${API_BASE}/inventory/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({ batchId, targetFridgeId })
  });
  if (res.ok) {
    alert('Relocation confirmed and logged in tamper-evident chain!');
    fetchDashboard();
    fetchAiRecommendations();
  }
}

async function fetchPublicQr() {
  const batchId = document.getElementById('publicBatchInput').value.trim();
  if (!batchId) return;

  const res = await fetch(`${API_BASE}/public/batch/${batchId}`);
  const data = await res.json();
  const card = document.getElementById('publicResultCard');

  if (res.ok) {
    card.classList.remove('hidden');
    let color = data.status === 'Safe' ? 'text-emerald-400' : (data.status === 'Discard' ? 'text-red-400' : 'text-amber-400');
    card.innerHTML = `
      <div class="flex flex-col sm:flex-row items-center gap-4">
        <img src="${data.qrCode}" class="w-28 h-28 bg-white p-1 rounded-xl shadow-md" alt="Batch QR Code" />
        <div class="space-y-1 text-xs">
          <div class="font-bold text-white text-sm">${data.name}</div>
          <div class="text-slate-400 font-mono">Batch ID: ${data.id}</div>
          <div>Viability Status: <b class="${color} uppercase font-bold">${data.status}</b></div>
          <div class="text-slate-400">Heat Exposure: <b>${data.exposureMinutes} mins</b> / 60 mins</div>
          <div class="text-slate-400">Remaining Budget: <b>${data.remainingBudgetMinutes} mins</b></div>
          <div class="text-slate-400">Expires: <b>${data.expiryDate}</b></div>
        </div>
      </div>
    `;
  } else {
    alert(data.error || 'Batch not found');
  }
}

function setupWebSocket() {
  const ws = new WebSocket('ws://' + window.location.host);
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'TELEMETRY_UPDATE') {
        if (msg.fridges && Array.isArray(msg.fridges)) {
          fridgesData = msg.fridges;
          renderFridges(msg.fridges);
        } else {
          fetchDashboard();
        }
      } else if (msg.type === 'INVENTORY_UPDATE') {
        fetchDashboard();
      }
    } catch (e) {}
  };
}

window.onload = init;

