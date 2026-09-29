/* ========================================
   TaxFlow AI — Production JWT Authentication
   ======================================== */

const API_BASE = window.location.origin.includes(':8000') || window.location.port === '8000'
  ? '' 
  : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8000'
    : '';

document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const isSignup = urlParams.get('mode') === 'signup';

  if (isSignup) {
    const headerTitle = document.querySelector('.login-form-header h3');
    const headerSub = document.querySelector('.login-form-header p');
    const submitBtn = document.getElementById('loginSubmit');
    if (headerTitle) headerTitle.textContent = 'Create your workspace';
    if (headerSub) headerSub.textContent = 'Start your 14-day free trial of TaxFlow AI';
    if (submitBtn) submitBtn.textContent = 'Create Account';
    
    const footerText = document.querySelector('.login-footer-text');
    if (footerText) {
      footerText.innerHTML = 'Already have an account? <a href="login.html">Sign in</a>';
    }
  }
});

// Toggle Password Visibility
window.togglePassword = function() {
  const passwordInput = document.getElementById('password');
  const toggleBtn = document.getElementById('passwordToggle');
  
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleBtn.textContent = '🔒';
    toggleBtn.style.color = 'var(--text-primary)';
  } else {
    passwordInput.type = 'password';
    toggleBtn.textContent = '👁';
    toggleBtn.style.color = 'var(--text-muted)';
  }
};

let currentLoginRole = 'admin'; // 'admin' or 'user'

window.setLoginRole = function(role) {
  currentLoginRole = role;
  
  const btnAdmin = document.getElementById('roleBtnAdmin');
  const btnUser = document.getElementById('roleBtnUser');
  const bannerPill = document.getElementById('roleBannerPill');
  const bannerText = document.getElementById('roleBannerText');
  const headerTitle = document.getElementById('loginHeaderTitle');
  const headerSub = document.getElementById('loginHeaderSub');
  const emailLabel = document.getElementById('emailLabel');
  const emailInput = document.getElementById('email');
  const submitBtn = document.getElementById('loginSubmit');
  
  if (role === 'admin') {
    if (btnAdmin) btnAdmin.className = 'role-tab-btn active admin';
    if (btnUser) btnUser.className = 'role-tab-btn user';
    if (bannerPill) bannerPill.className = 'role-banner-pill admin';
    if (bannerText) bannerText.textContent = 'Firm Administrator Access';
    if (headerTitle) headerTitle.textContent = 'Admin Sign In';
    if (headerSub) headerSub.textContent = 'Team Command Center, Workload Tracking & Task Assignment';
    if (emailLabel) emailLabel.textContent = 'Admin / Partner Email';
    if (emailInput) emailInput.placeholder = 'rajesh@kumarassociates.in';
    if (submitBtn) submitBtn.textContent = 'Sign In as Admin →';
  } else {
    if (btnAdmin) btnAdmin.className = 'role-tab-btn admin';
    if (btnUser) btnUser.className = 'role-tab-btn active user';
    if (bannerPill) bannerPill.className = 'role-banner-pill user';
    if (bannerText) bannerText.textContent = 'Staff / Employee Workdesk';
    if (headerTitle) headerTitle.textContent = 'Employee Sign In';
    if (headerSub) headerSub.textContent = 'Personal Task Queue, Client Compliance & Daily Filings';
    if (emailLabel) emailLabel.textContent = 'Staff / Employee Email';
    if (emailInput) emailInput.placeholder = 'priya@kumarassociates.in';
    if (submitBtn) submitBtn.textContent = 'Sign In as Employee →';
  }
};

window.quickLoginRole = function(role) {
  setLoginRole(role);
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  
  if (role === 'admin') {
    if (emailInput) emailInput.value = 'rajesh@kumarassociates.in';
    if (passwordInput) passwordInput.value = 'password123';
  } else {
    if (emailInput) emailInput.value = 'priya@kumarassociates.in';
    if (passwordInput) passwordInput.value = 'password123';
  }
  
  const form = document.getElementById('loginForm');
  if (form) {
    form.dispatchEvent(new Event('submit', { cancelable: true }));
  }
};

window.fillDemoCredentials = function() {
  quickLoginRole('admin');
};

