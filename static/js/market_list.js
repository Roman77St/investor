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

    // 1. Сбор значений фильтров и поискового запроса
    const searchInput = document.getElementById('market-search-input');
    const sectorElement = document.getElementById('filter-sector');
    const listingElement = document.getElementById('filter-listing');
    const typeElement = document.getElementById('filter-type');
    const blueChipElement = document.getElementById('filter-bluechip');

    const params = new URLSearchParams();

    // Поисковый запрос (q)
    if (searchInput && searchInput.value) {
        params.append('q', searchInput.value.trim());
    }

    // Фильтры (проверяем наличие элемента и его значение)
    if (sectorElement && sectorElement.value !== 'ALL') {
        params.append('sector', sectorElement.value);
    }
    if (listingElement && listingElement.value !== 'ALL') {
        params.append('listing_level', listingElement.value);
    }
    if (typeElement && typeElement.value !== 'ALL') {
        params.append('stock_type', typeElement.value);
    }
    // Голубые фишки (отправляем 'true' только если чекбокс отмечен)
    if (blueChipElement && blueChipElement.checked) {
        params.append('blue_chip', 'true');
    }

    // 2. Формируем конечный URL с параметрами
    const url = `${MARKET_LIST_URL}?${params.toString()}`;

    try {
        const response = await fetch(url, {
            headers: { 'Authorization': `Token ${token}` }
        });

        if (!response.ok) {
            tableBody.innerHTML = '<tr><td colspan="4">Ошибка загрузки данных рынка.</td></tr>';
            return;
        }

        const stocks = await response.json();

        // 3. Очищаем и рендерим данные
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

        // 4. Добавляем обработчики для кнопок "Купить"
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

// --- ИНИЦИАЛИЗАЦИЯ ---

document.addEventListener('DOMContentLoaded', () => {
    // Получаем элементы управления
    const applyButton = document.getElementById('apply-filters-button');
    const searchInput = document.getElementById('market-search-input');

    // 1. Привязываем кнопку "Применить"
    if (applyButton) {
        // При клике на "Применить" вызываем загрузку данных с фильтрами
        applyButton.addEventListener('click', fetchAndRenderMarketList);
    }
    // 2. Привязываем поле поиска
    if (searchInput) {
        // При вводе в поле поиска вызываем загрузку с задержкой (debounce)
        searchInput.addEventListener('input', debounce(filterMarketTable, 300));
    }
    // 3. Запускаем первоначальную загрузку
    if (getAuthToken()) {
        fetchAndRenderMarketList();
    }
});
