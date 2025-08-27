from flask import Flask, jsonify, render_template, session, request, redirect, make_response
import json
import datetime
from db import get_connection
from routes.auth import auth_bp
from routes.users import users_bp
from recommendation_engine import RecommendationEngine

app = Flask(__name__)
app.secret_key = 'your-secret-key'

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)


def get_filter_options():
    """Отримуємо унікальні значення для фільтрів з БД"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    filter_options = {}
    
    # Отримуємо унікальні значення для кожного поля
    fields_to_check = [
        'brand', 'os', 'screen_type', 'refresh_rate', 'ram', 'rom',
        'video_recording', 'wifi_version', 'bluetooth_version', 'sim_type',
        'sim_count', 'fingerprint_sensor', 'body_material', 'ip_protection', 'color'
    ]
    
    for field in fields_to_check:
        cursor.execute(f"SELECT DISTINCT {field} FROM products WHERE {field} IS NOT NULL AND {field} != '' ORDER BY {field}")
        filter_options[field] = [row[field] for row in cursor.fetchall()]
    
    conn.close()
    return filter_options

def save_search_history(user_id, search_query):
    """Зберігає історію пошуку користувача в users.search_history"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT search_history FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    import json
    try:
        history = json.loads(user_data['search_history']) if user_data and user_data['search_history'] else []
    except:
        history = []

    # Добавляем новый поиск
    history.append({
        "query": search_query,
        "timestamp": datetime.datetime.now().isoformat()
    })

    cursor.execute("UPDATE users SET search_history = %s WHERE id = %s",
                   (json.dumps(history), user_id))
    conn.commit()
    conn.close()


def save_filter_history(user_id, filters):
    """Зберігає історію використання фільтрів у users.filter_history"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT filter_history FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    import json
    try:
        history = json.loads(user_data['filter_history']) if user_data and user_data['filter_history'] else []
    except:
        history = []

    history.append({
        "filters": filters,
        "timestamp": datetime.datetime.now().isoformat()
    })

    cursor.execute("UPDATE users SET filter_history = %s WHERE id = %s",
                   (json.dumps(history), user_id))
    conn.commit()
    conn.close()


def save_view_history(user_id, product_id):
    """Зберігає історію переглядів у users.view_history"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT view_history FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    import json
    try:
        history = json.loads(user_data['view_history']) if user_data and user_data['view_history'] else []
    except:
        history = []

    history.append({
        "product_id": product_id,
        "timestamp": datetime.datetime.now().isoformat()
    })

    cursor.execute("UPDATE users SET view_history = %s WHERE id = %s",
                   (json.dumps(history), user_id))
    conn.commit()
    conn.close()

def extract_active_filters(args):
    """Витягує активні фільтри з параметрів запиту"""
    filters = {}
    filter_keys = [
        'brand', 'os', 'screen_type', 'refresh_rate', 'ram', 'rom',
        'video_recording', 'wifi_version', 'bluetooth_version', 'sim_type',
        'sim_count', 'fingerprint_sensor', 'body_material', 'ip_protection', 'color',
        'microsd_support', 'optical_stabilization', 'wireless_charge', 'reverse_charge',
        'support_5g', 'gps', 'nfc', 'ir_port', 'volte_support', 'face_unlock'
    ]
    
    for key in filter_keys:
        value = args.get(key, '')
        if value:
            filters[key] = value
    
    return filters if filters else None


