document.addEventListener('DOMContentLoaded', function() {
  // Получаем данные с сервера
  const serverData = JSON.parse(document.getElementById('server-data').textContent);
  const loggedInUser = serverData.user;
  
  console.log('🔍 Данные пользователя:', loggedInUser);
  
  // Получаем элементы
  const authButtons = document.getElementById('authButtons');
  const logoutSection = document.getElementById('logoutSection');
  const welcomeText = document.getElementById('welcomeText');
  
  // Функция для показа элементов авторизованного пользователя
  function showAuthenticatedUser() {
    console.log('✅ Показываем интерфейс для авторизованного пользователя');
    
    // Скрываем кнопки входа/регистрации
    authButtons.classList.remove('auth-visible');
    authButtons.classList.add('auth-hidden');
    
    // Показываем кнопку выхода и приветствие
    logoutSection.classList.remove('auth-hidden');
    logoutSection.classList.add('auth-visible');
    
    welcomeText.classList.remove('auth-hidden');
    welcomeText.classList.add('auth-inline');
    
    // Устанавливаем текст приветствия
    if (welcomeText) {
      welcomeText.textContent = `Привіт, ${loggedInUser.username}!`;
    }
  }
  
  // Функция для показа элементов неавторизованного пользователя
  function showGuestUser() {
    console.log('❌ Показываем интерфейс для неавторизованного пользователя');
    
    // Показываем кнопки входа/регистрации
    authButtons.classList.remove('auth-hidden');
    authButtons.classList.add('auth-visible');
    
    // Скрываем кнопку выхода и приветствие
    logoutSection.classList.remove('auth-visible');
    logoutSection.classList.add('auth-hidden');
    
    welcomeText.classList.remove('auth-inline');
    welcomeText.classList.add('auth-hidden');
  }
  
  // Применяем соответствующий интерфейс
  if (loggedInUser && loggedInUser.username) {
    showAuthenticatedUser();
  } else {
    showGuestUser();
  }
  
  // Обработчик регистрации
  document.getElementById('registerSubmit').addEventListener('click', async function () {
    const name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirm = document.getElementById('regConfirmPassword').value;

    if (!name || !email || !password || !confirm) {
      alert('❌ Заповніть усі поля!');
      return;
    }

    if (password !== confirm) {
      alert('❌ Паролі не співпадають!');
      return;
    }

    try {
      const res = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: name, email, password })
      });

      const data = await res.json();

      if (res.ok) {
        alert('✅ Реєстрація успішна!');
        // Закрываем модальное окно
        const modal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
        modal.hide();
        // Перезагружаем страницу
        setTimeout(() => location.reload(), 500);
      } else {
        alert('❌ ' + (data.error || 'Помилка реєстрації'));
      }
    } catch (error) {
      console.error('Ошибка регистрации:', error);
      alert('❌ Помилка підключення до сервера');
    }
  });

  // Обработчик входа
  document.getElementById('loginSubmit').addEventListener('click', async function () {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
      alert('❌ Заповніть усі поля!');
      return;
    }

    try {
      const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();

      if (res.ok) {
        alert('✅ Вхід успішний. Привіт, ' + data.user.username + '!');
        // Закрываем модальное окно
        const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
        modal.hide();
        // Перезагружаем страницу
        setTimeout(() => location.reload(), 500);
      } else {
        alert('❌ ' + (data.error || 'Невірний email або пароль'));
      }
    } catch (error) {
      console.error('Ошибка входа:', error);
      alert('❌ Помилка підключення до сервера');
    }
  });

  // Обработчик выхода
  document.getElementById('btnLogout').addEventListener('click', async function() {
    try {
      const res = await fetch('/logout', { method: 'POST' });
      if (res.ok) {
        alert('✅ Ви успішно вийшли з системи');
        location.reload();
      } else {
        alert('❌ Помилка при виході');
      }
    } catch (error) {
      console.error('Ошибка выхода:', error);
      alert('❌ Помилка підключення до сервера');
    }
  });

  document.getElementById('sortSelect').addEventListener('change', function () {
    const url = new URL(window.location);
    const sortValue = this.value;

    if (sortValue) {
        url.searchParams.set('sort', sortValue);
    } else {
        url.searchParams.delete('sort');
    }

    window.location.href = url.toString();
    });


      // Застосувати фільтри
  document.getElementById('applyFilters').addEventListener('click', function () {
    const url = new URL(window.location);

    // Текстові фільтри
    const selectFilters = [
      'brand', 'os', 'screen_type', 'refresh_rate', 'ram', 'rom',
      'video_recording', 'wifi_version', 'bluetooth_version', 'sim_type',
      'sim_count', 'fingerprint_sensor', 'body_material', 'ip_protection', 'color'
    ];

    selectFilters.forEach(key => {
      const element = document.getElementById(`${key}Filter`);
      if (element) {
        const value = element.value;
        if (value) {
          url.searchParams.set(key, value);
        } else {
          url.searchParams.delete(key);
        }
      }
    });

    // Чекбокси
    const checkboxFilters = [
      'microsd_support', 'optical_stabilization', 'wireless_charge', 'reverse_charge',
      'support_5g', 'gps', 'nfc', 'ir_port', 'volte_support', 'face_unlock'
    ];

    checkboxFilters.forEach(key => {
      const checkbox = document.getElementById(`${key}Filter`);
      if (checkbox) {
        if (checkbox.checked) {
          url.searchParams.set(key, 'on');
        } else {
          url.searchParams.delete(key);
        }
      }
    });

    // Застосування фільтрів
    window.location.href = url.toString();
  });

  // Очистити фільтри
  document.getElementById('clearFilters').addEventListener('click', function () {
    const url = new URL(window.location);

    // Видаляємо всі параметри фільтрів
    const keys = [
      'brand', 'os', 'screen_type', 'refresh_rate', 'ram', 'rom',
      'video_recording', 'wifi_version', 'bluetooth_version', 'sim_type',
      'sim_count', 'fingerprint_sensor', 'body_material', 'ip_protection', 'color',
      'microsd_support', 'optical_stabilization', 'wireless_charge', 'reverse_charge',
      'support_5g', 'gps', 'nfc', 'ir_port', 'volte_support', 'face_unlock'
    ];

    keys.forEach(key => url.searchParams.delete(key));

    // Також видаляємо пошук, якщо потрібно
    url.searchParams.delete('q');

    // Переходимо без фільтрів
    window.location.href = url.toString();
  });


});