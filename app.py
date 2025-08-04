from flask import Flask, jsonify, render_template, session, request, redirect
import json
from db import get_connection
from routes.auth import auth_bp
from routes.users import users_bp

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


@app.route("/")
def index():
    user = None
    if 'user_id' in session:
        user = {'username': session.get('username')}

    # Отримуємо параметри сортування і пошуку
    sort = request.args.get('sort', '')
    search_query = request.args.get('q', '').strip()

    # Фільтри з параметрів GET
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
    
    # Boolean фільтри (checkbox)
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

    # Формуємо SQL для сортування
    order_by = ""
    if sort == 'title_asc':
        order_by = "ORDER BY title ASC"
    elif sort == 'title_desc':
        order_by = "ORDER BY title DESC"
    elif sort == 'price_asc':
        order_by = "ORDER BY price ASC"
    elif sort == 'price_desc':
        order_by = "ORDER BY price DESC"

    # Формуємо умови WHERE
    where_clauses = []
    params = {}

    if search_query:
        where_clauses.append("title LIKE %(search)s")
        params['search'] = f"%{search_query}%"

    # Текстові фільтри
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

    # Boolean фільтри (checkbox)
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

    # Отримуємо опції для фільтрів
    filter_options = get_filter_options()

    

    return render_template("index.html", user=user, products=products, filter_options=filter_options)


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


if __name__ == '__main__':
    app.run(debug=True)