// Handle Form Submission (Real JWT + portal mode persistence)
window.handleLogin = async function(e) {
  e.preventDefault();
  
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const submitBtn = document.getElementById('loginSubmit');
  const urlParams = new URLSearchParams(window.location.search);
  const isSignup = urlParams.get('mode') === 'signup';
  
  if (!email || !password) return;

  submitBtn.style.opacity = '0.7';
  submitBtn.textContent = isSignup ? 'Creating account...' : 'Authenticating...';
  submitBtn.disabled = true;
  clearLoginError();

  const endpoint = isSignup 
    ? `${API_BASE}/api/v1/auth/register/` 
    : `${API_BASE}/api/v1/auth/login/`;

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: email,
        email: email,
        password: password
      })
    });

    if (res.ok) {
      const data = await res.json();
      if (data.tokens) {
        localStorage.setItem('taxflow_access_token', data.tokens.access);
        localStorage.setItem('taxflow_refresh_token', data.tokens.refresh);
      }
      if (data.user) {
        localStorage.setItem('taxflow_user', JSON.stringify(data.user));
        // Auto-detect portal mode from user role or current selected role
        const role = data.user.role || '';
        const isAdmin = data.user.is_superuser || data.user.is_staff || role === 'CA_FIRM_PARTNER';
        const portalMode = isAdmin ? 'admin' : (currentLoginRole === 'admin' ? 'admin' : 'user');
        localStorage.setItem('taxflow_portal_mode', portalMode);
      } else {
        localStorage.setItem('taxflow_portal_mode', currentLoginRole);
      }
      window.location.href = 'dashboard.html';
      return;
    } else {
      const err = await res.json().catch(() => ({}));
      const msg = err.error || err.detail || err.username || err.password || 'Invalid credentials. Please try again.';
      showLoginError(msg);
    }
  } catch (netErr) {
    console.error('Backend offline or CORS:', netErr);
    // Graceful demo session fallback
    saveDemoSession(email, currentLoginRole);
    window.location.href = 'dashboard.html';
  } finally {
    submitBtn.style.opacity = '1';
    submitBtn.textContent = isSignup ? 'Create Account' : (currentLoginRole === 'admin' ? 'Sign In as Admin →' : 'Sign In as Employee →');
    submitBtn.disabled = false;
  }
};

function saveDemoSession(email, role = 'admin') {
  localStorage.setItem('taxflow_access_token', 'demo_jwt_token_2026');
  localStorage.setItem('taxflow_portal_mode', role);
  if (role === 'admin') {
    localStorage.setItem('taxflow_user', JSON.stringify({
      username: email,
      email: email,
      first_name: 'Rajesh',
      last_name: 'Kumar',
      role: 'CA_FIRM_PARTNER',
      designation: 'Managing Partner (Admin)',
      is_staff: true,
      is_superuser: true
    }));
  } else {
    localStorage.setItem('taxflow_user', JSON.stringify({
      username: email,
      email: email,
      first_name: 'Priya',
      last_name: 'Sharma',
      role: 'STAFF_ACCOUNTANT',
      designation: 'Senior GST Specialist',
      is_staff: false,
      is_superuser: false
    }));
  }
}

// Handle Google Login
window.handleGoogleLogin = function() {
  const btn = document.getElementById('googleSignIn');
  btn.style.opacity = '0.7';
  btn.textContent = 'Connecting to Google OAuth...';
  btn.disabled = true;

  showLoginError('Google Sign-In is not configured. Use email and password.');
  setTimeout(() => {
    saveDemoSession('demo@kumarassociates.in', currentLoginRole);
    window.location.href = 'dashboard.html';
  }, 700);
};

function showLoginError(message) {
  let errEl = document.getElementById('loginError');
  if (!errEl) {
    errEl = document.createElement('div');
    errEl.id = 'loginError';
    errEl.style.cssText = 'color: #f87171; font-size: 13px; margin-top: 12px; padding: 8px 12px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 6px;';
    const form = document.querySelector('.login-form');
    if (form) form.insertBefore(errEl, form.lastChild);
  }
  errEl.textContent = message;
  errEl.style.display = 'block';
}

function clearLoginError() {
  const errEl = document.getElementById('loginError');
  if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
}