@app.route("/")
def index():
    user = None
    if 'user_id' in session:
        user = {'username': session.get('username')}

    # Получаем параметры сортировки и поиска
    sort = request.args.get('sort', '')
    search_query = request.args.get('q', '').strip()
    if search_query and 'user_id' in session:
        save_search_history(session['user_id'], search_query)

    # Фильтры из параметров GET
    brand = request.args.get('brand', '')
    os_ = request.args.get('os', '')
    screen_type = request.args.get('screen_type', '')
    refresh_rate = request.args.get('refresh_rate', '')
    ram = request.args.get('ram', '')
    rom = request.args.get('rom', '')
    video_recording = request.args.get('video_recording', '')
    wifi_version = request.args.get('wifi_version', '')
    bluetooth_version = request.args.get('bluetooth_version', '')
    sim_type = request.args.get('sim_type', '')
    sim_count = request.args.get('sim_count', '')
    fingerprint_sensor = request.args.get('fingerprint_sensor', '')
    body_material = request.args.get('body_material', '')
    ip_protection = request.args.get('ip_protection', '')
    color = request.args.get('color', '')

    # Boolean фильтры (checkbox)
    microsd_support = request.args.get('microsd_support', '')
    optical_stabilization = request.args.get('optical_stabilization', '')
    wireless_charge = request.args.get('wireless_charge', '')
    reverse_charge = request.args.get('reverse_charge', '')
    support_5g = request.args.get('support_5g', '')
    gps = request.args.get('gps', '')
    nfc = request.args.get('nfc', '')
    ir_port = request.args.get('ir_port', '')
    volte_support = request.args.get('volte_support', '')
    face_unlock = request.args.get('face_unlock', '')

    # Формируем SQL для сортировки
    order_by = ""
    if sort == 'title_asc':
        order_by = "ORDER BY title ASC"
    elif sort == 'title_desc':
        order_by = "ORDER BY title DESC"
    elif sort == 'price_asc':
        order_by = "ORDER BY price ASC"
    elif sort == 'price_desc':
        order_by = "ORDER BY price DESC"

    # Формируем условия WHERE
    where_clauses = []
    params = {}

    if search_query:
        where_clauses.append("title LIKE %(search)s")
        params['search'] = f"%{search_query}%"

    # Текстовые фильтры
    if brand:
        where_clauses.append("brand = %(brand)s")
        params['brand'] = brand
    if os_:
        where_clauses.append("os = %(os)s")
        params['os'] = os_
    if screen_type:
        where_clauses.append("screen_type = %(screen_type)s")
        params['screen_type'] = screen_type
    if refresh_rate:
        where_clauses.append("refresh_rate = %(refresh_rate)s")
        params['refresh_rate'] = refresh_rate
    if ram:
        where_clauses.append("ram = %(ram)s")
        params['ram'] = ram
    if rom:
        where_clauses.append("rom = %(rom)s")
        params['rom'] = rom
    if video_recording:
        where_clauses.append("video_recording = %(video_recording)s")
        params['video_recording'] = video_recording
    if wifi_version:
        where_clauses.append("wifi_version = %(wifi_version)s")
        params['wifi_version'] = wifi_version
    if bluetooth_version:
        where_clauses.append("bluetooth_version = %(bluetooth_version)s")
        params['bluetooth_version'] = bluetooth_version
    if sim_type:
        where_clauses.append("sim_type = %(sim_type)s")
        params['sim_type'] = sim_type
    if sim_count:
        where_clauses.append("sim_count = %(sim_count)s")
        params['sim_count'] = sim_count
    if fingerprint_sensor:
        where_clauses.append("fingerprint_sensor = %(fingerprint_sensor)s")
        params['fingerprint_sensor'] = fingerprint_sensor
    if body_material:
        where_clauses.append("body_material = %(body_material)s")
        params['body_material'] = body_material
    if ip_protection:
        where_clauses.append("ip_protection = %(ip_protection)s")
        params['ip_protection'] = ip_protection
    if color:
        where_clauses.append("color = %(color)s")
        params['color'] = color

    # Boolean фильтры (checkbox)
    if microsd_support == 'on':
        where_clauses.append("microsd_support = 1")
    if optical_stabilization == 'on':
        where_clauses.append("optical_stabilization = 1")
    if wireless_charge == 'on':
        where_clauses.append("wireless_charge = 1")
    if reverse_charge == 'on':
        where_clauses.append("reverse_charge = 1")
    if support_5g == 'on':
        where_clauses.append("support_5g = 1")
    if gps == 'on':
        where_clauses.append("gps = 1")
    if nfc == 'on':
        where_clauses.append("nfc = 1")
    if ir_port == 'on':
        where_clauses.append("ir_port = 1")
    if volte_support == 'on':
        where_clauses.append("volte_support = 1")
    if face_unlock == 'on':
        where_clauses.append("face_unlock = 1")

    where_sql = ''
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT id, title, image_url, price
        FROM products
        {where_sql}
        {order_by}
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()

    # Получаем опции для фильтров
    filter_options = get_filter_options()

    if 'user_id' in session:
        active_filters = extract_active_filters(request.args)
        if active_filters:
            # сохраняем фильтры в users.filter_history
            save_filter_history(session['user_id'], active_filters)

    # Получаем рекомендации для карусели
    rec_engine = RecommendationEngine()
    
    # Читаем cookie 'recent_views'
    recent_views = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent_views = json.loads(cookie_val)
        except Exception:
            recent_views = []
    
    # Исключаем товары, которые уже показаны в основном списке
    exclude_ids = [p['id'] for p in products]
    
    if 'user_id' in session:
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'], 
            limit=8,
            exclude_ids=exclude_ids,
            recent_views=recent_views
        )
    else:
        recommendations = rec_engine.get_popular_products(limit=8, exclude_ids=exclude_ids)

    return render_template("index.html", 
                         user=user, 
                         products=products, 
                         filter_options=filter_options,
                         recommendations=recommendations)

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        required_fields = ["title", "price", "image_url"]
        all_fields = [
            "title", "description", "price", "image_url", "brand", "os", "release_date",
            "screen_size", "resolution", "screen_type", "refresh_rate", "cpu", "gpu",
            "ram", "rom", "microsd_support", "main_camera", "selfie_camera",
            "optical_stabilization", "video_recording", "battery_capacity",
            "fast_charge", "wireless_charge", "reverse_charge", "support_5g",
            "wifi_version", "bluetooth_version", "gps", "nfc", "ir_port", "sim_type",
            "sim_count", "volte_support", "fingerprint_sensor", "face_unlock",
            "body_material", "ip_protection", "dimensions", "weight", "color",
            "accessories", "interfaces"
        ]

        form_data = request.form.to_dict()

        # Обрізати пробіли зліва і справа для всіх значень
        form_data = {k: v.strip() if isinstance(v, str) else v for k, v in form_data.items()}

        # Перевірка обов'язкових полів
        for field in required_fields:
            if not form_data.get(field):
                return "Помилка: обов'язкові поля не заповнено", 400

        # Додавання одиниць виміру, якщо поле не пусте
        if form_data.get("screen_size"):
            if not form_data["screen_size"].endswith('"'):
                form_data["screen_size"] += '"'

        if form_data.get("dimensions"):
            if not form_data["dimensions"].endswith("мм"):
                form_data["dimensions"] += " мм"

        if form_data.get("weight"):
            if not form_data["weight"].endswith("г"):
                form_data["weight"] += " г"

        if form_data.get("main_camera"):
            if not form_data["main_camera"].endswith("МП"):
                form_data["main_camera"] += " МП"

        if form_data.get("selfie_camera"):
            if not form_data["selfie_camera"].endswith("МП"):
                form_data["selfie_camera"] += " МП"

        # Заповнення відсутніх значень None
        for field in all_fields:
            if field not in form_data:
                form_data[field] = None

        # Далі код збереження у БД, як у тебе було
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (
                title, description, price, image_url, brand, os, release_date,
                screen_size, resolution, screen_type, refresh_rate, cpu, gpu,
                ram, rom, microsd_support, main_camera, selfie_camera,
                optical_stabilization, video_recording, battery_capacity,
                fast_charge, wireless_charge, reverse_charge, support_5g,
                wifi_version, bluetooth_version, gps, nfc, ir_port, sim_type,
                sim_count, volte_support, fingerprint_sensor, face_unlock,
                body_material, ip_protection, dimensions, weight, color,
                accessories, interfaces
            ) VALUES (
                %(title)s, %(description)s, %(price)s, %(image_url)s, %(brand)s,
                %(os)s, %(release_date)s, %(screen_size)s, %(resolution)s,
                %(screen_type)s, %(refresh_rate)s, %(cpu)s, %(gpu)s,
                %(ram)s, %(rom)s, %(microsd_support)s, %(main_camera)s,
                %(selfie_camera)s, %(optical_stabilization)s, %(video_recording)s,
                %(battery_capacity)s, %(fast_charge)s, %(wireless_charge)s,
                %(reverse_charge)s, %(support_5g)s, %(wifi_version)s,
                %(bluetooth_version)s, %(gps)s, %(nfc)s, %(ir_port)s,
                %(sim_type)s, %(sim_count)s, %(volte_support)s,
                %(fingerprint_sensor)s, %(face_unlock)s, %(body_material)s,
                %(ip_protection)s, %(dimensions)s, %(weight)s, %(color)s,
                %(accessories)s, %(interfaces)s
            )
        """, form_data)
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template('add_product.html')


# Добавить эти маршруты в app.py после существующих маршрутов

@app.route('/add-to-wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401
    
    data = request.get_json()
    product_id = int(data.get('product_id'))

    
    if not product_id:
        return jsonify({'success': False, 'error': 'Не вказано ID товару'}), 400
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Получаем текущий вишлист пользователя
    cursor.execute("SELECT wishlist FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return jsonify({'success': False, 'error': 'Користувач не знайдений'}), 404
    
    # Парсим JSON вишлиста или создаем пустой список
    import json
    try:
        wishlist = json.loads(user_data['wishlist']) if user_data['wishlist'] else []
    except:
        wishlist = []
    
    # Проверяем, есть ли уже товар в вишлисте
    if product_id in wishlist:
        conn.close()
        return jsonify({'success': False, 'error': 'Товар вже в вишлисті'}), 400
    
    # Добавляем товар в вишлист
    wishlist.append(product_id)
    
    # Обновляем в БД
    cursor.execute("UPDATE users SET wishlist = %s WHERE id = %s", 
                  (json.dumps(wishlist), session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Товар додано до вишлисту'})


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'success': False, 'error': 'Не вказано ID товару'}), 400
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Получаем текущую корзину пользователя
    cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return jsonify({'success': False, 'error': 'Користувач не знайдений'}), 404
    
    # Парсим JSON корзины или создаем пустой словарь
    import json
    try:
        cart = json.loads(user_data['cart']) if user_data['cart'] else {}
    except:
        cart = {}
    
    # Добавляем товар в корзину (если уже есть - увеличиваем количество)
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    
    # Обновляем в БД
    cursor.execute("UPDATE users SET cart = %s WHERE id = %s", 
                  (json.dumps(cart), session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Товар додано до кошика'})


@app.route('/wishlist')
def wishlist():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Отримати вішлист користувача
    cursor.execute("SELECT wishlist, cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    wishlist_ids = []
    cart_ids = []

    import json
    if user_data:
        wishlist_ids = json.loads(user_data['wishlist']) if user_data['wishlist'] else []
        cart_data = json.loads(user_data['cart']) if user_data['cart'] else {}
        cart_ids = list(map(int, cart_data.keys()))

    # Якщо вішлист не порожній — отримати продукти
    products = []
    if wishlist_ids:
        format_strings = ','.join(['%s'] * len(wishlist_ids))
        cursor.execute(f"SELECT id, title, image_url, price FROM products WHERE id IN ({format_strings})", tuple(wishlist_ids))
        products = cursor.fetchall()

    conn.close()
    return render_template("wishlist.html", user={'username': session.get('username')}, products=products, cart_ids=cart_ids)

@app.route('/remove-from-wishlist', methods=['POST'])
def remove_from_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401

    data = request.get_json()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'success': False, 'error': 'Не вказано ID товару'}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT wishlist FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    import json
    wishlist = json.loads(user_data['wishlist']) if user_data and user_data['wishlist'] else []

    if int(product_id) not in wishlist:
        return jsonify({'success': False, 'error': 'Товар не знайдено у вішлисті'}), 404

    wishlist.remove(int(product_id))
    cursor.execute("UPDATE users SET wishlist = %s WHERE id = %s", (json.dumps(wishlist), session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Товар видалено з вішлисту'})


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Отримати корзину користувача
    cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    cart_items = {}
    products = []
    total_price = 0

    import json
    if user_data and user_data['cart']:
        # Отримуємо словник товарів з cart {product_id: quantity}
        cart_items = json.loads(user_data['cart'])
        
        if cart_items:
            # Получаем информацию о товарах в корзине
            product_ids = list(cart_items.keys())
            format_strings = ','.join(['%s'] * len(product_ids))
            cursor.execute(f"SELECT id, title, image_url, price FROM products WHERE id IN ({format_strings})", 
                         tuple(map(int, product_ids)))
            products_data = cursor.fetchall()
            
            # Добавляем количество к каждому товару и считаем общую стоимость
            for product in products_data:
                product_id = str(product['id'])
                quantity = cart_items[product_id]
                product['quantity'] = quantity
                product['total_price'] = product['price'] * quantity
                total_price += product['total_price']
                products.append(product)

    conn.close()
    return render_template("cart.html", 
                         user={'username': session.get('username')}, 
                         products=products,
                         total_price=total_price)


@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401

    data = request.get_json()
    product_id = str(data.get('product_id'))

    if not product_id:
        return jsonify({'success': False, 'error': 'Не вказано ID товару'}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    import json
    cart = json.loads(user_data['cart']) if user_data and user_data['cart'] else {}

    if product_id not in cart:
        conn.close()
        return jsonify({'success': False, 'error': 'Товар не знайдено у кошику'}), 404

    # Удаляем товар из корзины
    del cart[product_id]
    
    cursor.execute("UPDATE users SET cart = %s WHERE id = %s", (json.dumps(cart), session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Товар видалено з кошика'})


@app.route('/update-cart-quantity', methods=['POST'])
def update_cart_quantity():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401

    data = request.get_json()
    product_id = str(data.get('product_id'))
    new_quantity = int(data.get('quantity', 1))

    if not product_id or new_quantity < 1:
        return jsonify({'success': False, 'error': 'Некоректні дані'}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    import json
    cart = json.loads(user_data['cart']) if user_data and user_data['cart'] else {}

    if product_id not in cart:
        conn.close()
        return jsonify({'success': False, 'error': 'Товар не знайдено у кошику'}), 404

    # Обновляем количество товара
    cart[product_id] = new_quantity
    
    cursor.execute("UPDATE users SET cart = %s WHERE id = %s", (json.dumps(cart), session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Кількість оновлено'})


@app.route('/clear-cart', methods=['POST'])
def clear_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401

    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET cart = %s WHERE id = %s", ('{}', session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Кошик очищено'})


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    user = None
    if 'user_id' in session:
        user = {'username': session.get('username')}
        save_view_history(session['user_id'], product_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Получаем данные о товаре
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return "Товар не знайдено", 404

    # Проверяем, есть ли товар в вишлисте и корзине пользователя
    in_wishlist = False
    in_cart = False

    if user:
        cursor.execute("SELECT wishlist, cart FROM users WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()

        if user_data:
            import json
            # Проверяем вишлист
            if user_data['wishlist']:
                try:
                    wishlist_ids = json.loads(user_data['wishlist'])
                except:
                    wishlist_ids = []
                in_wishlist = product_id in wishlist_ids

            # Проверяем корзину
            if user_data['cart']:
                try:
                    cart_data = json.loads(user_data['cart'])
                except:
                    cart_data = {}
                in_cart = str(product_id) in cart_data

    conn.close()

    # --- cookie recent views (на стороне клиента) ---
    # читаем существующий cookie recent_views, обновляем его (по последним 10)
    import json
    recent = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent = json.loads(cookie_val)
        except:
            recent = []

    # убираем дубли и добавляем текущий id в начало
    if product_id in recent:
        recent.remove(product_id)
    recent.insert(0, product_id)
    recent = recent[:10]

    # формируем ответ с установкой cookie
    response = make_response(render_template("product_detail.html",
                                             user=user,
                                             product=product,
                                             in_wishlist=in_wishlist,
                                             in_cart=in_cart))
    response.set_cookie('recent_views', json.dumps(recent), max_age=30*24*3600, path='/', httponly=False)
    return response



@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Отримуємо корзину користувача
        cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        
        if not user_data or not user_data['cart']:
            return jsonify({'success': False, 'error': 'Кошик порожній'}), 400
        
        import json
        cart_items = json.loads(user_data['cart'])
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Кошик порожній'}), 400
        
        # Отримуємо інформацію про товари та їх ціни
        product_ids = list(cart_items.keys())
        format_strings = ','.join(['%s'] * len(product_ids))
        cursor.execute(f"""
            SELECT id, price 
            FROM products 
            WHERE id IN ({format_strings})
        """, tuple(map(int, product_ids)))
        products = cursor.fetchall()
        
        # Створюємо словник цін
        prices = {str(p['id']): p['price'] for p in products}
        
        # Додаємо записи в purchase_history
        purchase_date = datetime.datetime.now()
        for product_id, quantity in cart_items.items():
            if product_id in prices:
                cursor.execute("""
                    INSERT INTO purchase_history (user_id, product_id, quantity, price, purchase_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session['user_id'], int(product_id), quantity, prices[product_id], purchase_date))
        
        # Оновлюємо поле purchased в таблиці users
        cursor.execute("SELECT purchased FROM users WHERE id = %s", (session['user_id'],))
        user_purchased = cursor.fetchone()
        
        # Парсимо існуючу історію покупок або створюємо нову
        try:
            purchased_history = json.loads(user_purchased['purchased']) if user_purchased['purchased'] else []
        except:
            purchased_history = []
        
        # Додаємо нову покупку до історії
        new_purchase = {
            'date': purchase_date.isoformat(),
            'items': cart_items,
            'total_items': sum(cart_items.values())
        }
        purchased_history.append(new_purchase)
        
        # Оновлюємо purchased і очищаємо корзину
        cursor.execute("""
            UPDATE users 
            SET purchased = %s, cart = '{}' 
            WHERE id = %s
        """, (json.dumps(purchased_history), session['user_id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Замовлення успішно оформлено!'})
        
    except Exception as e:
        conn.rollback()
        print(f"Помилка при оформленні замовлення: {e}")
        return jsonify({'success': False, 'error': 'Помилка при оформленні замовлення'}), 500
    finally:
        conn.close()

@app.route('/purchase-history')
def purchase_history():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Отримуємо історію покупок з purchase_history
    cursor.execute("""
        SELECT ph.*, p.title, p.image_url 
        FROM purchase_history ph
        JOIN products p ON ph.product_id = p.id
        WHERE ph.user_id = %s
        ORDER BY ph.purchase_date DESC
    """, (session['user_id'],))
    
    purchases = cursor.fetchall()
    conn.close()
    
    return render_template('purchase_history.html', 
                         user={'username': session.get('username')}, 
                         purchases=purchases)



def get_user_activity_stats(user_id):
    """
    Собирает статистику активности пользователя для отображения на странице рекомендаций
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT wishlist, cart, purchased, view_history, search_history, filter_history FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    import json
    stats = {
        "wishlist_count": 0,
        "cart_count": 0,
        "purchased_count": 0,
        "views_count": 0,
        "searches_count": 0,
        "filters_count": 0,
    }

    if not user_data:
        return stats

    # wishlist
    try:
        wishlist = json.loads(user_data.get("wishlist") or "[]")
        stats["wishlist_count"] = len(wishlist)
    except:
        pass

    # cart
    try:
        cart = json.loads(user_data.get("cart") or "{}")
        stats["cart_count"] = sum(cart.values()) if isinstance(cart, dict) else len(cart)
    except:
        pass

    # purchased
    try:
        purchased = json.loads(user_data.get("purchased") or "[]")
        stats["purchased_count"] = sum(len(p.get("items", {})) for p in purchased if isinstance(p, dict))
    except:
        pass

    # view_history
    try:
        view_history = json.loads(user_data.get("view_history") or "[]")
        stats["views_count"] = len(view_history)
    except:
        pass

    # search_history
    try:
        search_history = json.loads(user_data.get("search_history") or "[]")
        stats["searches_count"] = len(search_history)
    except:
        pass

    # filter_history
    try:
        filter_history = json.loads(user_data.get("filter_history") or "[]")
        stats["filters_count"] = len(filter_history)
    except:
        pass

    return stats



@app.route('/recommendations')
def recommendations():
    """Улучшенная страница рекомендаций с аналитикой"""
    user = None
    recommendations = []
    user_stats = {}
    
    rec_engine = RecommendationEngine()
    
    # ✅ читаем cookie 'recent_views' (список последних просмотренных id)
    recent_views = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent_views = json.loads(cookie_val)
        except Exception:
            recent_views = []

    if 'user_id' in session:
        user = {'username': session.get('username')}
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'], 
            limit=20,
            exclude_ids=None,
            recent_views=recent_views
        )
        
        user_stats = get_user_activity_stats(session['user_id'])
    else:
        recommendations = rec_engine.get_popular_products(limit=20)
    
    return render_template("recommendations.html", 
                         user=user, 
                         recommendations=recommendations,
                         user_stats=user_stats)





@app.route('/api/recommendations')
def api_recommendations():
    """API для получения рекомендаций"""
    limit = request.args.get('limit', 8, type=int)
    exclude_ids_str = request.args.get('exclude_ids', '')
    exclude_ids = []
    
    if exclude_ids_str:
        try:
            exclude_ids = [int(x.strip()) for x in exclude_ids_str.split(',') if x.strip().isdigit()]
        except:
            exclude_ids = []
    
    rec_engine = RecommendationEngine()
    
    if 'user_id' in session:
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'], 
            limit=limit, 
            exclude_ids=exclude_ids
        )
    else:
        recommendations = rec_engine.get_popular_products(
            limit=limit, 
            exclude_ids=exclude_ids
        )
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })


@app.route('/api/similar-products/<int:product_id>')
def api_similar_products(product_id):
    """API для получения похожих товаров"""
    limit = request.args.get('limit', 6, type=int)
    
    rec_engine = RecommendationEngine()
    similar_products = rec_engine.get_similar_products(product_id, limit)
    
    return jsonify({
        'success': True,
        'products': similar_products
    })

if __name__ == '__main__':
    app.run(debug=True)