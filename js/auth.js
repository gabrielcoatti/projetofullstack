// Configuração da API
const API_BASE_URL = 'http://localhost:8000/api';

// Utilitários para autenticação
class AuthManager {
  static getToken() {
    return localStorage.getItem('authToken');
  }

  static setToken(token) {
    localStorage.setItem('authToken', token);
  }

  static removeToken() {
    localStorage.removeItem('authToken');
  }

  static getUser() {
    const userData = localStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
  }

  static setUser(user) {
    localStorage.setItem('userData', JSON.stringify(user));
  }

  static removeUser() {
    localStorage.removeItem('userData');
  }

  static isAuthenticated() {
    return !!this.getToken();
  }

  static logout() {
    const hadToken = !!this.getToken();
    this.removeToken();
    this.removeUser();
    // Evitar loop de reload: só redirecionar se não estivermos já na lista OU se token existia e queremos reiniciar.
    if (hadToken && !window.location.pathname.endsWith('lista.html')) {
      window.location.href = 'lista.html';
    } else {
      // Se já estamos em lista.html, apenas mostrar tela de login se existir
      const loginScreen = document.getElementById('loginScreen');
      const mainApp = document.getElementById('mainApp');
      if (loginScreen) loginScreen.style.display = 'flex';
      if (mainApp) mainApp.style.display = 'none';
    }
  }

  static async checkAuthAndRedirect() {
    const token = this.getToken();
    if (!token) {
      // TEMPORÁRIO: Desabilitar redirecionamento automático para testes
      return false;
    }

    // SIMPLIFICADO: Só verificar se o token existe, não fazer requisições extras
    return true;
  }
}

// Utilitários para requisições API
class ApiClient {
  static async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = AuthManager.getToken();

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      // Verificar se a resposta é JSON válida
      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        console.error('Erro ao parsear JSON:', jsonError);
        throw new Error('Resposta inválida do servidor');
      }

      if (!response.ok) {
        // Só fazer logout autom. em 401 se havia token (token inválido)
        if (response.status === 401) {
          if (token) {
            console.warn('401 com token presente -> logout');
            AuthManager.logout();
          } else {
            console.warn('401 sem token: ignorando redirect para evitar loop');
          }
          return { error: 'Não autorizado' };
        }
        throw new Error(data.error || data.message || `Erro ${response.status}: ${response.statusText}`);
      }

      return data;
    } catch (error) {
      // Tratar erros de rede
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Erro de conexão. Verifique se o servidor está rodando.');
      }
      
      // Logout para erros de token
      if (error.message.includes('401') && token) {
        AuthManager.logout();
        return { error: 'Não autorizado' };
      }
      
      throw error;
    }
  }

  static async get(endpoint) {
    return this.request(endpoint);
  }

  static async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  static async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  static async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }
}

