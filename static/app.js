/* ================================================================
   Game Item Trading – Single-Page Frontend
   ================================================================ */

const API = '';  // same origin

// ── State ──────────────────────────────────────────────────────
let token = localStorage.getItem('token') || null;
let currentUser = null;

// ── Helpers ────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (opts.body && !(opts.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(API + path, { ...opts, headers });
  const data = res.headers.get('content-type')?.includes('json')
    ? await res.json() : null;
  if (!res.ok) {
    const msg = data?.detail || `Error ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function $(sel, parent = document) { return parent.querySelector(sel); }
function $$(sel, parent = document) { return [...parent.querySelectorAll(sel)]; }

function stars(rating, count) {
  const full = Math.round(rating || 0);
  let s = '';
  for (let i = 1; i <= 5; i++) s += i <= full ? '★' : '<span class="empty">★</span>';
  return `<span class="stars">${s}</span> <span class="text-muted text-small">(${count || 0})</span>`;
}

function rarityBadge(r) {
  if (!r) return '';
  return `<span class="rarity-badge rarity-${r}">${r}</span>`;
}

function statusBadge(s) {
  return `<span class="status-badge status-${s}">${s}</span>`;
}

function timeAgo(dt) {
  const d = new Date(dt);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff/60) + 'm ago';
  if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
  return d.toLocaleDateString();
}

// ── Router ─────────────────────────────────────────────────────
const routes = {};
function route(name, fn) { routes[name] = fn; }
async function navigate(name, params = {}) {
  if (name !== 'login' && name !== 'register' && !token) {
    return navigate('login');
  }
  if ((name === 'login' || name === 'register') && token) {
    return navigate('dashboard');
  }
  if (routes[name]) {
    try { await routes[name](params); } catch(e) { toast(e.message, 'error'); }
  }
  // Update sidebar active
  $$('.sidebar nav a').forEach(a => {
    a.classList.toggle('active', a.dataset.page === name);
  });
}

// ── Sidebar ────────────────────────────────────────────────────
function renderSidebar() {
  return `
    <div class="logo"><h2>🎮 GameSwap</h2></div>
    <nav>
      <a href="#" data-page="dashboard">📊 Dashboard</a>
      <a href="#" data-page="items">🔍 Browse Items</a>
      <a href="#" data-page="my-items">🎒 My Items</a>
      <a href="#" data-page="swaps">🔄 Swaps</a>
      <a href="#" data-page="swap-history">📜 Swap History</a>
      <a href="#" data-page="profile">⚙️ Profile</a>
    </nav>
    <div class="user-info">
      <div class="nickname">${currentUser?.nickname || ''}</div>
      <div class="email">${currentUser?.email || ''}</div>
      <button class="btn btn-secondary btn-sm btn-block mt-10" id="logoutBtn">Logout</button>
    </div>`;
}

function renderAppShell(content) {
  document.getElementById('app').innerHTML = `
    <div class="sidebar" id="sidebar">${renderSidebar()}</div>
    <div class="main-content" id="page">${content}</div>`;
  // Sidebar nav
  $$('.sidebar nav a').forEach(a => {
    a.addEventListener('click', e => { e.preventDefault(); navigate(a.dataset.page); });
  });
  $('#logoutBtn').addEventListener('click', () => {
    token = null; currentUser = null;
    localStorage.removeItem('token');
    navigate('login');
  });
}

// ── Auth: Login ────────────────────────────────────────────────
route('login', () => {
  document.getElementById('app').innerHTML = `
    <div class="auth-container">
      <div class="auth-box">
        <h1>🎮 GameSwap</h1>
        <p class="subtitle">Sign in to trade your game items</p>
        <form id="loginForm">
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="loginEmail" required placeholder="you@example.com" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input type="password" id="loginPass" required placeholder="••••••" />
          </div>
          <button class="btn btn-primary btn-block" type="submit">Sign In</button>
        </form>
        <p class="text-center mt-20 text-small">
          Don't have an account? <a href="#" id="goRegister">Create one</a>
        </p>
      </div>
    </div>`;
  $('#goRegister').addEventListener('click', e => { e.preventDefault(); navigate('register'); });
  $('#loginForm').addEventListener('submit', async e => {
    e.preventDefault();
    try {
      const res = await api('/api/auth/login', {
        method: 'POST',
        body: { email: $('#loginEmail').value, password: $('#loginPass').value },
      });
      token = res.access_token;
      localStorage.setItem('token', token);
      currentUser = await api('/api/users/me');
      toast('Welcome back, ' + currentUser.nickname + '!', 'success');
      navigate('dashboard');
    } catch(err) { toast(err.message, 'error'); }
  });
});

// ── Auth: Register ─────────────────────────────────────────────
route('register', () => {
  document.getElementById('app').innerHTML = `
    <div class="auth-container">
      <div class="auth-box" style="max-width:520px">
        <h1>🎮 Create Account</h1>
        <p class="subtitle">Join GameSwap and start trading!</p>
        <form id="regForm">
          <div class="form-group">
            <label>Email *</label>
            <input type="email" id="regEmail" required placeholder="you@example.com" />
          </div>
          <div class="form-group">
            <label>Password *</label>
            <input type="password" id="regPass" required minlength="6" placeholder="Min 6 characters" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>First Name *</label>
              <input id="regFirst" required placeholder="Alice" />
            </div>
            <div class="form-group">
              <label>Last Name *</label>
              <input id="regLast" required placeholder="Smith" />
            </div>
          </div>
          <div class="form-group">
            <label>Nickname (display name) *</label>
            <input id="regNick" required placeholder="AliceGamer" />
          </div>
          <div class="form-group">
            <label>Phone Number</label>
            <input id="regPhone" placeholder="+1-555-1234 (optional)" />
          </div>
          <div class="form-group">
            <label>Postal Code *</label>
            <div class="autocomplete-wrapper">
              <input id="regZip" required placeholder="Start typing ZIP code…" autocomplete="off" />
              <div class="autocomplete-list hidden" id="zipDropdown"></div>
            </div>
            <small class="text-muted" id="zipInfo"></small>
          </div>
          <button class="btn btn-primary btn-block" type="submit">Create Account</button>
        </form>
        <p class="text-center mt-20 text-small">
          Already have an account? <a href="#" id="goLogin">Sign in</a>
        </p>
      </div>
    </div>`;

  $('#goLogin').addEventListener('click', e => { e.preventDefault(); navigate('login'); });

  // Postal code autocomplete
  let zipTimeout;
  const zipInput = $('#regZip');
  const zipDrop = $('#zipDropdown');
  const zipInfoEl = $('#zipInfo');

  zipInput.addEventListener('input', () => {
    clearTimeout(zipTimeout);
    const q = zipInput.value.trim();
    if (q.length < 2) { zipDrop.classList.add('hidden'); return; }
    zipTimeout = setTimeout(async () => {
      try {
        const results = await api(`/api/postal-codes/?search=${encodeURIComponent(q)}&limit=10`);
        if (results.length === 0) {
          zipDrop.classList.add('hidden');
          return;
        }
        zipDrop.innerHTML = results.map(r => `
          <div class="ac-item" data-zip="${r.postal_code}" data-city="${r.city}" data-state="${r.state}">
            <span class="ac-zip">${r.postal_code}</span>
            <span class="ac-loc">${r.city}, ${r.state}</span>
          </div>`).join('');
        zipDrop.classList.remove('hidden');
        $$('.ac-item', zipDrop).forEach(item => {
          item.addEventListener('click', () => {
            zipInput.value = item.dataset.zip;
            zipInfoEl.textContent = `${item.dataset.city}, ${item.dataset.state}`;
            zipDrop.classList.add('hidden');
          });
        });
      } catch(e) { /* ignore */ }
    }, 250);
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.autocomplete-wrapper')) zipDrop.classList.add('hidden');
  });

  $('#regForm').addEventListener('submit', async e => {
    e.preventDefault();
    try {
      const body = {
        email: $('#regEmail').value,
        password: $('#regPass').value,
        first_name: $('#regFirst').value,
        last_name: $('#regLast').value,
        nickname: $('#regNick').value,
        postal_code: $('#regZip').value,
      };
      const phone = $('#regPhone').value.trim();
      if (phone) body.phone_number = phone;

      await api('/api/auth/register', { method: 'POST', body });
      toast('Account created! Please sign in.', 'success');
      navigate('login');
    } catch(err) { toast(err.message, 'error'); }
  });
});

// ── Dashboard ──────────────────────────────────────────────────
route('dashboard', async () => {
  currentUser = await api('/api/users/me');
  const items = await api('/api/items/my?limit=100');
  const swaps = await api('/api/swaps/history?limit=100');

  const pending = swaps.filter(s => s.status === 'pending');
  const completed = swaps.filter(s => s.status === 'completed');

  renderAppShell(`
    <div class="page-header"><h1>Dashboard</h1></div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="value">${items.length}</div>
        <div class="label">My Items</div>
      </div>
      <div class="stat-card">
        <div class="value">${pending.length}</div>
        <div class="label">Pending Swaps</div>
      </div>
      <div class="stat-card">
        <div class="value">${completed.length}</div>
        <div class="label">Completed Swaps</div>
      </div>
      <div class="stat-card">
        <div class="value">${stars(currentUser.average_rating, currentUser.rating_count)}</div>
        <div class="label">Rating</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3>👋 Welcome, ${currentUser.nickname}!</h3></div>
      <p class="text-muted">
        ${currentUser.city ? `📍 ${currentUser.city}, ${currentUser.state}` : ''}
        &nbsp;&middot;&nbsp; Member since ${new Date(currentUser.created_at).toLocaleDateString()}
      </p>
    </div>

    ${pending.length > 0 ? `
    <div class="card">
      <div class="card-header"><h3>⏳ Pending Swaps</h3></div>
      ${pending.slice(0, 5).map(s => `
        <div class="swap-card" style="cursor:pointer" data-swap-id="${s.id}">
          <div class="swap-header">
            <span>${s.proposer_id === currentUser.id ? 'You proposed' : 'Received'}</span>
            ${statusBadge(s.status)}
          </div>
          <div class="text-muted text-small">${timeAgo(s.created_at)}</div>
        </div>`).join('')}
    </div>` : ''}
  `);

  $$('[data-swap-id]').forEach(el => {
    el.addEventListener('click', () => navigate('swap-detail', { id: el.dataset.swapId }));
  });
});

// ── Browse Items ───────────────────────────────────────────────
route('items', async (params) => {
  renderAppShell(`
    <div class="page-header">
      <h1>Browse Items</h1>
    </div>
    <div class="filter-bar">
      <input id="searchInput" placeholder="Search items…" value="${params.search || ''}" />
      <input id="gameFilter" placeholder="Game name" value="${params.game || ''}" />
      <select id="rarityFilter">
        <option value="">All Rarities</option>
        <option value="common">Common</option>
        <option value="uncommon">Uncommon</option>
        <option value="rare">Rare</option>
        <option value="epic">Epic</option>
        <option value="legendary">Legendary</option>
      </select>
      <button class="btn btn-primary" id="searchBtn">Search</button>
    </div>
    <div id="itemsGrid" class="items-grid"></div>
  `);

  async function loadItems() {
    const search = $('#searchInput').value.trim();
    const game = $('#gameFilter').value.trim();
    const rarity = $('#rarityFilter').value;
    let url = '/api/items/?limit=50';
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (game) url += `&game=${encodeURIComponent(game)}`;
    if (rarity) url += `&rarity=${rarity}`;
    const items = await api(url);
    if (items.length === 0) {
      $('#itemsGrid').innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>No items found</p></div>';
      return;
    }
    $('#itemsGrid').innerHTML = items.map(it => `
      <div class="item-card" data-item-id="${it.id}">
        <div class="item-name">${esc(it.name)}</div>
        <div class="item-game">${esc(it.game)} ${rarityBadge(it.rarity)}</div>
        <p class="text-muted text-small mb-10">${esc(it.description || '').slice(0, 80)}</p>
        <div class="item-meta">
          <span>👤 ${esc(it.owner_username || 'Unknown')}</span>
          ${it.estimated_value ? `<span>💰 $${it.estimated_value}</span>` : ''}
        </div>
      </div>`).join('');
    $$('[data-item-id]', $('#itemsGrid')).forEach(el => {
      el.addEventListener('click', () => navigate('item-detail', { id: el.dataset.itemId }));
    });
  }

  $('#searchBtn').addEventListener('click', loadItems);
  $('#searchInput').addEventListener('keyup', e => { if (e.key === 'Enter') loadItems(); });
  await loadItems();
});

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

// ── Item Detail ────────────────────────────────────────────────
route('item-detail', async ({ id }) => {
  const item = await api(`/api/items/${id}`);
  const isOwner = item.owner_id === currentUser?.id;

  renderAppShell(`
    <div class="page-header">
      <h1>${esc(item.name)}</h1>
      <div>${isOwner ? '<button class="btn btn-secondary" id="editItemBtn">Edit</button>' :
        '<button class="btn btn-primary" id="proposeSwapBtn">Propose Swap</button>'}</div>
    </div>
    <div class="card">
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
        <div>
          <p class="text-muted text-small">GAME</p>
          <p>${esc(item.game)}</p>
        </div>
        <div>
          <p class="text-muted text-small">CATEGORY</p>
          <p>${esc(item.category || '—')}</p>
        </div>
        <div>
          <p class="text-muted text-small">RARITY</p>
          <p>${rarityBadge(item.rarity) || '—'}</p>
        </div>
        <div>
          <p class="text-muted text-small">EST. VALUE</p>
          <p>${item.estimated_value ? '$' + item.estimated_value : '—'}</p>
        </div>
        <div>
          <p class="text-muted text-small">OWNER</p>
          <p>👤 ${esc(item.owner_username || 'Unknown')}</p>
        </div>
        <div>
          <p class="text-muted text-small">AVAILABLE</p>
          <p>${item.is_available ? '✅ Yes' : '❌ No'}</p>
        </div>
      </div>
      ${item.description ? `<div class="mt-20"><p class="text-muted text-small">DESCRIPTION</p><p>${esc(item.description)}</p></div>` : ''}
    </div>
  `);

  if (!isOwner && $('#proposeSwapBtn')) {
    $('#proposeSwapBtn').addEventListener('click', () => navigate('propose-swap', { receiverId: item.owner_id, requestedItemId: id }));
  }
  if (isOwner && $('#editItemBtn')) {
    $('#editItemBtn').addEventListener('click', () => navigate('edit-item', { id }));
  }
});

// ── My Items ───────────────────────────────────────────────────
route('my-items', async () => {
  const items = await api('/api/items/my?limit=100');

  renderAppShell(`
    <div class="page-header">
      <h1>My Items</h1>
      <button class="btn btn-primary" id="addItemBtn">+ Add Item</button>
    </div>
    ${items.length === 0 ? '<div class="empty-state"><div class="icon">🎒</div><p>You have no items yet. Add one!</p></div>' :
    `<div class="items-grid">${items.map(it => `
      <div class="item-card" data-item-id="${it.id}">
        <div class="item-name">${esc(it.name)}</div>
        <div class="item-game">${esc(it.game)} ${rarityBadge(it.rarity)}</div>
        <div class="item-meta">
          <span>${it.is_available ? '✅ Available' : '❌ Unavailable'}</span>
          ${it.estimated_value ? `<span>💰 $${it.estimated_value}</span>` : ''}
        </div>
      </div>`).join('')}</div>`}
  `);

  $('#addItemBtn').addEventListener('click', () => navigate('add-item'));
  $$('[data-item-id]').forEach(el => {
    el.addEventListener('click', () => navigate('edit-item', { id: el.dataset.itemId }));
  });
});

// ── Add Item ───────────────────────────────────────────────────
route('add-item', async () => {
  renderAppShell(`
    <div class="page-header"><h1>Add New Item</h1></div>
    <div class="card">
      <form id="addItemForm">
        <div class="form-group">
          <label>Item Name *</label>
          <input id="itemName" required placeholder="Legendary Sword of Fire" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Game *</label>
            <input id="itemGame" required placeholder="World of Warcraft" />
          </div>
          <div class="form-group">
            <label>Category</label>
            <input id="itemCat" placeholder="Weapon, Armor, etc." />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Rarity</label>
            <select id="itemRarity">
              <option value="">Select…</option>
              <option value="common">Common</option>
              <option value="uncommon">Uncommon</option>
              <option value="rare">Rare</option>
              <option value="epic">Epic</option>
              <option value="legendary">Legendary</option>
            </select>
          </div>
          <div class="form-group">
            <label>Estimated Value ($)</label>
            <input id="itemValue" type="number" step="0.01" min="0" placeholder="0.00" />
          </div>
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea id="itemDesc" placeholder="Describe your item…"></textarea>
        </div>
        <div class="form-group">
          <label>Image URL</label>
          <input id="itemImg" placeholder="https://…" />
        </div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-primary" type="submit">Create Item</button>
          <button class="btn btn-secondary" type="button" id="cancelAdd">Cancel</button>
        </div>
      </form>
    </div>
  `);

  $('#cancelAdd').addEventListener('click', () => navigate('my-items'));
  $('#addItemForm').addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      name: $('#itemName').value,
      game: $('#itemGame').value,
    };
    const cat = $('#itemCat').value.trim(); if (cat) body.category = cat;
    const rar = $('#itemRarity').value; if (rar) body.rarity = rar;
    const val = $('#itemValue').value; if (val) body.estimated_value = parseFloat(val);
    const desc = $('#itemDesc').value.trim(); if (desc) body.description = desc;
    const img = $('#itemImg').value.trim(); if (img) body.image_url = img;
    try {
      await api('/api/items/', { method: 'POST', body });
      toast('Item created!', 'success');
      navigate('my-items');
    } catch(err) { toast(err.message, 'error'); }
  });
});

// ── Edit Item ──────────────────────────────────────────────────
route('edit-item', async ({ id }) => {
  const item = await api(`/api/items/${id}`);

  renderAppShell(`
    <div class="page-header"><h1>Edit Item</h1></div>
    <div class="card">
      <form id="editItemForm">
        <div class="form-group">
          <label>Item Name</label>
          <input id="itemName" value="${esc(item.name)}" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Game</label>
            <input id="itemGame" value="${esc(item.game)}" />
          </div>
          <div class="form-group">
            <label>Category</label>
            <input id="itemCat" value="${esc(item.category || '')}" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Rarity</label>
            <select id="itemRarity">
              <option value="">Select…</option>
              <option value="common" ${item.rarity==='common'?'selected':''}>Common</option>
              <option value="uncommon" ${item.rarity==='uncommon'?'selected':''}>Uncommon</option>
              <option value="rare" ${item.rarity==='rare'?'selected':''}>Rare</option>
              <option value="epic" ${item.rarity==='epic'?'selected':''}>Epic</option>
              <option value="legendary" ${item.rarity==='legendary'?'selected':''}>Legendary</option>
            </select>
          </div>
          <div class="form-group">
            <label>Estimated Value ($)</label>
            <input id="itemValue" type="number" step="0.01" min="0" value="${item.estimated_value || ''}" />
          </div>
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea id="itemDesc">${esc(item.description || '')}</textarea>
        </div>
        <div class="form-group">
          <label>Available for trading</label>
          <select id="itemAvail">
            <option value="true" ${item.is_available?'selected':''}>Yes</option>
            <option value="false" ${!item.is_available?'selected':''}>No</option>
          </select>
        </div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-primary" type="submit">Save Changes</button>
          <button class="btn btn-danger" type="button" id="deleteItem">Delete</button>
          <button class="btn btn-secondary" type="button" id="cancelEdit">Cancel</button>
        </div>
      </form>
    </div>
  `);

  $('#cancelEdit').addEventListener('click', () => navigate('my-items'));
  $('#deleteItem').addEventListener('click', async () => {
    if (!confirm('Delete this item permanently?')) return;
    try {
      await api(`/api/items/${id}`, { method: 'DELETE' });
      toast('Item deleted', 'success');
      navigate('my-items');
    } catch(err) { toast(err.message, 'error'); }
  });
  $('#editItemForm').addEventListener('submit', async e => {
    e.preventDefault();
    const body = {};
    body.name = $('#itemName').value;
    body.game = $('#itemGame').value;
    body.category = $('#itemCat').value || null;
    body.rarity = $('#itemRarity').value || null;
    const val = $('#itemValue').value;
    body.estimated_value = val ? parseFloat(val) : null;
    body.description = $('#itemDesc').value || null;
    body.is_available = $('#itemAvail').value === 'true';
    try {
      await api(`/api/items/${id}`, { method: 'PUT', body });
      toast('Item updated!', 'success');
      navigate('my-items');
    } catch(err) { toast(err.message, 'error'); }
  });
});

// ── Propose Swap ───────────────────────────────────────────────
route('propose-swap', async ({ receiverId, requestedItemId }) => {
  const myItems = await api('/api/items/my?limit=100');
  const available = myItems.filter(i => i.is_available);

  // Load receiver items
  const receiverItems = await api(`/api/items/?limit=100`);
  const theirItems = receiverItems.filter(i => i.owner_id === receiverId && i.is_available);

  renderAppShell(`
    <div class="page-header"><h1>Propose a Swap</h1></div>
    <div class="card">
      <form id="swapForm">
        <div class="form-group">
          <label>Your items to offer (select one or more) *</label>
          <div id="myItemsList">
            ${available.length === 0 ? '<p class="text-muted">No available items. Add some items first!</p>' :
              available.map(i => `
              <label style="display:flex;align-items:center;gap:8px;padding:6px 0;cursor:pointer;">
                <input type="checkbox" name="offered" value="${i.id}" />
                <span>${esc(i.name)}</span>
                <span class="text-muted text-small">${esc(i.game)}</span>
                ${rarityBadge(i.rarity)}
              </label>`).join('')}
          </div>
        </div>
        <div class="form-group">
          <label>Items you want (select one or more) *</label>
          <div id="theirItemsList">
            ${theirItems.map(i => `
              <label style="display:flex;align-items:center;gap:8px;padding:6px 0;cursor:pointer;">
                <input type="checkbox" name="requested" value="${i.id}" ${i.id === requestedItemId ? 'checked' : ''} />
                <span>${esc(i.name)}</span>
                <span class="text-muted text-small">${esc(i.game)}</span>
                ${rarityBadge(i.rarity)}
              </label>`).join('')}
          </div>
        </div>
        <div class="form-group">
          <label>Message (optional)</label>
          <textarea id="swapMsg" placeholder="Hi! I'd love to trade…"></textarea>
        </div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-primary" type="submit" ${available.length === 0 ? 'disabled' : ''}>Send Proposal</button>
          <button class="btn btn-secondary" type="button" id="cancelSwap">Cancel</button>
        </div>
      </form>
    </div>
  `);

  $('#cancelSwap').addEventListener('click', () => navigate('items'));
  $('#swapForm').addEventListener('submit', async e => {
    e.preventDefault();
    const offered = $$('input[name="offered"]:checked').map(cb => cb.value);
    const requested = $$('input[name="requested"]:checked').map(cb => cb.value);
    if (offered.length === 0 || requested.length === 0) {
      toast('Select at least one item on each side', 'error');
      return;
    }
    const body = {
      receiver_id: receiverId,
      offered_item_ids: offered,
      requested_item_ids: requested,
    };
    const msg = $('#swapMsg').value.trim();
    if (msg) body.message = msg;
    try {
      await api('/api/swaps/', { method: 'POST', body });
      toast('Swap proposed!', 'success');
      navigate('swaps');
    } catch(err) { toast(err.message, 'error'); }
  });
});

// ── Swaps (pending incoming/outgoing) ──────────────────────────
route('swaps', async () => {
  const swaps = await api('/api/swaps/history?status=pending&limit=50');

  const incoming = swaps.filter(s => s.receiver_id === currentUser.id);
  const outgoing = swaps.filter(s => s.proposer_id === currentUser.id);

  renderAppShell(`
    <div class="page-header"><h1>Pending Swaps</h1></div>

    <h3 class="mb-10">📥 Incoming (${incoming.length})</h3>
    ${incoming.length === 0 ? '<p class="text-muted mb-20 text-small">No incoming swap proposals</p>' :
      incoming.map(s => `
      <div class="swap-card" style="cursor:pointer" data-swap-id="${s.id}">
        <div class="swap-header">
          <span>From user • ${timeAgo(s.created_at)}</span>
          ${statusBadge(s.status)}
        </div>
        ${s.message ? `<p class="text-muted text-small">"${esc(s.message)}"</p>` : ''}
      </div>`).join('')}

    <h3 class="mb-10 mt-20">📤 Outgoing (${outgoing.length})</h3>
    ${outgoing.length === 0 ? '<p class="text-muted mb-20 text-small">No outgoing swap proposals</p>' :
      outgoing.map(s => `
      <div class="swap-card" style="cursor:pointer" data-swap-id="${s.id}">
        <div class="swap-header">
          <span>To user • ${timeAgo(s.created_at)}</span>
          ${statusBadge(s.status)}
        </div>
        ${s.message ? `<p class="text-muted text-small">"${esc(s.message)}"</p>` : ''}
      </div>`).join('')}
  `);

  $$('[data-swap-id]').forEach(el => {
    el.addEventListener('click', () => navigate('swap-detail', { id: el.dataset.swapId }));
  });
});

// ── Swap Detail ────────────────────────────────────────────────
route('swap-detail', async ({ id }) => {
  const swap = await api(`/api/swaps/${id}`);
  const isProposer = swap.proposer_id === currentUser.id;
  const isReceiver = swap.receiver_id === currentUser.id;

  const canAcceptReject = isReceiver && swap.status === 'pending';
  const canCancel = isProposer && swap.status === 'pending';
  const canRate = swap.status === 'completed' && (
    (isProposer && swap.proposer_rating == null) ||
    (isReceiver && swap.receiver_rating == null)
  );

  renderAppShell(`
    <div class="page-header">
      <h1>Swap Details</h1>
      ${statusBadge(swap.status)}
    </div>
    <div class="card">
      <div class="swap-items-row">
        <div class="swap-items-list">
          <div class="label">Offered by ${esc(swap.proposer_username || 'Proposer')}</div>
          ${swap.offered_items.map(i => `<div>• ${esc(i.name)} <span class="text-muted text-small">(${esc(i.game)})</span> ${rarityBadge(i.rarity)}</div>`).join('')}
        </div>
        <div class="arrow">⇄</div>
        <div class="swap-items-list">
          <div class="label">Requested from ${esc(swap.receiver_username || 'Receiver')}</div>
          ${swap.requested_items.map(i => `<div>• ${esc(i.name)} <span class="text-muted text-small">(${esc(i.game)})</span> ${rarityBadge(i.rarity)}</div>`).join('')}
        </div>
      </div>
      ${swap.message ? `<div class="mt-10"><p class="text-muted text-small">MESSAGE</p><p>"${esc(swap.message)}"</p></div>` : ''}
      <div class="mt-10 text-muted text-small">Created ${timeAgo(swap.created_at)}${swap.completed_at ? ' • Completed ' + timeAgo(swap.completed_at) : ''}</div>
    </div>

    ${swap.proposer_rating != null || swap.receiver_rating != null ? `
    <div class="card">
      <h3 class="mb-10">Ratings</h3>
      ${swap.proposer_rating != null ? `<div class="mb-10"><strong>${esc(swap.proposer_username)}</strong> rated: ${stars(swap.proposer_rating, 1)} ${swap.proposer_review ? `<br><span class="text-muted text-small">"${esc(swap.proposer_review)}"</span>` : ''}</div>` : ''}
      ${swap.receiver_rating != null ? `<div><strong>${esc(swap.receiver_username)}</strong> rated: ${stars(swap.receiver_rating, 1)} ${swap.receiver_review ? `<br><span class="text-muted text-small">"${esc(swap.receiver_review)}"</span>` : ''}</div>` : ''}
    </div>` : ''}

    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      ${canAcceptReject ? `
        <button class="btn btn-success" id="acceptBtn">✓ Accept</button>
        <button class="btn btn-danger" id="rejectBtn">✗ Reject</button>
      ` : ''}
      ${canCancel ? `<button class="btn btn-warning" id="cancelBtn">Cancel Proposal</button>` : ''}
      ${canRate ? `<button class="btn btn-primary" id="rateBtn">⭐ Rate this Swap</button>` : ''}
      <button class="btn btn-secondary" id="backBtn">← Back</button>
    </div>

    <div id="rateModal" class="hidden"></div>
  `);

  $('#backBtn').addEventListener('click', () => navigate('swaps'));

  if (canAcceptReject) {
    $('#acceptBtn').addEventListener('click', async () => {
      if (!confirm('Accept this swap? Items will be exchanged.')) return;
      try {
        await api(`/api/swaps/${id}/accept`, { method: 'POST' });
        toast('Swap accepted! Items exchanged.', 'success');
        navigate('swap-detail', { id });
      } catch(err) { toast(err.message, 'error'); }
    });
    $('#rejectBtn').addEventListener('click', async () => {
      if (!confirm('Reject this swap?')) return;
      try {
        await api(`/api/swaps/${id}/reject`, { method: 'POST' });
        toast('Swap rejected', 'info');
        navigate('swap-detail', { id });
      } catch(err) { toast(err.message, 'error'); }
    });
  }
  if (canCancel) {
    $('#cancelBtn').addEventListener('click', async () => {
      if (!confirm('Cancel your swap proposal?')) return;
      try {
        await api(`/api/swaps/${id}/cancel`, { method: 'POST' });
        toast('Swap cancelled', 'info');
        navigate('swap-detail', { id });
      } catch(err) { toast(err.message, 'error'); }
    });
  }
  if (canRate) {
    $('#rateBtn').addEventListener('click', () => {
      const modal = $('#rateModal');
      modal.classList.remove('hidden');
      modal.innerHTML = `
        <div class="modal-overlay">
          <div class="modal">
            <h2>Rate this Swap</h2>
            <div class="form-group">
              <label>Rating (1–5 stars)</label>
              <div id="starPicker" style="font-size:28px;cursor:pointer;">
                ${[1,2,3,4,5].map(i => `<span data-val="${i}" style="color:var(--border)">★</span>`).join('')}
              </div>
              <input type="hidden" id="ratingVal" value="" />
            </div>
            <div class="form-group">
              <label>Review (optional)</label>
              <textarea id="reviewText" placeholder="How was the trade?"></textarea>
            </div>
            <div class="modal-actions">
              <button class="btn btn-secondary" id="cancelRate">Cancel</button>
              <button class="btn btn-primary" id="submitRate">Submit Rating</button>
            </div>
          </div>
        </div>`;

      // Star picker
      $$('#starPicker span').forEach(s => {
        s.addEventListener('click', () => {
          const val = parseInt(s.dataset.val);
          $('#ratingVal').value = val;
          $$('#starPicker span').forEach((ss, idx) => {
            ss.style.color = idx < val ? 'var(--warning)' : 'var(--border)';
          });
        });
        s.addEventListener('mouseenter', () => {
          const val = parseInt(s.dataset.val);
          $$('#starPicker span').forEach((ss, idx) => {
            ss.style.color = idx < val ? 'var(--warning)' : 'var(--border)';
          });
        });
      });

      $('#cancelRate').addEventListener('click', () => modal.classList.add('hidden'));
      $('#submitRate').addEventListener('click', async () => {
        const rating = parseInt($('#ratingVal').value);
        if (!rating || rating < 1 || rating > 5) { toast('Select a rating', 'error'); return; }
        const body = { rating };
        const review = $('#reviewText').value.trim();
        if (review) body.review = review;
        try {
          await api(`/api/swaps/${id}/rate`, { method: 'POST', body });
          toast('Rating submitted!', 'success');
          navigate('swap-detail', { id });
        } catch(err) { toast(err.message, 'error'); }
      });
    });
  }
});

// ── Swap History ───────────────────────────────────────────────
route('swap-history', async () => {
  renderAppShell(`
    <div class="page-header"><h1>Swap History</h1></div>
    <div class="filter-bar">
      <select id="statusFilter">
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
        <option value="rejected">Rejected</option>
        <option value="cancelled">Cancelled</option>
      </select>
      <button class="btn btn-primary" id="filterBtn">Filter</button>
    </div>
    <div id="historyList"></div>
  `);

  async function load() {
    const status = $('#statusFilter').value;
    let url = '/api/swaps/history?limit=50';
    if (status) url += `&status=${status}`;
    const swaps = await api(url);
    if (swaps.length === 0) {
      $('#historyList').innerHTML = '<div class="empty-state"><div class="icon">📜</div><p>No swaps found</p></div>';
      return;
    }
    $('#historyList').innerHTML = swaps.map(s => `
      <div class="swap-card" style="cursor:pointer" data-swap-id="${s.id}">
        <div class="swap-header">
          <span>${s.proposer_id === currentUser.id ? '📤 You proposed' : '📥 You received'}</span>
          ${statusBadge(s.status)}
        </div>
        <div class="text-muted text-small">${timeAgo(s.created_at)} ${s.message ? '• "' + esc(s.message).slice(0,50) + '…"' : ''}</div>
      </div>`).join('');
    $$('[data-swap-id]', $('#historyList')).forEach(el => {
      el.addEventListener('click', () => navigate('swap-detail', { id: el.dataset.swapId }));
    });
  }

  $('#filterBtn').addEventListener('click', load);
  await load();
});

// ── Profile / Settings ─────────────────────────────────────────
route('profile', async () => {
  currentUser = await api('/api/users/me');
  const u = currentUser;

  renderAppShell(`
    <div class="page-header"><h1>Profile Settings</h1></div>
    <div class="card">
      <h3 class="mb-10">Personal Information</h3>
      <form id="profileForm">
        <div class="form-row">
          <div class="form-group">
            <label>First Name</label>
            <input id="pFirst" value="${esc(u.first_name)}" />
          </div>
          <div class="form-group">
            <label>Last Name</label>
            <input id="pLast" value="${esc(u.last_name)}" />
          </div>
        </div>
        <div class="form-group">
          <label>Nickname (display name)</label>
          <input id="pNick" value="${esc(u.nickname)}" />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="pEmail" value="${esc(u.email)}" />
        </div>
        <div class="form-group">
          <label>Phone Number</label>
          <input id="pPhone" value="${esc(u.phone_number || '')}" placeholder="Optional" />
        </div>
        <div class="form-group">
          <label>Postal Code</label>
          <div class="autocomplete-wrapper">
            <input id="pZip" value="${esc(u.postal_code || '')}" autocomplete="off" />
            <div class="autocomplete-list hidden" id="pZipDrop"></div>
          </div>
          <small class="text-muted" id="pZipInfo">${u.city ? u.city + ', ' + u.state : ''}</small>
        </div>
        <div class="form-group">
          <label>Bio</label>
          <textarea id="pBio">${esc(u.bio || '')}</textarea>
        </div>
        <div class="form-group">
          <label>Avatar URL</label>
          <input id="pAvatar" value="${esc(u.avatar_url || '')}" placeholder="https://…" />
        </div>
        <button class="btn btn-primary" type="submit">Save Changes</button>
      </form>
    </div>

    <div class="card mt-20">
      <h3 class="mb-10">Change Password</h3>
      <form id="passwordForm">
        <div class="form-group">
          <label>Current Password</label>
          <input type="password" id="curPass" required />
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input type="password" id="newPass" required minlength="6" />
        </div>
        <button class="btn btn-warning" type="submit">Change Password</button>
      </form>
    </div>
  `);

  // Postal code autocomplete on profile
  let zipTimeout;
  const zipInput = $('#pZip');
  const zipDrop = $('#pZipDrop');
  const zipInfo = $('#pZipInfo');
  zipInput.addEventListener('input', () => {
    clearTimeout(zipTimeout);
    const q = zipInput.value.trim();
    if (q.length < 2) { zipDrop.classList.add('hidden'); return; }
    zipTimeout = setTimeout(async () => {
      try {
        const results = await api(`/api/postal-codes/?search=${encodeURIComponent(q)}&limit=10`);
        if (!results.length) { zipDrop.classList.add('hidden'); return; }
        zipDrop.innerHTML = results.map(r => `
          <div class="ac-item" data-zip="${r.postal_code}" data-city="${r.city}" data-state="${r.state}">
            <span class="ac-zip">${r.postal_code}</span>
            <span class="ac-loc">${r.city}, ${r.state}</span>
          </div>`).join('');
        zipDrop.classList.remove('hidden');
        $$('.ac-item', zipDrop).forEach(item => {
          item.addEventListener('click', () => {
            zipInput.value = item.dataset.zip;
            zipInfo.textContent = `${item.dataset.city}, ${item.dataset.state}`;
            zipDrop.classList.add('hidden');
          });
        });
      } catch(e) {}
    }, 250);
  });

  $('#profileForm').addEventListener('submit', async e => {
    e.preventDefault();
    const body = {};
    body.first_name = $('#pFirst').value;
    body.last_name = $('#pLast').value;
    body.nickname = $('#pNick').value;
    body.email = $('#pEmail').value;
    const phone = $('#pPhone').value.trim();
    body.phone_number = phone || null;
    body.postal_code = $('#pZip').value || null;
    body.bio = $('#pBio').value || null;
    body.avatar_url = $('#pAvatar').value || null;
    try {
      currentUser = await api('/api/users/me', { method: 'PUT', body });
      toast('Profile updated!', 'success');
      navigate('profile');
    } catch(err) { toast(err.message, 'error'); }
  });

  $('#passwordForm').addEventListener('submit', async e => {
    e.preventDefault();
    try {
      await api('/api/users/me/password', {
        method: 'PUT',
        body: { current_password: $('#curPass').value, new_password: $('#newPass').value },
      });
      toast('Password changed!', 'success');
      $('#curPass').value = '';
      $('#newPass').value = '';
    } catch(err) { toast(err.message, 'error'); }
  });
});

// ── Init ───────────────────────────────────────────────────────
(async function init() {
  if (token) {
    try {
      currentUser = await api('/api/users/me');
      navigate('dashboard');
    } catch(e) {
      token = null;
      localStorage.removeItem('token');
      navigate('login');
    }
  } else {
    navigate('login');
  }
})();
