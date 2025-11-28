// --- КОНСТАНТЫ API ---
const API_ROOT = '/api/portfolio/'; // Общий корень API
const SUMMARY_URL = API_ROOT + 'summary/';
const HISTORY_URL = API_ROOT + 'history/';
const TRADE_BUY_URL = API_ROOT + 'trade/buy/';
const TRADE_SELL_URL = API_ROOT + 'trade/sell/';
const LOGIN_URL = '/auth/token/login/';
const REGISTER_URL = '/auth/users/';
const tokenKey = 'authToken';

// --- УТИЛИТЫ ТОКЕНА ---
function getAuthToken() {
    return localStorage.getItem(tokenKey);
}
function setAuthToken(token) {
    localStorage.setItem(tokenKey, token);
}
function clearAuthToken() {
    localStorage.removeItem(tokenKey);
}

// --- УТИЛИТЫ СООБЩЕНИЙ ---
function displayMessage(message, isError = false) {
    const statusElement = document.getElementById('status-message');
    if (!statusElement) return;

    statusElement.textContent = message;
    statusElement.style.color = 'white';
    statusElement.style.backgroundColor = isError ? '#dc3545' : '#28a745';
    statusElement.style.border = 'none';

    if (!isError) {
        setTimeout(() => {
            statusElement.textContent = '';
            statusElement.style.backgroundColor = 'transparent';
        }, 5000);
    }
}

// --- ЛОГИКА ИМЕНИ ПОЛЬЗОВАТЕЛЯ (Placeholder) ---
function getUsernameFromToken() {
    // В реальном приложении: декодирование JWT или получение имени через API
    return 'User';
}

// --- ЛОГИКА ПЕРЕНАПРАВЛЕНИЯ И ОБНОВЛЕНИЯ HEADER ---

function checkAuthAndRedirect() {
    const token = getAuthToken();
    const isMarketPage = window.location.pathname === '/market/';

    // Элементы всегда доступны, так как они в base.html
    const logoutButton = document.getElementById('logout-button');
    const userInfoDisplay = document.getElementById('user-info-display');

    if (token) {
        // --- Авторизован ---
        logoutButton.style.display = 'inline-block';
        userInfoDisplay.textContent = `Добро пожаловать, ${getUsernameFromToken() || 'Пользователь'}.`;

        if (!isMarketPage) {
            // Если на странице входа или регистрации, перенаправляем на биржу
            window.location.href = '/market/';
        }
    } else {
        // --- Не авторизован ---
        logoutButton.style.display = 'none';
        userInfoDisplay.textContent = '';

        if (isMarketPage) {
            // Если на странице биржи без токена, перенаправляем на вход
            window.location.href = '/';
        }
    }
}

// -----------------------------------------------------------
// ГЛАВНЫЙ БЛОК: Запуск логики после загрузки всех элементов DOM
// -----------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {

    // 1. ПРИВЯЗКА ЛОГИКИ ВХОДА
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;

            try {
                const response = await fetch(LOGIN_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (response.ok) {
                    setAuthToken(data.auth_token);
                    // Перенаправляем на страницу биржи
                    window.location.href = '/market/';
                } else {
                    const errorMessage = data.non_field_errors ? data.non_field_errors[0] : 'Неверные учетные данные.';
                    displayMessage(`Ошибка входа: ${errorMessage}`, true);
                }
            } catch (error) {
                displayMessage('Произошла ошибка сети при входе.', true);
                console.error(error);
            }
        });
    }

    // 2. ПРИВЯЗКА ЛОГИКИ ВЫХОДА (Кнопка в base.html)
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            clearAuthToken();
            window.location.href = '/';
        });
    }

    // 3. ЗАПУСК ГЛОБАЛЬНОЙ ПРОВЕРКИ АУТЕНТИФИКАЦИИ
    // Вызываем checkAuthAndRedirect на всех страницах, КРОМЕ index.html,
    // где его нужно вызвать через window.onload, чтобы не конфликтовать с market.html
    const pathname = window.location.pathname;
    if (pathname === '/market/') {
        // На странице /market/ нам нужно обновить header и перенаправить, если токена нет.
        // Запускаем здесь, если market.html не использует window.onload.
        checkAuthAndRedirect();
    } else if (pathname !== '/register/') {
        // На главной странице (/) мы не запускаем его сразу, так как там есть форма входа.
        // Перенаправление происходит только после успешного входа.
    }
});