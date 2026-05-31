/* =============================================
   Diet Plan Generator - Frontend Application
   ============================================= */

// API base: usa caminho relativo pois o frontend é servido pelo próprio FastAPI
const API_BASE = '';

// ─── State ────────────────────────────────────
const state = {
    currentUser: null,       // { id, nome_completo, cpf, email, ... }
    currentPage: 'login',
    dietResult: null,        // DietGenerateResponse
};

// ─── DOM Cache ────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {};
let cepTimeout = null;

function cacheDom() {

    // Pages
    dom.pageLogin = $('#page-login');
    dom.pageRegister = $('#page-register');
    dom.pageForgotPassword = $('#page-forgot-password');
    dom.pageResetPassword = $('#page-reset-password');
    dom.pageDiet = $('#page-diet');
    dom.pageResults = $('#page-results');

    // Login form
    dom.loginForm = $('#login-form');
    dom.loginEmail = $('#login-email');
    dom.loginSenha = $('#login-senha');
    dom.loginError = $('#login-error');
    dom.loginBtn = $('#login-btn');

    // Register form
    dom.registerForm = $('#register-form');
    dom.regNome = $('#reg-nome');
    dom.regCpf = $('#reg-cpf');
    dom.regTelefone = $('#reg-telefone');
    dom.regEmail = $('#reg-email');
    dom.regCep = $('#reg-cep');
    dom.regLogradouro = $('#reg-logradouro');
    dom.regBairro = $('#reg-bairro');
    dom.regCidade = $('#reg-cidade');
    dom.regEstado = $('#reg-estado');
    dom.regSenha = $('#reg-senha');
    dom.regSenhaConfirm = $('#reg-senha-confirm');
    dom.regError = $('#reg-error');
    dom.regSuccess = $('#reg-success');
    dom.regBtn = $('#reg-btn');
    dom.regCepSpinner = $('#reg-cep-spinner');

    // Forgot password form
    dom.forgotForm = $('#forgot-form');
    dom.forgotEmail = $('#forgot-email');
    dom.forgotError = $('#forgot-error');
    dom.forgotSuccess = $('#forgot-success');
    dom.forgotBtn = $('#forgot-btn');

    // Reset password form
    dom.resetForm = $('#reset-form');
    dom.resetToken = $('#reset-token');
    dom.resetSenha = $('#reset-senha');
    dom.resetSenhaConfirm = $('#reset-senha-confirm');
    dom.resetError = $('#reset-error');
    dom.resetSuccess = $('#reset-success');
    dom.resetBtn = $('#reset-btn');

    // Strength bars
    dom.strengthBars = $$('.strength-bar');
    dom.pwdReqs = $$('.password-requirements li');

    // Diet form (SPEC-009: textarea-based)
    dom.dietTextarea = $('#diet-texto');
    dom.dietBtn = $('#diet-btn');
    dom.dietError = $('#diet-error');
    dom.dietRetryBtn = $('#diet-retry-btn');
    dom.dietCharCounter = $('#diet-char-counter');
    dom.exampleText = $('#diet-example-text');
    dom.exampleBtn = $('#diet-example-btn');
    dom.exampleDots = $('#diet-example-dots');

    // Routine fields
    dom.routineNome = $$('.routine-nome');
    dom.routineAtividade = $$('.routine-atividade');
    dom.routineObjetivo = $$('.routine-objetivo');
    dom.routineAlimentos = $$('.routine-alimentos');

    // Header
    dom.headerUser = $('#header-user');
    dom.headerUserName = $('#header-user-name');
    dom.btnLogout = $('#btn-logout');

    // Loading overlay
    dom.loadingOverlay = $('#loading-overlay');
    dom.loadingText = $('#loading-text');

    // Results
    dom.pageResults = $('#page-results');
    dom.resultsContent = $('#results-content');
    dom.btnNewDiet = $('#btn-new-diet');
}

// ─── Navigation ───────────────────────────────
function showPage(pageName) {
    // Hide all pages
    ['login', 'register', 'forgot-password', 'reset-password', 'diet', 'results'].forEach(p => {
        const key = 'page' + p.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
        const el = dom[key];
        if (el) el.classList.add('hidden');
    });

    const pageMap = {
        login: dom.pageLogin,
        register: dom.pageRegister,
        'forgot-password': dom.pageForgotPassword,
        'reset-password': dom.pageResetPassword,
        diet: dom.pageDiet,
        results: dom.pageResults,
    };

    const target = pageMap[pageName];
    if (target) {
        target.classList.remove('hidden');
        target.classList.add('page-active');
    }

    state.currentPage = pageName;

    // Start/stop example rotation on diet page
    if (pageName === 'diet') {
        startExampleRotation();
    } else {
        stopExampleRotation();
    }

    // Update header visibility
    updateHeader();
}

