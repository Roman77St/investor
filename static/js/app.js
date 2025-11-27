const API_ROOT = '/api/portfolio/trade/';
const SUMMARY_URL = '/api/portfolio/summary/';
const HISTORY_URL = '/api/portfolio/history/';
const LOGIN_URL = '/auth/token/login/';
const LOGOUT_URL = '/auth/token/logout/';
const tokenKey = 'authToken';

// --- УТИЛИТЫ ---

function getAuthToken() {
    return localStorage.getItem(tokenKey);
}

function setAuthToken(token) {
    localStorage.setItem(tokenKey, token);
    checkAuthStatus();
}

function clearAuthToken() {
    localStorage.removeItem(tokenKey);
    checkAuthStatus();
    document.getElementById('portfolio-view').style.display = 'none';
    document.getElementById('status-message').textContent = 'Вы вышли из системы.';
}

function displayMessage(message, isError = false) {
    const statusElement = document.getElementById('status-message');
    statusElement.textContent = message;
    statusElement.style.color = isError ? 'white' : 'white'; // Белый текст для контраста
    statusElement.style.backgroundColor = isError ? '#dc3545' : '#28a745'; // Красный/Зеленый фон
    statusElement.style.border = 'none';
    setTimeout(() => {
        statusElement.textContent = '';
        statusElement.style.backgroundColor = 'transparent';
    }, 5000);
}

// --- ОБРАБОТКА АУТЕНТИФИКАЦИИ ---

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(LOGIN_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            setAuthToken(data.auth_token);
            displayMessage(`Добро пожаловать, ${username}!`);
            document.getElementById('user-display').textContent = username;
            await fetchPortfolioSummary();
        } else {
            const errorMessage = data.non_field_errors ? data.non_field_errors[0] : 'Неверные учетные данные.';
            displayMessage(`Ошибка входа: ${errorMessage}`, true);
        }
    } catch (error) {
        displayMessage('Произошла ошибка сети при входе.', true);
        console.error(error);
    }
});

document.getElementById('logout-button').addEventListener('click', clearAuthToken);

function checkAuthStatus() {
    const token = getAuthToken();
    const portfolioView = document.getElementById('portfolio-view');
    const loginForm = document.getElementById('login-form');
    const logoutButton = document.getElementById('logout-button');

    if (token) {
        loginForm.style.display = 'none';
        logoutButton.style.display = 'inline-block';
        portfolioView.style.display = 'block';
        // Предполагаем, что имя пользователя сохранено или получаем его из API
        // Для простоты, здесь имя пользователя не сохраняется, но в реальном приложении нужно получать его из /auth/users/me
        document.getElementById('user-display').textContent = 'загрузка...';
        fetchPortfolioSummary();
    } else {
        loginForm.style.display = 'flex';
        logoutButton.style.display = 'none';
        portfolioView.style.display = 'none';
    }
}

// --- ПОРТФЕЛЬ И P&L ---

async function fetchPortfolioSummary() {
    const token = getAuthToken();
    if (!token) return;

    try {
        const response = await fetch(SUMMARY_URL, {
            headers: { 'Authorization': `Token ${token}` }
        });

        if (response.status === 401) {
            clearAuthToken();
            displayMessage('Сессия истекла. Войдите снова.', true);
            return;
        }

        const summary = await response.json();

        // 1. Отображение сводки
        document.getElementById('balance-display').textContent = parseFloat(summary.balance).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' });
        document.getElementById('market-value-display').textContent = parseFloat(summary.total_market_value).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' });

        const pnlElement = document.getElementById('pnl-display');
        const pnlValue = parseFloat(summary.total_profit_loss);
        const pnlPercent = parseFloat(summary.total_profit_loss_percent);

        const pnlDisplay = pnlValue.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' });

        pnlElement.textContent = `${pnlDisplay} (${pnlPercent.toFixed(2)}%)`;
        pnlElement.className = pnlValue >= 0 ? 'profit' : 'loss';

        // 2. Отображение активов
        const tbody = document.getElementById('assets-table').querySelector('tbody');
        tbody.innerHTML = '';

        summary.assets.forEach(asset => {
            const row = tbody.insertRow();

            const assetPnl = parseFloat(asset.profit_loss);
            const assetPnlPercent = parseFloat(asset.profit_loss_percent);

            const pnlClass = assetPnl >= 0 ? 'profit' : 'loss';
            const marketValue = parseFloat(asset.market_value);

            row.insertCell().textContent = asset.ticker;
            row.insertCell().textContent = asset.quantity;
            row.insertCell().textContent = parseFloat(asset.average_buy_price).toFixed(2);
            row.insertCell().textContent = parseFloat(asset.current_price).toFixed(2);
            row.insertCell().textContent = marketValue.toFixed(2);
            row.insertCell().innerHTML = `<span class="${pnlClass}">${assetPnl.toFixed(2)}</span>`;
            row.insertCell().innerHTML = `<span class="${pnlClass}">${assetPnlPercent.toFixed(2)}%</span>`;
            row.insertCell().textContent = asset.lot_size;
        });

    } catch (error) {
        displayMessage('Не удалось загрузить данные портфеля.', true);
        console.error(error);
    }
    await fetchTransactionHistory();
}

