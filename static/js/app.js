// --- КОНСТАНТЫ API ---
const API_ROOT = '/api/portfolio/'; // Общий корень API
const SUMMARY_URL = API_ROOT + 'summary/';
const HISTORY_URL = API_ROOT + 'history/';
const TRADE_BUY_URL = API_ROOT + 'trade/buy/';
const TRADE_SELL_URL = API_ROOT + 'trade/sell/';
const STOCK_SEARCH_URL = '/api/market/search/';
const LOGIN_URL = '/auth/token/login/';
const REGISTER_URL = '/auth/users/';
const USER_ME_URL = '/auth/users/me/';
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
    sessionStorage.removeItem('userNameDisplay');
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

/**
 * Загружает имя пользователя (FirstName LastName или Username) и отображает его в заголовке,
 * используя маршрут Djoser.
 * @returns {Promise<string>} Отображаемое имя
 */
async function fetchAndDisplayUserName() {
    const token = getAuthToken();
    const userDisplayElement = document.getElementById('user-display');       // Заголовок "Портфель <Имя>"
    const userInfoDisplayElement = document.getElementById('user-info-display'); // Приветствие "Добро пожаловать, <Имя>."

    if (!token) return 'Пользователь';

    // 1. Проверяем Session Storage, чтобы избежать лишних API-запросов
    const storedUser = sessionStorage.getItem('userNameDisplay');
    if (storedUser) {
        if (userDisplayElement) userDisplayElement.textContent = `Портфель ${storedUser}`;
        if (userInfoDisplayElement) userInfoDisplayElement.textContent = `Добро пожаловать, ${storedUser}.`;
        return storedUser;
    }

    // 2. Устанавливаем статус "загрузка" перед запросом
    if (userDisplayElement) userDisplayElement.textContent = 'Портфель (загрузка...)';

    // 3. Загружаем с API
    try {
        // Используем маршрут Djoser для получения данных пользователя
        const response = await fetch(USER_ME_URL, {
            headers: { 'Authorization': `Token ${token}` }
        });

        if (response.status === 401) {
            clearAuthToken();
            window.location.href = '/';
            return 'Пользователь';
        }

        const userData = await response.json();

        let userName;

        // 💡 ЛОГИКА ФОРМАТИРОВАНИЯ ИМЕНИ: FirstName + LastName, или Username
        if (userData.first_name && userData.last_name) {
            userName = `${userData.first_name} ${userData.last_name}`;
        } else if (userData.username) {
            userName = userData.username;
        } else {
            userName = 'Пользователь';
        }

        // 4. Сохраняем и отображаем
        sessionStorage.setItem('userNameDisplay', userName);

        if (userDisplayElement) userDisplayElement.textContent = `Портфель ${userName}`;
        if (userInfoDisplayElement) userInfoDisplayElement.textContent = `Добро пожаловать, ${userName}.`;

        return userName;

    } catch (error) {
        console.error('Не удалось загрузить данные пользователя.', error);
        if (userDisplayElement) userDisplayElement.textContent = 'Портфель (Ошибка)';
        return 'Пользователь';
    }
}

// --- ЛОГИКА ПЕРЕНАПРАВЛЕНИЯ И ОБНОВЛЕНИЯ HEADER ---

function checkAuthAndRedirect() {
    const token = getAuthToken();
    const isMarketPage = window.location.pathname === '/market/';
    const logoutButton = document.getElementById('logout-button');

    if (token) {
        // --- Авторизован ---
        if (logoutButton) logoutButton.style.display = 'inline-block';
        fetchAndDisplayUserName();

        if (!isMarketPage && window.location.pathname !== '/register/') {
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