function updateHeader() {
    if (state.currentUser) {
        dom.headerUser.classList.remove('hidden');
        dom.headerUserName.textContent = state.currentUser.nome_completo.split(' ')[0];
    } else {
        dom.headerUser.classList.add('hidden');
    }
}

// ─── Loading ──────────────────────────────────
function showLoading(text = 'Processando...') {
    dom.loadingText.textContent = text;
    dom.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    dom.loadingOverlay.classList.add('hidden');
}

// ─── API Helper ───────────────────────────────
async function apiRequest(method, path, body = null) {
    const url = `${API_BASE}${path}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    // Tentar parsear JSON; se falhar (ex: resposta HTML/binária), trata como erro genérico
    let data;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        try {
            data = await response.json();
        } catch (_parseError) {
            throw new Error(`Resposta inválida do servidor (status ${response.status})`);
        }
    } else {
        // Resposta não-JSON (ex: erro 500 em HTML, binário inesperado)
        const text = await response.text().catch(() => '');
        throw new Error(
            text
                ? `Erro do servidor (${response.status}): ${text.substring(0, 200)}`
                : `Erro do servidor (status ${response.status})`
        );
    }

    if (!response.ok) {
        const detail = data.detail || data.message || 'Erro desconhecido';
        // Pydantic validation errors come as array
        if (Array.isArray(detail)) {
            const msgs = detail.map(e => e.msg || e.message).join('; ');
            throw new Error(msgs);
        }
        throw new Error(detail);
    }

    return data;
}

// ─── Auth: Login ──────────────────────────────
function showLoginError(msg) {
    dom.loginError.querySelector('.alert-text').textContent = msg;
    dom.loginError.classList.remove('hidden');
}

// ─── Auth: Register ────────────────────────────
function showRegError(msg) {
    dom.regError.querySelector('.alert-text').textContent = msg;
    dom.regError.classList.remove('hidden');
}

// ─── Password Strength ────────────────────────
function updatePasswordStrength(pwd) {
    const reqs = {
        length: pwd.length >= 8,
        upper: /[A-Z]/.test(pwd),
        number: /[0-9]/.test(pwd),
        special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(pwd),
    };

    const items = ['req-length', 'req-upper', 'req-number', 'req-special'];
    items.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        const key = id.replace('req-', '');
        if (reqs[key]) {
            el.classList.add('met');
        } else {
            el.classList.remove('met');
        }
    });

    const metCount = Object.values(reqs).filter(Boolean).length;
    const bars = dom.strengthBars;

    bars.forEach((bar, i) => {
        bar.className = 'strength-bar';
        if (i < metCount) {
            if (metCount <= 2) bar.classList.add('weak');
            else if (metCount === 3) bar.classList.add('medium');
            else bar.classList.add('strong');
        }
    });
}

// ─── Field Error Helpers ──────────────────────
function showFieldError(input, msg) {
    input.classList.add('error');
    const parent = input.closest('.form-group');
    if (parent) {
        const errorEl = parent.querySelector('.form-error');
        if (errorEl) errorEl.textContent = msg;
    }
}

function clearFieldError(input) {
    input.classList.remove('error');
    const parent = input.closest('.form-group');
    if (parent) {
        const errorEl = parent.querySelector('.form-error');
        if (errorEl) errorEl.textContent = '';
    }
}

// ─── ViaCEP Address Lookup ────────────────────
async function fetchAddress(cep) {
    dom.regCepSpinner.classList.add('active');
    dom.regCep.classList.add('success');

    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();

        if (data.erro) {
            dom.regCep.classList.remove('success');
            dom.regCep.classList.add('error');
            dom.regLogradouro.value = '';
            dom.regBairro.value = '';
            dom.regCidade.value = '';
            dom.regEstado.value = '';
            showFieldError(dom.regCep, 'CEP não encontrado');
            return;
        }

        dom.regLogradouro.value = data.logradouro || '';
        dom.regBairro.value = data.bairro || '';
        dom.regCidade.value = data.localidade || '';
        dom.regEstado.value = data.uf || '';
        dom.regCep.classList.remove('error');
        dom.regCep.classList.add('success');
        clearFieldError(dom.regCep);
    } catch (err) {
        dom.regCep.classList.remove('success');
        showFieldError(dom.regCep, 'Erro ao buscar CEP');
    } finally {
        dom.regCepSpinner.classList.remove('active');
    }
}

// ─── Diet Generation ──────────────────────────

// Add routine dynamically (3rd routine with different defaults)
function initializeRoutines() {
    // Set default values for the 3 routines
    const defaultRoutines = [
        { nome: 'Low Carb', atividade: 'sedentario', objetivo: 'perda_de_peso', alimentos: 'frango, ovos, brócolis, espinafre, abacate' },
        { nome: 'Balanceada', atividade: 'moderado', objetivo: 'manutencao', alimentos: 'arroz integral, frango, feijão, salada, banana' },
        { nome: 'High Protein', atividade: 'ativo', objetivo: 'ganho_de_massa', alimentos: 'frango, batata doce, ovos, aveia, whey protein' },
    ];

    dom.routineNome.forEach((input, i) => {
        if (defaultRoutines[i]) {
            input.value = defaultRoutines[i].nome;
        }
    });

    dom.routineAtividade.forEach((select, i) => {
        if (defaultRoutines[i]) {
            select.value = defaultRoutines[i].atividade;
        }
    });

    dom.routineObjetivo.forEach((select, i) => {
        if (defaultRoutines[i]) {
            select.value = defaultRoutines[i].objetivo;
        }
    });

    dom.routineAlimentos.forEach((input, i) => {
        if (defaultRoutines[i]) {
            input.value = defaultRoutines[i].alimentos;
        }
    });
}

function showDietError(msg) {
    dom.dietError.querySelector('.alert-text').textContent = msg;
    dom.dietError.classList.remove('hidden');
    // Show retry button only for 5xx/server errors
    const isServerError = /502|503|504|500|Erro interno|indisponível|tempo limite/i.test(msg);
    if (dom.dietRetryBtn) {
        dom.dietRetryBtn.classList.toggle('hidden', !isServerError);
    }
}

// ─── Results Rendering (SPEC-010) ──────────────
function renderResults(result) {
    dom.resultsContent.innerHTML = '';

    // ═══ Summary Section ═══
    const p = result.paciente;
    const summary = document.createElement('div');
    summary.className = 'result-summary';
    summary.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${result.tmb.toFixed(0)}</div>
            <div class="stat-label">TMB (kcal/dia)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${result.get_calorico.toFixed(0)}</div>
            <div class="stat-label">GET (kcal/dia)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${_getObjetivoLabel(result.objetivo)}</div>
            <div class="stat-label">Objetivo</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${(p.peso_kg || 0).toFixed(1)} kg</div>
            <div class="stat-label">Peso</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${(p.altura_cm || 0).toFixed(0)} cm</div>
            <div class="stat-label">Altura</div>
        </div>
    `;
    dom.resultsContent.appendChild(summary);

    // ═══ Plans Grid ═══
    const plansGrid = document.createElement('div');
    plansGrid.className = 'plans-grid';

    result.planos.forEach((plano, idx) => {
        const card = _buildPlanCard(plano, idx);
        plansGrid.appendChild(card);
    });

    dom.resultsContent.appendChild(plansGrid);

    // ═══ Accordion (mobile) ═══
    const accordion = document.createElement('div');
    accordion.className = 'plans-accordion';

    const tabNames = ['Tradicional', 'Funcional', 'Prático'];
    const tabIcons = ['🍛', '🥗', '⏱️'];

    // Tabs
    const tabs = document.createElement('div');
    tabs.className = 'accordion-tabs';
    tabNames.forEach((name, i) => {
        const tab = document.createElement('button');
        tab.className = 'accordion-tab' + (i === 0 ? ' active' : '');
        tab.textContent = `${tabIcons[i]} ${name}`;
        tab.dataset.tab = i;
        tab.addEventListener('click', () => _switchAccordionTab(i));
        tabs.appendChild(tab);
    });
    accordion.appendChild(tabs);

    // Panels
    result.planos.forEach((plano, idx) => {
        const panel = document.createElement('div');
        panel.className = 'accordion-panel' + (idx === 0 ? ' active' : '');
        panel.dataset.panel = idx;
        const card = _buildPlanCard(plano, idx, true);
        panel.appendChild(card);
        accordion.appendChild(panel);
    });

    dom.resultsContent.appendChild(accordion);

    // ═══ Avisos (SPEC-008) ═══
    if (result.avisos && result.avisos.length > 0) {
        const avisosSection = document.createElement('div');
        avisosSection.className = 'avisos-section';
        avisosSection.innerHTML = `
            <h3 class="avisos-title">⚠️ Avisos Importantes</h3>
            <ul class="avisos-list">
                ${result.avisos.map(a => `<li>${a}</li>`).join('')}
            </ul>
        `;
        dom.resultsContent.appendChild(avisosSection);
    }

    // ═══ Global Actions ═══
    const actions = document.createElement('div');
    actions.className = 'results-actions';
    actions.innerHTML = `
        <button class="btn btn-secondary" onclick="document.getElementById('btn-new-diet').click()">
            🔄 Gerar Novamente
        </button>
    `;
    if (result.pdf_url) {
        actions.innerHTML += `
            <a href="${API_BASE}${result.pdf_url}" target="_blank" class="btn btn-success">
                📄 Baixar PDF Completo
            </a>
        `;
    }
    dom.resultsContent.appendChild(actions);

    // ═══ Disclaimer (RN-070) ═══
    const disclaimer = document.createElement('p');
    disclaimer.className = 'results-disclaimer';
    disclaimer.textContent = '⚠️ Este plano alimentar é gerado por inteligência artificial e tem caráter informativo. Não substitui consulta com nutricionista ou médico.';
    dom.resultsContent.appendChild(disclaimer);

    hideLoading();
}

