/**
 * Загружает полный список акций с ценами и рендерит его в таблице.
 */
async function fetchAndRenderMarketList() {
    const token = getAuthToken();
    if (!token) {
        // Дополнительная проверка на всякий случай, хотя app.js должен был перенаправить
        window.location.href = '/';
        return;
    }

    const tableBody = document.querySelector('#market-stocks-table tbody');
    tableBody.innerHTML = '<tr><td colspan="4">Загрузка...</td></tr>';

    try {
        const response = await fetch(MARKET_LIST_URL, {
            headers: { 'Authorization': `Token ${token}` }
        });

        if (!response.ok) {
            tableBody.innerHTML = '<tr><td colspan="4">Ошибка загрузки данных рынка.</td></tr>';
            return;
        }

        const stocks = await response.json();

        // Очищаем и рендерим данные
        tableBody.innerHTML = '';
        if (stocks.length === 0) {
             tableBody.innerHTML = '<tr><td colspan="4">На рынке нет доступных акций.</td></tr>';
             return;
        }

        stocks.forEach(stock => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = stock.ticker;
            row.insertCell().textContent = stock.name;
            row.insertCell().textContent = parseFloat(stock.current_price).toFixed(2);

            // Кнопка для быстрого перехода к покупке
            const actionCell = row.insertCell();
            actionCell.innerHTML = `<button class="buy-market-btn" data-ticker="${stock.ticker}">Купить</button>`;
        });

        // Добавляем обработчики для кнопок "Купить"
        attachBuyButtonListeners();

    } catch (error) {
        console.error('Сетевая ошибка при загрузке рынка:', error);
        tableBody.innerHTML = '<tr><td colspan="4">Ошибка соединения.</td></tr>';
    }
}

/**
 * Привязывает обработчик к кнопкам "Купить", которые могут быть добавлены динамически.
 * В MVP мы просто перенаправляем пользователя на страницу портфеля с предзаполненным тикером.
 */
function attachBuyButtonListeners() {
    document.querySelectorAll('.buy-market-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const ticker = e.target.getAttribute('data-ticker');

            // 💡 Временный хак: перенаправляем на страницу портфеля и сохраняем тикер
            // В реальном приложении лучше использовать модальное окно.
            localStorage.setItem('prefillTicker', ticker);
            window.location.href = '/market/';
        });
    });
}


// --- ДОБАВЛЕНИЕ ЛОГИКИ ПОИСКА/ФИЛЬТРАЦИИ (необходимо) ---

// 💡 Заглушка для фильтрации на стороне клиента
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('market-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterMarketTable, 300));
    }
});

function filterMarketTable(e) {
    const filter = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#market-stocks-table tbody tr');

    rows.forEach(row => {
        // Получаем тикер и название
        const ticker = row.cells[0].textContent.toLowerCase();
        const name = row.cells[1].textContent.toLowerCase();

        if (ticker.includes(filter) || name.includes(filter) || filter === '') {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Утилита Debounce (для улучшения производительности поиска)
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}