/**
 * 美的智能家居控制前端脚本
 */

// DOM 元素
const loginView = document.getElementById('loginView');
const mainView = document.getElementById('mainView');
const loading = document.getElementById('loading');

const accountInput = document.getElementById('account');
const passwordInput = document.getElementById('password');
const loginBtn = document.getElementById('loginBtn');
const loginMessage = document.getElementById('loginMessage');

const userAccount = document.getElementById('userAccount');
const logoutBtn = document.getElementById('logoutBtn');
const homeList = document.getElementById('homeList');
const deviceList = document.getElementById('deviceList');

// 当前选中的家庭 ID
let currentHomeId = null;

// ==================== 工具函数 ====================

function showLoading() {
    loading.style.display = 'flex';
}

function hideLoading() {
    loading.style.display = 'none';
}

function showMessage(element, message, isError = false) {
    element.textContent = message;
    element.className = 'message ' + (isError ? 'error' : 'success');
    element.style.display = 'block';
}

function hideMessage(element) {
    element.style.display = 'none';
}

function showLoginView() {
    loginView.style.display = 'block';
    mainView.style.display = 'none';
}

function showMainView() {
    loginView.style.display = 'none';
    mainView.style.display = 'block';
}

// ==================== API 调用 ====================

async function checkStatus() {
    try {
        const response = await fetch('api/status');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('检查状态失败:', error);
        return { logged_in: false };
    }
}

async function login(account, password) {
    const response = await fetch('api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account, password })
    });
    return await response.json();
}

async function logout() {
    const response = await fetch('api/logout', { method: 'POST' });
    return await response.json();
}

async function getHomes() {
    const response = await fetch('api/homes');
    if (!response.ok) {
        throw new Error('获取家庭列表失败');
    }
    return await response.json();
}

async function getDevices(homeId) {
    const response = await fetch(`api/devices/${homeId}`);
    if (!response.ok) {
        throw new Error('获取设备列表失败');
    }
    return await response.json();
}

// ==================== UI 渲染 ====================

function renderHomes(homes) {
    homeList.innerHTML = '';

    if (!homes || homes.length === 0) {
        homeList.innerHTML = '<p class="hint">没有找到家庭</p>';
        return;
    }

    homes.forEach(home => {
        const item = document.createElement('div');
        item.className = 'home-item' + (currentHomeId === home.id ? ' active' : '');
        item.innerHTML = `<i class="fas fa-home"></i>${home.name}`;
        item.onclick = () => selectHome(home.id);
        homeList.appendChild(item);
    });
}

function renderDevices(devices) {
    deviceList.innerHTML = '';

    if (!devices || devices.length === 0) {
        deviceList.innerHTML = '<p class="hint">没有找到设备</p>';
        return;
    }

    devices.forEach(device => {
        const card = document.createElement('div');
        card.className = 'device-card';
        card.innerHTML = `
            <div class="device-header">
                <div class="device-name">${device.name}</div>
                <span class="device-status ${device.online ? 'online' : 'offline'}">
                    ${device.online ? '在线' : '离线'}
                </span>
            </div>
            <div class="device-info">
                <p><i class="fas fa-cube"></i> ${device.type_name}</p>
                <p><i class="fas fa-door-open"></i> ${device.room}</p>
                <p><i class="fas fa-microchip"></i> ${device.model || '未知型号'}</p>
                <p><i class="fas fa-hashtag"></i> ID: ${device.id}</p>
            </div>
        `;
        deviceList.appendChild(card);
    });
}

// ==================== 事件处理 ====================

async function handleLogin() {
    const account = accountInput.value.trim();
    const password = passwordInput.value;

    if (!account || !password) {
        showMessage(loginMessage, '请输入账号和密码', true);
        return;
    }

    hideMessage(loginMessage);
    showLoading();
    loginBtn.disabled = true;

    try {
        const result = await login(account, password);

        if (result.success) {
            showMessage(loginMessage, '登录成功！', false);
            setTimeout(() => {
                initMainView(account);
            }, 500);
        } else {
            showMessage(loginMessage, result.message || '登录失败', true);
        }
    } catch (error) {
        showMessage(loginMessage, '登录请求失败: ' + error.message, true);
    } finally {
        hideLoading();
        loginBtn.disabled = false;
    }
}

async function handleLogout() {
    showLoading();

    try {
        await logout();
        currentHomeId = null;
        showLoginView();
        accountInput.value = '';
        passwordInput.value = '';
        hideMessage(loginMessage);
    } catch (error) {
        console.error('退出登录失败:', error);
    } finally {
        hideLoading();
    }
}

async function selectHome(homeId) {
    currentHomeId = homeId;

    // 更新 UI 选中状态
    document.querySelectorAll('.home-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.home-item').classList.add('active');

    // 加载设备
    showLoading();
    try {
        const data = await getDevices(homeId);
        renderDevices(data.devices);
    } catch (error) {
        deviceList.innerHTML = `<p class="hint">加载设备失败: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

async function initMainView(account) {
    showMainView();
    userAccount.textContent = `账号: ${account}`;

    // 加载家庭列表
    showLoading();
    try {
        const data = await getHomes();
        renderHomes(data.homes);

        // 自动选择第一个家庭
        if (data.homes && data.homes.length > 0) {
            currentHomeId = data.homes[0].id;
            renderHomes(data.homes); // 重新渲染以显示选中状态

            const devicesData = await getDevices(currentHomeId);
            renderDevices(devicesData.devices);
        }
    } catch (error) {
        homeList.innerHTML = `<p class="hint">加载家庭失败: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

// ==================== 初始化 ====================

async function init() {
    // 绑定事件
    loginBtn.onclick = handleLogin;
    logoutBtn.onclick = handleLogout;

    // 回车登录
    passwordInput.onkeypress = (e) => {
        if (e.key === 'Enter') handleLogin();
    };
    accountInput.onkeypress = (e) => {
        if (e.key === 'Enter') passwordInput.focus();
    };

    // 检查登录状态
    showLoading();
    try {
        const status = await checkStatus();

        if (status.logged_in) {
            initMainView(status.account);
        } else {
            showLoginView();
        }
    } catch (error) {
        showLoginView();
    } finally {
        hideLoading();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