function _buildPlanCard(plano, idx, isAccordion = false) {
    const card = document.createElement('div');
    card.className = 'plan-card-v2';

    // Compute totals
    let totalProt = 0, totalCarbo = 0, totalGord = 0, totalKcal = 0;
    plano.refeicoes.forEach(ref => {
        ref.alimentos.forEach(a => {
            totalProt += a.proteina_g || 0;
            totalCarbo += a.carboidrato_g || 0;
            totalGord += a.gordura_g || 0;
            totalKcal += a.calorias_kcal || 0;
        });
    });

    const eixoLabels = {
        tradicional: 'Tradicional Brasileiro',
        funcional: 'Funcional & Nutrientes',
        pratico: 'Prático & Rápido',
    };
    const eixoIcons = {
        tradicional: '🍛',
        funcional: '🥗',
        pratico: '⏱️',
    };

    card.innerHTML = `
        <div class="plan-v2-header">
            <span class="plan-v2-badge">${eixoIcons[plano.eixo] || '📋'} ${eixoLabels[plano.eixo] || plano.eixo}</span>
            <h3 class="plan-v2-name">${plano.nome}</h3>
            <p class="plan-v2-desc">${plano.descricao || ''}</p>
        </div>

        <div class="plan-v2-macros">
            <div class="macro-card">
                <div class="macro-card-value">${totalProt.toFixed(0)}g</div>
                <div class="macro-card-label">Proteína</div>
            </div>
            <div class="macro-card">
                <div class="macro-card-value">${totalCarbo.toFixed(0)}g</div>
                <div class="macro-card-label">Carboidrato</div>
            </div>
            <div class="macro-card">
                <div class="macro-card-value">${totalGord.toFixed(0)}g</div>
                <div class="macro-card-label">Gordura</div>
            </div>
            <div class="macro-card macro-card-kcal">
                <div class="macro-card-value">${totalKcal.toFixed(0)}</div>
                <div class="macro-card-label">kcal totais</div>
            </div>
        </div>

        <div class="plan-v2-meals">
            ${plano.refeicoes.map(ref => `
                <div class="meal-v2">
                    <div class="meal-v2-title">
                        ${ref.nome}
                        ${ref.horario ? `<span class="meal-v2-time">${ref.horario}</span>` : ''}
                    </div>
                    <table class="meal-v2-table">
                        <thead>
                            <tr>
                                <th>Alimento</th>
                                <th>g</th>
                                <th>P</th>
                                <th>C</th>
                                <th>G</th>
                                <th>kcal</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${ref.alimentos.map(a => `
                                <tr>
                                    <td>${a.nome}</td>
                                    <td>${(a.quantidade_g || 0).toFixed(0)}</td>
                                    <td>${(a.proteina_g || 0).toFixed(1)}</td>
                                    <td>${(a.carboidrato_g || 0).toFixed(1)}</td>
                                    <td>${(a.gordura_g || 0).toFixed(1)}</td>
                                    <td>${(a.calorias_kcal || 0).toFixed(0)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `).join('')}
        </div>

        <div class="plan-v2-actions">
            <button class="btn btn-sm btn-outline" onclick="_copyPlanToClipboard(this)" data-plan-idx="${idx}">
                📋 Copiar
            </button>
            <div class="plan-v2-feedback">
                <button class="feedback-btn" title="Gostei!">👍</button>
                <button class="feedback-btn" title="Não gostei">👎</button>
            </div>
        </div>
    `;

    return card;
}

function _switchAccordionTab(index) {
    document.querySelectorAll('.accordion-tab').forEach((t, i) => {
        t.classList.toggle('active', i === index);
    });
    document.querySelectorAll('.accordion-panel').forEach((p, i) => {
        p.classList.toggle('active', i === index);
    });
}

function _getObjetivoLabel(obj) {
    const map = {
        'perda_de_peso': '📉 Perda',
        'manutencao': '⚖️ Manutenção',
        'ganho_de_massa': '💪 Ganho',
    };
    return map[obj] || obj || '—';
}

// ─── Alert helper ─────────────────────────────
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1000; max-width: 400px; box-shadow: var(--shadow-lg); animation: fadeIn 0.3s ease;';
    const icons = { success: '✅', error: '❌', warning: '⚠️' };
    alertDiv.innerHTML = `
        <span class="alert-icon">${icons[type] || 'ℹ️'}</span>
        <span class="alert-text">${message}</span>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transition = 'opacity 0.3s ease';
        setTimeout(() => alertDiv.remove(), 300);
    }, 4000);
}

