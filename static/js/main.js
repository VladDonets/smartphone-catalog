document.addEventListener('DOMContentLoaded', function() {
  // Получаем данные с сервера
  const serverDataElement = document.getElementById('server-data');
  let loggedInUser = null;
  
  if (serverDataElement) {
    const serverData = JSON.parse(serverDataElement.textContent);
    loggedInUser = serverData.user;
  }
  
  async function logRecommendationEvent(productId, eventType, source="recommendation") {
    if (!loggedInUser || !loggedInUser.id) {
      console.warn("⚠️ Користувач не авторизований — логування пропущено");
      return;
    }
    try {
      await fetch("/log_recommendation_event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          user_id: loggedInUser.id,
          product_id: productId,
          event_type: eventType,
          source: source
        })
      });
      console.log(`✅ Залоговано: ${eventType} для товару ${productId}`);
    } catch (err) {
      console.error("❌ Помилка логування:", err);
    }
  }

  console.log('🔍 Данные пользователя:', loggedInUser);
  
  // Получаем элементы
  const authButtons = document.getElementById('authButtons');
  const logoutSection = document.getElementById('logoutSection');
  const welcomeText = document.getElementById('welcomeText');
  
  // Функция для показа элементов авторизованного пользователя
  function showAuthenticatedUser() {
    console.log('✅ Показываем интерфейс для авторизованного пользователя');
    
    const authButtons = document.getElementById('authButtons');
    const logoutSection = document.getElementById('logoutSection');
    const welcomeText = document.getElementById('welcomeText');
    
    if (authButtons) {
      authButtons.classList.remove('auth-visible');
      authButtons.classList.add('auth-hidden');
    }
    
    if (logoutSection) {
      logoutSection.classList.remove('auth-hidden');
      logoutSection.classList.add('auth-visible');
    }
    
    if (welcomeText) {
      welcomeText.classList.remove('auth-hidden');
      welcomeText.classList.add('auth-inline');
      welcomeText.textContent = `Привіт, ${loggedInUser.username}!`;
    }
  }
  
  // Функция для показа элементов неавторизованного пользователя
  function showGuestUser() {
    console.log('❌ Показываем интерфейс для неавторизованного пользователя');
    
    const authButtons = document.getElementById('authButtons');
    const logoutSection = document.getElementById('logoutSection');
    const welcomeText = document.getElementById('welcomeText');
    
    if (authButtons) {
      authButtons.classList.remove('auth-hidden');
      authButtons.classList.add('auth-visible');
    }
    
    if (logoutSection) {
      logoutSection.classList.remove('auth-visible');
      logoutSection.classList.add('auth-hidden');
    }
    
    if (welcomeText) {
      welcomeText.classList.remove('auth-inline');
      welcomeText.classList.add('auth-hidden');
    }
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
  const btnLogout = document.getElementById('btnLogout');
  if (btnLogout) {
  btnLogout.addEventListener('click', async function() {
    try {
      const res = await fetch('/logout', { method: 'POST' });
      if (res.ok) {
        alert('✅ Ви успішно вийшли з системи');
        window.location.href = '/';
      } else {
        alert('❌ Помилка при виході');
      }
    } catch (error) {
      console.error('Помилка виходу:', error);
      alert('❌ Помилка підключення до сервера');
    }
  });
}

  //Сортувальник
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

    // Enhanced click handler with proper event tracking
  document.addEventListener('click', async function(e) {
    // Product link clicks (navigation to product page)
    if (e.target.closest("a[href*='/product/']")) {
      const link = e.target.closest("a[href*='/product/']");
      const productId = link.getAttribute("href").split("/").pop();
      const source = determineSource(link);
      
      // Log the click event
      await logRecommendationEvent(productId, "clicked", source);
    }

    // Wishlist button handler
    if (e.target.classList.contains('wishlist-btn') || e.target.closest('.wishlist-btn')) {
      e.preventDefault();
      const btn = e.target.classList.contains('wishlist-btn') ? e.target : e.target.closest('.wishlist-btn');
      const productId = btn.getAttribute('data-product-id');
      const source = determineSource(btn);
      
      try {
        const response = await fetch('/add-to-wishlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ product_id: parseInt(productId) })
        });
        
        const data = await response.json();
        
        if (data.success) {
          alert('✅ ' + data.message);
          btn.style.backgroundColor = '#dc3545';
          btn.style.color = 'white';
          
          // Log wishlist event
          await logRecommendationEvent(productId, "wishlisted", source);
        } else {
          if (response.status === 401) {
            alert('❌ Для додавання товарів до вишлисту необхідно авторизуватися!');
          } else {
            alert('❌ ' + data.error);
          }
        }
      } catch (error) {
        console.error('Error adding to wishlist:', error);
        alert('❌ Помилка підключення до сервера');
      }
    }
    
    // Обработчик для кнопки корзины
    if (e.target.classList.contains('cart-btn') || e.target.closest('.cart-btn')) {
      e.preventDefault();
      const btn = e.target.classList.contains('cart-btn') ? e.target : e.target.closest('.cart-btn');
      const productId = btn.getAttribute('data-product-id');
      const source = determineSource(btn);
      
      try {
        const response = await fetch('/add-to-cart', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ product_id: parseInt(productId), quantity: 1 })
        });
        
        const data = await response.json();
        
        if (data.success) {
          alert('✅ ' + data.message);
          btn.style.backgroundColor = '#0d6efd';
          btn.style.color = 'white';
          
          // Log cart event
          await logRecommendationEvent(productId, "added_to_cart", source);
        } else {
          if (response.status === 401) {
            alert('❌ Для додавання товарів до кошика необхідно авторизуватися!');
          } else {
            alert('❌ ' + data.error);
          }
        }
      } catch (error) {
        console.error('Error adding to cart:', error);
        alert('❌ Помилка підключення до сервера');
      }
    }

    // Обробка кнопки "Прибрати з вішлиста"
    if (e.target.classList.contains('remove-wishlist-btn') || e.target.closest('.remove-wishlist-btn')) {
      e.preventDefault();
      const btn = e.target.classList.contains('remove-wishlist-btn') ? e.target : e.target.closest('.remove-wishlist-btn');
      const productId = btn.getAttribute('data-product-id');

      try {
        const response = await fetch('/remove-from-wishlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ product_id: parseInt(productId) })
        });

        const data = await response.json();

        if (data.success) {
          alert('✅ ' + data.message);
          location.reload();
        } else {
          if (response.status === 401) {
            alert('❌ Необхідно авторизуватися');
          } else {
            alert('❌ ' + data.error);
          }
        }
      } catch (error) {
        console.error('Error removing from wishlist:', error);
        alert('❌ Помилка підключення до сервера');
      }
    }
  });

  // визначення івенту
  function determineSource(element) {
    if (element.closest('.recommendation-block') || element.closest('.rec-card')) {
      return 'recommendation';
    } else if (element.closest('.product-card')) {
      return 'catalog';
    } else if (window.location.pathname.includes('/product/')) {
      return 'product_page';
    } else if (window.location.pathname.includes('/wishlist')) {
      return 'wishlist';
    } else if (window.location.pathname.includes('/cart')) {
      return 'cart';
    } else {
      return 'unknown';
    }
  }

  let carouselPositions = {};