// Utilitários de UI
function showToast(message, type = 'info', duration = 3000) {
  // Usar o sistema de componentes se disponível
  if (window.Components && window.Components.Toast) {
    return window.Components.Toast.show(message, type, duration);
  }
  
  // Fallback para sistema simples
  const toastRoot = document.getElementById('toastRoot');
  if (!toastRoot) {
    return;
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  toastRoot.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('fade-out');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}

function showAlert(element, message, type = 'error') {
  if (!element) return;

  const messageEl = element.querySelector('.alert-message');
  if (messageEl) {
    messageEl.textContent = message;
  }

  element.className = `alert ${type}-alert`;
  element.style.display = 'flex';

  setTimeout(() => {
    element.style.display = 'none';
  }, 5000);
}

function setButtonLoading(button, loading = true) {
  if (!button) return;

  const span = button.querySelector('span');
  const spinner = button.querySelector('.loading-spinner');

  if (loading) {
    button.disabled = true;
    if (span) span.style.opacity = '0.7';
    if (spinner) spinner.style.display = 'block';
  } else {
    button.disabled = false;
    if (span) span.style.opacity = '1';
    if (spinner) spinner.style.display = 'none';
  }
}

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function validateUsername(username) {
  const usernameRegex = /^[a-zA-Z0-9_]{3,30}$/;
  return usernameRegex.test(username);
}

function clearError(fieldId) {
  const errorEl = document.getElementById(`${fieldId}Error`);
  const inputEl = document.getElementById(fieldId);
  
  if (errorEl) errorEl.textContent = '';
  if (inputEl) inputEl.classList.remove('error');
}

function showError(fieldId, message) {
  const errorEl = document.getElementById(`${fieldId}Error`);
  const inputEl = document.getElementById(fieldId);
  
  if (errorEl) errorEl.textContent = message;
  if (inputEl) inputEl.classList.add('error');
}

// Página de Login
function initLoginPage() {
  // Redirecionar se já estiver logado
  if (AuthManager.isAuthenticated()) {
    window.location.href = 'index.html';
    return;
  }

  const form = document.getElementById('loginForm');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const loginBtn = document.getElementById('loginBtn');
  const demoBtn = document.getElementById('demoBtn');
  const errorAlert = document.getElementById('errorAlert');

  // Limpar erros quando o usuário digita
  emailInput?.addEventListener('input', () => clearError('email'));
  passwordInput?.addEventListener('input', () => clearError('password'));

  // Submissão do formulário
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Limpar erros anteriores
    clearError('email');
    clearError('password');

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // Validação
    let hasError = false;

    if (!validateEmail(email)) {
      showError('email', 'Email inválido');
      hasError = true;
    }

    if (password.length < 6) {
      showError('password', 'Senha deve ter pelo menos 6 caracteres');
      hasError = true;
    }

    if (hasError) return;

    setButtonLoading(loginBtn, true);

    try {
      const response = await ApiClient.post('/login', { email, password });

      AuthManager.setToken(response.token);
      AuthManager.setUser(response.user);

      showToast('Login realizado com sucesso!', 'success');
      
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 1000);

    } catch (error) {
      console.error('Erro no login:', error);
      showAlert(errorAlert, error.message || 'Erro ao fazer login');
    } finally {
      setButtonLoading(loginBtn, false);
    }
  });

  // Botão demo
  demoBtn?.addEventListener('click', async () => {
    emailInput.value = 'demo@exemplo.com';
    passwordInput.value = 'demo123';

    // Tentar fazer login com dados demo
    // Se não existir, criar automaticamente
    setButtonLoading(demoBtn, true);

    try {
      let response;
      
      try {
        // Tentar login primeiro
        response = await ApiClient.post('/login', {
          email: 'demo@exemplo.com',
          password: 'demo123'
        });
      } catch (loginError) {
        // Se não conseguir login, criar usuário demo
        if (loginError.message.includes('incorretos')) {
          await ApiClient.post('/register', {
            username: 'demo_user',
            email: 'demo@exemplo.com',
            password: 'demo123'
          });

          response = await ApiClient.post('/login', {
            email: 'demo@exemplo.com',
            password: 'demo123'
          });
        } else {
          throw loginError;
        }
      }

      AuthManager.setToken(response.token);
      AuthManager.setUser(response.user);

      showToast('Login demo realizado com sucesso!', 'success');
      
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 1000);

    } catch (error) {
      console.error('Erro no login demo:', error);
      showAlert(errorAlert, error.message || 'Erro ao fazer login demo');
    } finally {
      setButtonLoading(demoBtn, false);
    }
  });
}

// Página de Registro
function initRegisterPage() {
  // Redirecionar se já estiver logado
  if (AuthManager.isAuthenticated()) {
    window.location.href = 'index.html';
    return;
  }

  const form = document.getElementById('registerForm');
  const usernameInput = document.getElementById('username');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirmPassword');
  const registerBtn = document.getElementById('registerBtn');
  const errorAlert = document.getElementById('errorAlert');

  // Limpar erros quando o usuário digita
  usernameInput?.addEventListener('input', () => clearError('username'));
  emailInput?.addEventListener('input', () => clearError('email'));
  passwordInput?.addEventListener('input', () => clearError('password'));
  confirmPasswordInput?.addEventListener('input', () => clearError('confirmPassword'));

  // Submissão do formulário
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Limpar erros anteriores
    clearError('username');
    clearError('email');
    clearError('password');
    clearError('confirmPassword');

    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    // Validação
    let hasError = false;

    if (!validateUsername(username)) {
      showError('username', 'Username deve ter 3-30 caracteres (letras, números e _)');
      hasError = true;
    }

    if (!validateEmail(email)) {
      showError('email', 'Email inválido');
      hasError = true;
    }

    if (password.length < 6) {
      showError('password', 'Senha deve ter pelo menos 6 caracteres');
      hasError = true;
    }

    if (password !== confirmPassword) {
      showError('confirmPassword', 'Senhas não coincidem');
      hasError = true;
    }

    if (hasError) return;

    setButtonLoading(registerBtn, true);

    try {
      const response = await ApiClient.post('/register', {
        username,
        email,
        password
      });

      showToast('Conta criada com sucesso! Fazendo login...', 'success');

      // Fazer login automaticamente
      const loginResponse = await ApiClient.post('/login', { email, password });

      AuthManager.setToken(loginResponse.token);
      AuthManager.setUser(loginResponse.user);

      setTimeout(() => {
        window.location.href = 'index.html';
      }, 1500);

    } catch (error) {
      console.error('Erro no registro:', error);
      showAlert(errorAlert, error.message || 'Erro ao criar conta');
    } finally {
      setButtonLoading(registerBtn, false);
    }
  });
}

// Verificar autenticação na página principal
async function initMainPage() {
  const isAuth = await AuthManager.checkAuthAndRedirect();
  if (!isAuth) return false;

  const user = AuthManager.getUser();
  if (user) {
    // Atualizar UI com dados do usuário
    const userElements = document.querySelectorAll('.user-name');
    userElements.forEach(el => el.textContent = user.username);
    
    // Atualizar subtítulo com nome do usuário
    const subElement = document.querySelector('.sub');
    if (subElement) {
      subElement.textContent = `Bem-vindo, ${user.username}! — mínimo 5 caracteres`;
    }
  }

  return true;
}