// ─── Logout ───────────────────────────────────
function logout() {
    state.currentUser = null;
    state.dietResult = null;
    showPage('login');
    dom.loginForm.reset();
    dom.loginError.classList.add('hidden');
    showAlert('success', 'Logout realizado com sucesso!');
}

// ─── CPF formatting helper ────────────────────
function formatCPF(val) {
    val = val.replace(/\D/g, '');
    if (val.length > 11) val = val.slice(0, 11);
    if (val.length > 9) {
        val = val.slice(0, 3) + '.' + val.slice(3, 6) + '.' + val.slice(6, 9) + '-' + val.slice(9);
    } else if (val.length > 6) {
        val = val.slice(0, 3) + '.' + val.slice(3, 6) + '.' + val.slice(6);
    } else if (val.length > 3) {
        val = val.slice(0, 3) + '.' + val.slice(3);
    }
    return val;
}

// ─── Telefone formatting helper ───────────────
function formatTelefone(val) {
    val = val.replace(/\D/g, '');
    if (val.length > 11) val = val.slice(0, 11);
    if (val.length > 7) {
        val = '(' + val.slice(0, 2) + ') ' + val.slice(2, 7) + '-' + val.slice(7);
    } else if (val.length > 2) {
        val = '(' + val.slice(0, 2) + ') ' + val.slice(2);
    } else if (val.length > 0) {
        val = '(' + val;
    }
    return val;
}

