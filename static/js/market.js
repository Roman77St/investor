// static/js/market.js

// Предполагается, что константы API (SUMMARY_URL, HISTORY_URL, etc.),
// функции (getAuthToken, displayMessage) доступны из app.js


// --- 2. ГЛАВНАЯ ФУНКЦИЯ ЗАГРУЗКИ (Вызывается из market.html) ---

function checkAuthAndLoadMarket() {
    const token = getAuthToken();
    const userDisplay = document.getElementById('user-display');
    const portfolioView = document.getElementById('portfolio-view');

    if (!token) {
        // Если нет токена, перенаправляем на страницу входа
        if (portfolioView) portfolioView.style.display = 'none';
        displayMessage('Необходим вход для доступа к бирже.', true);
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return;
    }

    // Вставляем основной HTML
    if (portfolioView) portfolioView.style.display = 'block';

    // Временно получаем имя пользователя из токена или API
    userDisplay.textContent = 'загрузка...';

    // Загружаем данные портфеля
    fetchPortfolioSummary();
}


// --- 3. ЛОГИКА ПОРТФЕЛЯ (Включая P&L) ---
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

// --- 4. ЛОГИКА СДЕЛОК ---
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

    // 💡 ИСПРАВЛЕНИЕ: Выбираем нужный URL из констант
    let tradeUrl;
    if (actionType === 'buy') {
        tradeUrl = TRADE_BUY_URL;
    } else if (actionType === 'sell') {
        tradeUrl = TRADE_SELL_URL;
    } else {
        displayMessage('Неизвестный тип сделки.', true);
        return;
    }

    try {
        const response = await fetch(tradeUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`,
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

// --- 5. ЛОГИКА ИСТОРИИ ---
// (Скопируйте сюда fetchTransactionHistory и toggleHistory)

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
    } catch (error) {
        console.error('Не удалось загрузить историю транзакций.', error);
    }
}

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