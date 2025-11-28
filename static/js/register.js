// Предполагается, что константы (REGISTER_URL, displayMessage) доступны из app.js

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const passwordConfirm = document.getElementById('register-password-confirm').value;

    if (password !== passwordConfirm) {
        displayMessage('Пароли не совпадают!', true);
        return;
    }

    try {
        const response = await fetch(REGISTER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.status === 201) {
            displayMessage(`Пользователь ${username} успешно зарегистрирован! Перенаправление...`, false);
            // Задержка и перенаправление на страницу входа
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            let errorMessage = 'Ошибка регистрации.';
            if (data.username) {
                errorMessage = `Имя пользователя: ${data.username[0]}`;
            } else if (data.password) {
                errorMessage = `Пароль: ${data.password[0]}`;
            }
            displayMessage(`Ошибка регистрации: ${errorMessage}`, true);
        }
    } catch (error) {
        displayMessage('Произошла ошибка сети при регистрации.', true);
        console.error(error);
    }
});