async function fetchTransactionHistory() {
    const token = getAuthToken();
    if (!token) return;

    try {
        const response = await fetch(HISTORY_URL, {
            headers: { 'Authorization': `Token ${token}` }
        });

        if (response.status === 401) {
            // Если сессия истекла, это будет поймано в fetchPortfolioSummary
            return;
        }

        const history = await response.json();

        const tbody = document.getElementById('history-table').querySelector('tbody');
        tbody.innerHTML = ''; // Очистка старых данных

        history.forEach(tx => {
            const row = tbody.insertRow();
            const timestamp = new Date(tx.timestamp).toLocaleString('ru-RU');
            const total = parseFloat(tx.total);
            // Стиль для "Покупка" (BUY) и "Продажа" (SELL)
            const actionClass = tx.action === 'Покупка' ? 'loss' : 'profit';
            const commission = parseFloat(tx.commission);

            row.insertCell().textContent = timestamp;
            row.insertCell().innerHTML = `<span class="${actionClass}">${tx.action}</span>`;
            row.insertCell().textContent = tx.ticker;
            row.insertCell().textContent = tx.quantity;
            row.insertCell().textContent = parseFloat(tx.price).toFixed(2);
            row.insertCell().textContent = total.toFixed(2);
            row.insertCell().textContent = commission.toFixed(2);
        });
        // Загружаем историю только если она открыта
        const historyContent = document.getElementById('history-content');
        if (historyContent.style.display !== 'none') {
            await fetchTransactionHistory();
        }
    } catch (error) {
        console.error('Не удалось загрузить историю транзакций.', error);
    }
}

// --- ОБРАБОТКА СДЕЛОК ---

async function handleTrade(actionType) {
    const token = getAuthToken();
    const tickerInput = document.getElementById('ticker');
    const quantityInput = document.getElementById('quantity');

    const ticker = tickerInput.value;
    const quantity = parseInt(quantityInput.value);

    if (!token || !ticker || !quantity) {
        displayMessage('Заполните тикер и количество.', true);
        return;
    }

    try {
        const response = await fetch(`${API_ROOT}${actionType}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`
            },
            body: JSON.stringify({ ticker, quantity })
        });

        const data = await response.json();

        if (response.ok) {
            displayMessage(data.message);
            tickerInput.value = '';
            quantityInput.value = '';
            await fetchPortfolioSummary();
        } else {
            displayMessage(`Ошибка: ${data.error || data.ticker || data.quantity || 'Неизвестная ошибка.'}`, true);
        }

    } catch (error) {
        displayMessage('Произошла ошибка сети при совершении сделки.', true);
        console.error(error);
    }
}

// Инициализация при загрузке страницы
window.onload = checkAuthStatus;

// Скрытие - показ истории транзакцийю
function toggleHistory() {
    const content = document.getElementById('history-content');
    const arrow = document.getElementById('history-arrow');

    if (content.style.display === 'none') {
        // ОТКРЫВАЕМ
        content.style.display = 'block';

        // Меняем символ стрелки
        arrow.textContent = '▲'; // Стрелка вверх (свернуть)
        // Или arrow.textContent = '▼'; если хотите стрелку вниз

        arrow.classList.add('open'); // Добавляем класс (для анимации, если нужно)

        // Загружаем данные
        fetchTransactionHistory();
    } else {
        // ЗАКРЫВАЕМ
        content.style.display = 'none';

        // Возвращаем исходную стрелку
        arrow.textContent = '▼'; // Стрелка вниз (развернуть)
        // Или arrow.textContent = '▶';

        arrow.classList.remove('open');
    }
}