// ─── Initialize ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    cacheDom();

    // ── Login Form ──
    dom.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        dom.loginError.classList.add('hidden');

        const email = dom.loginEmail.value.trim();
        const senha = dom.loginSenha.value;

        if (!email || !senha) {
            showLoginError('Preencha todos os campos.');
            return;
        }

        dom.loginBtn.classList.add('loading');

        try {
            const data = await apiRequest('POST', '/api/auth/login', { email, senha });
            state.currentUser = data.usuario;
            showPage('diet');
            dom.loginForm.reset();
            dom.loginError.classList.add('hidden');
            showAlert('success', 'Login realizado com sucesso!');
        } catch (err) {
            showLoginError(err.message);
        } finally {
            dom.loginBtn.classList.remove('loading');
        }
    });

    // ── CPF formatting ──
    dom.regCpf.addEventListener('input', (e) => {
        e.target.value = formatCPF(e.target.value);
    });

    // ── Telefone formatting ──
    dom.regTelefone.addEventListener('input', (e) => {
        e.target.value = formatTelefone(e.target.value);
    });

    // ── CEP auto fetch ──
    dom.regCep.addEventListener('input', (e) => {
        let val = e.target.value.replace(/\D/g, '');
        if (val.length > 8) val = val.slice(0, 8);
        e.target.value = val;

        clearTimeout(cepTimeout);

        if (val.length === 8) {
            cepTimeout = setTimeout(() => fetchAddress(val), 500);
        } else {
            if (val.length === 0) {
                dom.regLogradouro.value = '';
                dom.regBairro.value = '';
                dom.regCidade.value = '';
                dom.regEstado.value = '';
            }
        }
    });

    // ── Password strength ──
    dom.regSenha.addEventListener('input', (e) => {
        updatePasswordStrength(e.target.value);
    });

    // ── Register Form ──
    dom.registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        dom.regError.classList.add('hidden');
        dom.regSuccess.classList.add('hidden');

        const nome = dom.regNome.value.trim();
        const cpf = dom.regCpf.value.replace(/\D/g, '');
        const telefone = dom.regTelefone.value.replace(/\D/g, '');
        const email = dom.regEmail.value.trim();
        const cep = dom.regCep.value.trim();
        const senha = dom.regSenha.value;
        const senhaConfirm = dom.regSenhaConfirm.value;

        if (!nome || !cpf || !telefone || !email || !cep || !senha || !senhaConfirm) {
            showRegError('Preencha todos os campos.');
            return;
        }

        if (cpf.length !== 11) {
            showRegError('CPF deve ter 11 dígitos.');
            return;
        }

        if (senha !== senhaConfirm) {
            showRegError('As senhas não conferem.');
            return;
        }

        if (cep.length !== 8) {
            showRegError('CEP deve ter 8 dígitos.');
            return;
        }

        dom.regBtn.classList.add('loading');

        try {
            const data = await apiRequest('POST', '/api/auth/register', {
                nome_completo: nome,
                cpf,
                telefone,
                email,
                cep,
                senha,
            });

            dom.regSuccess.classList.remove('hidden');
            dom.regSuccess.querySelector('.alert-text').textContent =
                `Cadastro realizado com sucesso! Bem-vindo(a), ${data.nome_completo.split(' ')[0]}!`;

            dom.registerForm.reset();
            dom.strengthBars.forEach(b => b.className = 'strength-bar');
            document.querySelectorAll('.password-requirements li').forEach(el => el.classList.remove('met'));

            setTimeout(() => {
                dom.regSuccess.classList.add('hidden');
                showPage('login');
                dom.loginEmail.value = email;
                dom.loginSenha.value = '';
            }, 2000);
        } catch (err) {
            showRegError(err.message);
        } finally {
            dom.regBtn.classList.remove('loading');
        }
    });

    // ── Forgot Password Form ──
    dom.forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        dom.forgotError.classList.add('hidden');
        dom.forgotSuccess.classList.add('hidden');

        const email = dom.forgotEmail.value.trim();

        if (!email) {
            dom.forgotError.querySelector('.alert-text').textContent = 'Digite seu e-mail.';
            dom.forgotError.classList.remove('hidden');
            return;
        }

        dom.forgotBtn.classList.add('loading');

        try {
            const data = await apiRequest('POST', '/api/auth/forgot-password', { email });

            // Mostrar o token na mensagem de sucesso (desenvolvimento)
            const successMsg = data.token
                ? `Token gerado! Copie o token abaixo para redefinir sua senha:\n\n${data.token}`
                : data.mensagem;

            dom.forgotSuccess.querySelector('.alert-text').textContent = successMsg;
            dom.forgotSuccess.classList.remove('hidden');

            // Se tiver token, limpa o form e mostra link para reset
            if (data.token) {
                dom.forgotEmail.value = '';
                // Remove link antigo se existir para evitar duplicatas
                const oldLink = dom.forgotSuccess.querySelector('.reset-nav-link');
                if (oldLink) oldLink.remove();
                // Adiciona botão para ir para a página de reset
                const resetLink = document.createElement('div');
                resetLink.className = 'reset-nav-link';
                resetLink.style.marginTop = '1rem';
                resetLink.innerHTML = '<a href="#" data-page="reset-password" class="btn btn-secondary btn-block" style="text-decoration:none;display:block;text-align:center;">Ir para Redefinir Senha</a>';
                dom.forgotSuccess.appendChild(resetLink);
            }
        } catch (err) {
            dom.forgotError.querySelector('.alert-text').textContent = err.message;
            dom.forgotError.classList.remove('hidden');
        } finally {
            dom.forgotBtn.classList.remove('loading');
        }
    });

    // ── Reset Password Form ──
    dom.resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        dom.resetError.classList.add('hidden');
        dom.resetSuccess.classList.add('hidden');

        const token = dom.resetToken.value.trim();
        const novaSenha = dom.resetSenha.value;
        const novaSenhaConfirm = dom.resetSenhaConfirm.value;

        if (!token || !novaSenha || !novaSenhaConfirm) {
            dom.resetError.querySelector('.alert-text').textContent = 'Preencha todos os campos.';
            dom.resetError.classList.remove('hidden');
            return;
        }

        if (novaSenha !== novaSenhaConfirm) {
            dom.resetError.querySelector('.alert-text').textContent = 'As senhas não conferem.';
            dom.resetError.classList.remove('hidden');
            return;
        }

        if (novaSenha.length < 8) {
            dom.resetError.querySelector('.alert-text').textContent = 'A senha deve ter no mínimo 8 caracteres.';
            dom.resetError.classList.remove('hidden');
            return;
        }

        dom.resetBtn.classList.add('loading');

        try {
            const data = await apiRequest('POST', '/api/auth/reset-password', {
                token,
                nova_senha: novaSenha,
            });

            dom.resetSuccess.querySelector('.alert-text').textContent = data.mensagem;
            dom.resetSuccess.classList.remove('hidden');
            dom.resetForm.reset();

            // Redirecionar para o login após 2.5s
            setTimeout(() => {
                dom.resetSuccess.classList.add('hidden');
                showPage('login');
                showAlert('success', 'Senha redefinida! Faça login com sua nova senha.');
            }, 2500);
        } catch (err) {
            dom.resetError.querySelector('.alert-text').textContent = err.message;
            dom.resetError.classList.remove('hidden');
        } finally {
            dom.resetBtn.classList.remove('loading');
        }
    });

    // ── Diet Textarea + Examples (SPEC-009) ──

    // Exemplos rotativos
    const DIET_EXAMPLES = [
        {
            text: 'Trabalho sentado o dia todo, faço musculação 4x por semana. Quero ganhar massa. Tenho 1,75m, 72kg e 28 anos. Gosto de frango, batata doce, ovo e banana. Não como peixe.',
            label: 'Atleta — Ganho de Massa',
        },
        {
            text: 'Sou vegetariano, corro 3x por semana, quero perder uns quilinhos. Tenho 1,65m, 78kg, 35 anos. Adoro salada, grão de bico, tofu e frutas.',
            label: 'Vegetariano — Perda de Peso',
        },
        {
            text: 'Cuido da casa e das crianças, não sobra tempo pra academia. Ando bastante a pé. Quero só me alimentar melhor. Tenho 1,60m, 62kg, 42 anos. Gosto de arroz, feijão, carne moída e legumes.',
            label: 'Rotina Caseira — Saúde',
        },
        {
            text: 'Sou estagiário, almoço no bandejão, janto em casa. Faço academia 5x por semana e quero definição. 1,80m, 85kg, 22 anos. Curto frango grelhado, whey, aveia e pasta de amendoim.',
            label: 'Universitário — Definição',
        },
        {
            text: 'Estou grávida de 5 meses, meu médico pediu pra eu me alimentar melhor. Não tenho restrições específicas. 1,68m, 70kg, 31 anos. Gosto de frutas, iogurte, peixe e legumes.',
            label: 'Gestante — Nutrição',
        },
    ];

    let _exampleIndex = 0;
    let _exampleTimer = null;

    function startExampleRotation() {
        _exampleIndex = 0;
        _showExample(0);
        _renderExampleDots();
        _exampleTimer = setInterval(() => {
            _exampleIndex = (_exampleIndex + 1) % DIET_EXAMPLES.length;
            _showExample(_exampleIndex);
        }, 5000);
    }

    function stopExampleRotation() {
        if (_exampleTimer) {
            clearInterval(_exampleTimer);
            _exampleTimer = null;
        }
    }

    function _showExample(index) {
        if (!dom.exampleText || !dom.exampleDots) return;
        dom.exampleText.textContent = DIET_EXAMPLES[index].text;
        const dots = dom.exampleDots.querySelectorAll('.diet-example-dot');
        dots.forEach((d, i) => {
            d.classList.toggle('active', i === index);
        });
    }

    function _renderExampleDots() {
        if (!dom.exampleDots) return;
        dom.exampleDots.innerHTML = DIET_EXAMPLES.map((_, i) =>
            `<span class="diet-example-dot${i === 0 ? ' active' : ''}" data-index="${i}"></span>`
        ).join('');
        dom.exampleDots.querySelectorAll('.diet-example-dot').forEach(dot => {
            dot.addEventListener('click', () => {
                const idx = parseInt(dot.dataset.index);
                _exampleIndex = idx;
                _showExample(idx);
                // Reiniciar timer
                stopExampleRotation();
                _exampleTimer = setInterval(() => {
                    _exampleIndex = (_exampleIndex + 1) % DIET_EXAMPLES.length;
                    _showExample(_exampleIndex);
                }, 5000);
            });
        });
    }

    // Botão "Usar este exemplo"
    if (dom.exampleBtn) {
        dom.exampleBtn.addEventListener('click', () => {
            dom.dietTextarea.value = DIET_EXAMPLES[_exampleIndex].text;
            _updateCharCounter();
        });
    }

    // Contador de caracteres + habilitar/desabilitar botão
    function _updateCharCounter() {
        const len = dom.dietTextarea.value.length;
        dom.dietCharCounter.textContent = `${len}/2000`;
        dom.dietCharCounter.classList.remove('valid', 'invalid');
        if (len >= 20) {
            dom.dietCharCounter.classList.add('valid');
            dom.dietBtn.disabled = false;
        } else {
            dom.dietCharCounter.classList.add('invalid');
            dom.dietBtn.disabled = true;
        }
    }

    if (dom.dietTextarea) {
        dom.dietTextarea.addEventListener('input', _updateCharCounter);
    }

    // Handler do botão Gerar Planos
    if (dom.dietBtn) {
        dom.dietBtn.addEventListener('click', async () => {
            const texto = dom.dietTextarea.value.trim();
            if (texto.length < 20) return;

            dom.dietError.classList.add('hidden');
            dom.dietBtn.classList.add('loading');
            dom.dietRetryBtn.classList.add('hidden');

            // Sanitização leve client-side
            const sanitized = texto
                .replace(/<[^>]*>/g, '')        // remove HTML tags
                .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, '')  // remove control chars
                .replace(/\s+/g, ' ')           // normalize spaces
                .trim();

            // Loading com estágios dinâmicos
            const stages = [
                'Analisando sua descrição...',
                'Calculando seu metabolismo...',
                'Gerando 3 planos com IA...',
                'Montando seu PDF...',
            ];
            let stageIdx = 0;
            showLoading(stages[0]);
            const stageInterval = setInterval(() => {
                stageIdx = Math.min(stageIdx + 1, stages.length - 1);
                dom.loadingText.textContent = stages[stageIdx];
            }, 6000);

            try {
                const result = await apiRequest('POST', '/api/diet/generate', { texto: sanitized });
                clearInterval(stageInterval);
                state.dietResult = result;
                renderResults(result);
                showPage('results');
            } catch (err) {
                clearInterval(stageInterval);
                hideLoading();
                showDietError(err.message);
            } finally {
                dom.dietBtn.classList.remove('loading');
            }
        });
    }

    // Retry button
    if (dom.dietRetryBtn) {
        dom.dietRetryBtn.addEventListener('click', () => {
            dom.dietError.classList.add('hidden');
            dom.dietBtn.click();
        });
    }

    // ── Navigation Links ──
    document.addEventListener('click', (e) => {
        const link = e.target.closest('[data-page]');
        if (link) {
            e.preventDefault();
            const page = link.dataset.page;
            if (page === 'logout') {
                logout();
            } else {
                showPage(page);
            }
        }
    });

    // ── Logout Button ──
    dom.btnLogout.addEventListener('click', logout);

    // ── New Diet Button ──
    dom.btnNewDiet.addEventListener('click', () => {
        showPage('diet');
        dom.dietTextarea.value = '';
        _updateCharCounter();
    });

    // ── Clear field errors on input ──
    document.querySelectorAll('.form-input, .form-select').forEach(el => {
        el.addEventListener('input', () => {
            el.classList.remove('error');
            const parent = el.closest('.form-group');
            if (parent) {
                const errorEl = parent.querySelector('.form-error');
                if (errorEl) errorEl.textContent = '';
            }
        });
    });

    // ── Show login page by default ──
    showPage('login');
});