function slideCarousel(carouselId, direction) {
  const carousel = document.getElementById(carouselId);
  if (!carousel) return;
  
  if (!carouselPositions[carouselId]) {
    carouselPositions[carouselId] = 0;
  }
  
  const cardWidth = 195; // 180px + 15px gap
  const scrollAmount = cardWidth * 3;
  
  carouselPositions[carouselId] += direction * scrollAmount;
  
  const maxScroll = carousel.scrollWidth - carousel.clientWidth;
  carouselPositions[carouselId] = Math.max(0, Math.min(carouselPositions[carouselId], maxScroll));
  
  carousel.scrollTo({
    left: carouselPositions[carouselId],
    behavior: 'smooth'
  });
}

function trackRecommendationClick(productId, source) {
  fetch('/track-recommendation-event', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: parseInt(productId), event_type: 'clicked', source })
  }).catch(error => console.error('Error tracking recommendation click:', error));
}

document.addEventListener("click", function(e) {
  // Клік по товару (перехід на сторінку)
  if (e.target.closest("a[href*='/product/']")) {
    const productId = e.target.closest("a").getAttribute("href").split("/").pop();
    logRecommendationEvent(productId, "clicked");
  }

  // Клік по "вишлист"
  if (e.target.classList.contains("wishlist-btn")) {
    const productId = e.target.dataset.productId;
    logRecommendationEvent(productId, "wishlist");
  }

  // Клік по "кошик"
  if (e.target.classList.contains("cart-btn")) {
    const productId = e.target.dataset.productId;
    logRecommendationEvent(productId, "cart");
  }
});

// Инициализация каруселей
document.querySelectorAll('[id^="recCarousel"]').forEach(carousel => {
    const id = carousel.id;
    const num = id.replace('recCarousel', '');
    const prevBtn = document.getElementById('prevRec' + num);
    const nextBtn = document.getElementById('nextRec' + num);
    
    if (prevBtn) prevBtn.addEventListener('click', () => slideCarousel(id, -1));
    if (nextBtn) nextBtn.addEventListener('click', () => slideCarousel(id, 1));
  });

  const prevRecEndBtn = document.getElementById('prevRecEnd');
  const nextRecEndBtn = document.getElementById('nextRecEnd');
  
  if (prevRecEndBtn) prevRecEndBtn.addEventListener('click', () => slideCarousel('recCarouselEnd', -1));
  if (nextRecEndBtn) nextRecEndBtn.addEventListener('click', () => slideCarousel('recCarouselEnd', 1));

  console.log('✅ Система логування рекомендацій ініціалізована');

  document.getElementById('prevRecEnd')?.addEventListener('click', () => slideCarousel('recCarouselEnd', -1));
  document.getElementById('nextRecEnd')?.addEventListener('click', () => slideCarousel('recCarouselEnd', 1));

  document.querySelectorAll(".recommendation-block a").forEach(link => {
      link.addEventListener("click", function () {
        const productId = this.getAttribute("href").split("/").pop();
        logRecommendationEvent(productId, "click");
      });
  });

  // 2️⃣ Додавання у вішлист із рекомендацій
  document.querySelectorAll(".recommendation-block .wishlist-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const productId = this.dataset.productId;
      logRecommendationEvent(productId, "wishlist_add");
    });
  });

  // 3️⃣ Додавання у корзину із рекомендацій
  document.querySelectorAll(".recommendation-block .cart-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      const productId = this.dataset.productId;
      logRecommendationEvent(productId, "cart_add");
    });
  });
});