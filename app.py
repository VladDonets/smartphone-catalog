from flask import Blueprint, Flask, jsonify, render_template, session, request, redirect, make_response
import json
import datetime
from db import get_connection
from routes.auth import auth_bp
from routes.users import users_bp
from routes.chat import chat_bp
from recommendation_engine import RecommendationEngine

app = Flask(__name__)
app.secret_key = 'your-secret-key'

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(chat_bp)


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
    user = None
    if 'user_id' in session:
        user = {
            'username': session.get('username'),
            'id': session.get('user_id') 
        }

    # Параметри сортування та пошуку
    sort = request.args.get('sort', '')
    search_query = request.args.get('q', '').strip()
    if search_query and 'user_id' in session:
        save_search_history(session['user_id'], search_query)

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

    # Boolean фільтри 
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

    # SQL для сортування
    order_by = ""
    if sort == 'title_asc':
        order_by = "ORDER BY title ASC"
    elif sort == 'title_desc':
        order_by = "ORDER BY title DESC"
    elif sort == 'price_asc':
        order_by = "ORDER BY price ASC"
    elif sort == 'price_desc':
        order_by = "ORDER BY price DESC"

    # WHERE умови
    where_clauses = []
    params = {}

    if search_query:
        where_clauses.append("title LIKE %(search)s")
        params['search'] = f"%{search_query}%"

    # Текстові фільтри
    text_filters = {
        'brand': brand, 'os': os_, 'screen_type': screen_type, 'refresh_rate': refresh_rate,
        'ram': ram, 'rom': rom, 'video_recording': video_recording, 'wifi_version': wifi_version,
        'bluetooth_version': bluetooth_version, 'sim_type': sim_type, 'fingerprint_sensor': fingerprint_sensor,
        'body_material': body_material, 'ip_protection': ip_protection, 'color': color
    }
    
    for field, value in text_filters.items():
        if value:
            where_clauses.append(f"{field} = %({field})s")
            params[field] = value
    
    # Числовий фільтр sim_count
    if sim_count:
        where_clauses.append("sim_count = %(sim_count)s")
        params['sim_count'] = int(sim_count)

    # Boolean фільтри (1 = True в БД)
    boolean_filters = {
        'microsd_support': microsd_support, 'optical_stabilization': optical_stabilization,
        'wireless_charge': wireless_charge, 'reverse_charge': reverse_charge, 'support_5g': support_5g,
        'gps': gps, 'nfc': nfc, 'ir_port': ir_port, 'volte_support': volte_support, 'face_unlock': face_unlock
    }
    
    for field, value in boolean_filters.items():
        if value == 'on':
            where_clauses.append(f"{field} = 1")

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
    
    # Рекомендації
    rec_engine = RecommendationEngine()
    recent_views = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent_views = json.loads(cookie_val)
        except:
            recent_views = []
    
    if 'user_id' in session:
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'], 
            limit=12,
            exclude_ids=None,
            recent_views=recent_views
        )
        for rec in recommendations:
            log_recommendation_event(session['user_id'], rec['id'], "shown", "catalog_page")
    else:
        recommendations = rec_engine.get_popular_products(limit=12)
    
    conn.close()

    filter_options = get_filter_options()

    if 'user_id' in session:
        active_filters = extract_active_filters(request.args)
        if active_filters:
            save_filter_history(session['user_id'], active_filters)

    return render_template("index.html", 
                         user=user, 
                         products=products, 
                         filter_options=filter_options,
                         recommendations=recommendations)



def get_filter_options():
    """Отримуємо унікальні значення для фільтрів з БД"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    filter_options = {}
    
    # Поля для фільтрації
    fields_to_check = [
        'brand', 'os', 'screen_type', 'refresh_rate', 'ram', 'rom',
        'video_recording', 'wifi_version', 'bluetooth_version', 'sim_type',
        'sim_count', 'fingerprint_sensor', 'body_material', 'ip_protection', 'color'
    ]
    
    for field in fields_to_check:
        # Для sim_count використовуємо DISTINCT з CAST до VARCHAR для сортування
        if field == 'sim_count':
            cursor.execute(f"SELECT DISTINCT {field} FROM products WHERE {field} IS NOT NULL ORDER BY {field}")
        else:
            cursor.execute(f"SELECT DISTINCT {field} FROM products WHERE {field} IS NOT NULL AND {field} != '' ORDER BY {field}")
        filter_options[field] = [row[field] for row in cursor.fetchall()]
    
    conn.close()
    return filter_options


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
    
    cursor.execute("SELECT wishlist FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return jsonify({'success': False, 'error': 'Користувач не знайдений'}), 404

    import json
    try:
        wishlist = json.loads(user_data['wishlist']) if user_data['wishlist'] else []
    except:
        wishlist = []

    if product_id in wishlist:
        conn.close()
        return jsonify({'success': False, 'error': 'Товар вже в вишлисті'}), 400
    
    wishlist.append(product_id)
    
    cursor.execute("UPDATE users SET wishlist = %s WHERE id = %s", 
                  (json.dumps(wishlist), session['user_id']))
    conn.commit()
    conn.close()
    
    # Log the wishlist event
    log_recommendation_event(session['user_id'], product_id, "wishlisted", "user_action")
    
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
    
    cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return jsonify({'success': False, 'error': 'Користувач не знайдений'}), 404

    import json
    try:
        cart = json.loads(user_data['cart']) if user_data['cart'] else {}
    except:
        cart = {}

    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    
    cursor.execute("UPDATE users SET cart = %s WHERE id = %s", 
                  (json.dumps(cart), session['user_id']))
    conn.commit()
    conn.close()
    
    # Log cart event
    log_recommendation_event(session['user_id'], product_id, "added_to_cart", "user_action")
    
    return jsonify({'success': True, 'message': 'Товар додано до кошика'})


@app.route('/wishlist')
def wishlist():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT wishlist, cart FROM users WHERE id = %s", (session['user_id'],))
    user_data = cursor.fetchone()

    wishlist_ids = []
    cart_ids = []

    import json
    if user_data:
        wishlist_ids = json.loads(user_data['wishlist']) if user_data['wishlist'] else []
        cart_data = json.loads(user_data['cart']) if user_data['cart'] else {}
        cart_ids = list(map(int, cart_data.keys()))

    # отримати продукти
    products = []
    if wishlist_ids:
        format_strings = ','.join(['%s'] * len(wishlist_ids))
        cursor.execute(f"SELECT id, title, image_url, price FROM products WHERE id IN ({format_strings})", tuple(wishlist_ids))
        products = cursor.fetchall()

    # Рекомендації
    from recommendation_engine import RecommendationEngine
    rec_engine = RecommendationEngine()

    recommendations = rec_engine.get_user_recommendations(
        session['user_id'],
        limit=12,
        exclude_ids=wishlist_ids
    )

    conn.close()

    return render_template(
        "wishlist.html",
        user={
            'username': session.get('username'),
            'id': session.get('user_id')
        },
        products=products,
        cart_ids=cart_ids,
        recommendations=recommendations)

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
        cart_items = json.loads(user_data['cart'])
        
        if cart_items:
            product_ids = list(cart_items.keys())
            format_strings = ','.join(['%s'] * len(product_ids))
            cursor.execute(f"SELECT id, title, image_url, price FROM products WHERE id IN ({format_strings})", 
                         tuple(map(int, product_ids)))
            products_data = cursor.fetchall()
            
            for product in products_data:
                product_id = str(product['id'])
                quantity = cart_items[product_id]
                product['quantity'] = quantity
                product['total_price'] = product['price'] * quantity
                total_price += product['total_price']
                products.append(product)

    # Рекомендации
    rec_engine = RecommendationEngine()
    recent_views = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent_views = json.loads(cookie_val)
        except:
            recent_views = []

    if 'user_id' in session:
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'], 
            limit=12,
            exclude_ids=list(map(int, cart_items.keys())) if cart_items else None,
            recent_views=recent_views
        )
    else:
        recommendations = rec_engine.get_popular_products(limit=12)

    conn.close()
    return render_template("cart.html", 
                         user={
                             'username': session.get('username'),
                             'id': session.get('user_id')
                         },
                         products=products,
                         total_price=total_price,
                         recommendations=recommendations)



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
        user = {
            'username': session.get('username'),
            'id': session.get('user_id')  # Add this line
        }
        save_view_history(session['user_id'], product_id)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return "Товар не знайдено", 404

    in_wishlist = False
    in_cart = False

    if user:
        cursor.execute("SELECT wishlist, cart FROM users WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        if user_data:
            import json
            if user_data['wishlist']:
                try:
                    wishlist_ids = json.loads(user_data['wishlist'])
                except:
                    wishlist_ids = []
                in_wishlist = product_id in wishlist_ids
            if user_data['cart']:
                try:
                    cart_data = json.loads(user_data['cart'])
                except:
                    cart_data = {}
                in_cart = str(product_id) in cart_data

    # Рекомендации
    from recommendation_engine import RecommendationEngine
    rec_engine = RecommendationEngine()
    import json

    recent_views = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent_views = json.loads(cookie_val)
        except:
            recent_views = []

    if 'user_id' in session:
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'],
            limit=12,
            exclude_ids=[product_id],
            recent_views=recent_views
        )
        for rec in recommendations:
            log_recommendation_event(session['user_id'], rec['id'], "shown", "product_page")
    else:
        # если пользователь не залогинен — просто популярные
        recommendations = rec_engine.get_popular_products(limit=12, exclude_ids=[product_id])

    conn.close()

    # cookie
    recent = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent = json.loads(cookie_val)
        except:
            recent = []
    if product_id in recent:
        recent.remove(product_id)
    recent.insert(0, product_id)
    recent = recent[:10]

    response = make_response(render_template("product_detail.html",
                                             user=user,
                                             product=product,
                                             in_wishlist=in_wishlist,
                                             in_cart=in_cart,
                                             recommendations=recommendations))
    response.set_cookie('recent_views', json.dumps(recent), max_age=30*24*3600, path='/', httponly=False)
    return response


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Необхідно авторизуватися'}), 401
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user's cart
        cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        
        if not user_data or not user_data['cart']:
            return jsonify({'success': False, 'error': 'Кошик порожній'}), 400
        
        import json
        cart_items = json.loads(user_data['cart'])
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Кошик порожній'}), 400
        
        # Get product information and prices
        product_ids = list(cart_items.keys())
        format_strings = ','.join(['%s'] * len(product_ids))
        cursor.execute(f"""
            SELECT id, price 
            FROM products 
            WHERE id IN ({format_strings})
        """, tuple(map(int, product_ids)))
        products = cursor.fetchall()
        
        prices = {str(p['id']): p['price'] for p in products}
        
        purchase_date = datetime.datetime.now()
        
        # Process each item in cart
        for product_id, quantity in cart_items.items():
            if product_id in prices:
                # Add to purchase history
                cursor.execute("""
                    INSERT INTO purchase_history (user_id, product_id, quantity, price, purchase_date)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (session['user_id'], int(product_id), quantity, prices[product_id], purchase_date))
                
                # Log purchase event
                log_recommendation_event(session['user_id'], int(product_id), "purchased", "checkout")
        
        # Update user's purchased history
        cursor.execute("SELECT purchased FROM users WHERE id = %s", (session['user_id'],))
        user_purchased = cursor.fetchone()
        
        try:
            purchased_history = json.loads(user_purchased['purchased']) if user_purchased['purchased'] else []
        except:
            purchased_history = []
        
        # Add new purchase to history
        new_purchase = {
            'date': purchase_date.isoformat(),
            'items': cart_items,
            'total_items': sum(cart_items.values())
        }
        purchased_history.append(new_purchase)
        
        # Clear cart and update purchased history
        cursor.execute("""
            UPDATE users 
            SET purchased = %s, cart = '{}' 
            WHERE id = %s
        """, (json.dumps(purchased_history), session['user_id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Замовлення успішно оформлено!'})
        
    except Exception as e:
        conn.rollback()
        print(f"Error during checkout: {e}")
        return jsonify({'success': False, 'error': 'Помилка при оформленні замовлення'}), 500
    finally:
        conn.close()


@app.route('/purchase-history')
def purchase_history():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
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
    
    recent_views = []
    cookie_val = request.cookies.get('recent_views')
    if cookie_val:
        try:
            recent_views = json.loads(cookie_val)
        except Exception:
            recent_views = []

    if 'user_id' in session:
        user = {
            'username': session.get('username'),
            'id': session.get('user_id')
        }
        recommendations = rec_engine.get_user_recommendations(
            session['user_id'], 
            limit=20,
            exclude_ids=None,
            recent_views=recent_views
        )
        for rec in recommendations:
            log_recommendation_event(session['user_id'], rec['id'], "shown", "recommendations_page")
        
        user_stats = get_user_activity_stats(session['user_id'])
    else:
        recommendations = rec_engine.get_popular_products(limit=20)
    
    return render_template("recommendations.html", 
                         user=user, 
                         recommendations=recommendations,
                         user_stats=user_stats)


@app.route('/track-recommendation-event', methods=['POST'])
def track_recommendation_event():
    """Відстеження рекомендаціїї"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    product_id = data.get('product_id')
    event_type = data.get('event_type')
    source = data.get('source', 'unknown')
    
    event_type_mapping = {
        'added_to_cart': 'cart_add',
        'wishlisted': 'wishlist',
        'removed_from_wishlist': 'wishlist_remove'
    }

    event_type = event_type_mapping.get(event_type, event_type)
    
    # Validate required parameters
    if not product_id or not event_type:
        return jsonify({'success': False, 'error': 'Missing product_id or event_type'}), 400
    
    # Validate event_type
    valid_events = ['shown', 'clicked', 'wishlisted', 'added_to_cart', 'purchased', 'removed_from_wishlist']
    if event_type not in valid_events:
        return jsonify({'success': False, 'error': f'Invalid event_type. Must be one of: {valid_events}'}), 400
    
    try:
        # Log the event
        log_recommendation_event(session['user_id'], product_id, event_type, source)
        return jsonify({'success': True, 'message': 'Event logged successfully'})
    except Exception as e:
        print(f"Error logging recommendation event: {e}")
        return jsonify({'success': False, 'error': 'Failed to log event'}), 500



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


@app.route('/admin/stats')
def admin_stats():
    # if 'user_id' not in session or session.get('username') != 'admin':
    #     return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    cursor.execute("SELECT COUNT(*) as total_products FROM products")
    total_products = cursor.fetchone()['total_products']

    cursor.execute("SELECT COUNT(*) as total_orders FROM purchase_history")
    total_orders = cursor.fetchone()['total_orders']

    cursor.execute("SELECT SUM(price*quantity) as total_revenue FROM purchase_history")
    total_revenue = cursor.fetchone()['total_revenue'] or 0

    # Топ бренди
    cursor.execute("SELECT brand, COUNT(*) as cnt FROM products GROUP BY brand ORDER BY cnt DESC LIMIT 5")
    top_brands = cursor.fetchall()

    # Топ товари
    cursor.execute("""
        SELECT p.title, SUM(ph.quantity) as sold 
        FROM purchase_history ph
        JOIN products p ON p.id = ph.product_id
        GROUP BY ph.product_id ORDER BY sold DESC LIMIT 5
    """)
    top_products = cursor.fetchall()

    # Пошуки
    cursor.execute("SELECT search_history FROM users WHERE search_history IS NOT NULL")
    all_searches = []
    for row in cursor.fetchall():
        try:
            import json
            history = json.loads(row['search_history'])
            all_searches.extend([h['query'] for h in history])
        except:
            pass
    from collections import Counter
    top_searches = Counter(all_searches).most_common(5)

    # ВСІ фільтри
    cursor.execute("SELECT filter_history FROM users WHERE filter_history IS NOT NULL")
    all_filters = []
    for row in cursor.fetchall():
        try:
            import json
            history = json.loads(row['filter_history'])
            for h in history:
                for k, v in h.get("filters", {}).items():
                    all_filters.append(f"{k}:{v}")
        except:
            pass
    filter_counts = Counter(all_filters)  # без .most_common(), беремо все

    # Продані смартфони (усі)
    cursor.execute("""
        SELECT p.title, SUM(ph.quantity) as sold
        FROM purchase_history ph
        JOIN products p ON p.id = ph.product_id
        GROUP BY ph.product_id ORDER BY sold DESC
    """)
    sold_products = cursor.fetchall()

    # Статистика рекомендацій
    cursor.execute("""
    SELECT 
        -- Унікальні користувачі, які бачили рекомендації
        COUNT(DISTINCT CASE WHEN event_type = 'shown' THEN user_id END) as users_with_recs,
        -- Унікальні користувачі, які взаємодіяли з рекомендаціями
        COUNT(DISTINCT CASE WHEN event_type IN ('clicked', 'purchased', 'wishlisted', 'added_to_cart') 
              THEN user_id END) as engaged_users,
        -- Загальна кількість взаємодій
        COUNT(CASE WHEN event_type = 'clicked' THEN 1 END) as total_clicks,
        COUNT(CASE WHEN event_type = 'purchased' THEN 1 END) as total_purchases,
        COUNT(CASE WHEN event_type = 'wishlisted' THEN 1 END) as total_wishlisted,
        COUNT(CASE WHEN event_type = 'added_to_cart' THEN 1 END) as total_cart_adds
        FROM recommendation_logs
        """)
    
    rec_result = cursor.fetchone()
    
    # User engagement rate (скільки користувачів взаємодіяли з рекомендаціями)
    user_engagement_rate = round((rec_result['engaged_users'] / rec_result['users_with_recs'] * 100), 2) if rec_result['users_with_recs'] > 0 else 0
    
    # Purchase conversion від кліків
    purchase_conversion = round((rec_result['total_purchases'] / rec_result['total_clicks'] * 100), 2) if rec_result['total_clicks'] > 0 else 0
    
    rec_stats = {
        'users_with_recs': rec_result['users_with_recs'],
        'engaged_users': rec_result['engaged_users'],
        'user_engagement_rate': user_engagement_rate,
        'clicked': rec_result['total_clicks'],
        'purchased': rec_result['total_purchases'],
        'wishlisted': rec_result['total_wishlisted'],
        'cart_adds': rec_result['total_cart_adds'],
        'purchase_conversion': purchase_conversion
    }

    # Замовлення по датах
    cursor.execute("""
        SELECT DATE(purchase_date) as date, 
               COUNT(*) as orders, 
               SUM(price * quantity) as revenue 
        FROM purchase_history 
        GROUP BY DATE(purchase_date) 
        ORDER BY date DESC LIMIT 30
    """)
    orders_by_date = cursor.fetchall()

    # Рекомендації по датах
    cursor.execute("""
        SELECT DATE(created_at) as date,
               SUM(CASE WHEN event_type = 'shown' THEN 1 ELSE 0 END) as shown,
               SUM(CASE WHEN event_type = 'clicked' THEN 1 ELSE 0 END) as clicked,
               SUM(CASE WHEN event_type = 'purchased' THEN 1 ELSE 0 END) as purchased
        FROM recommendation_logs
        GROUP BY date
        ORDER BY date DESC LIMIT 30
    """)
    rec_by_date = cursor.fetchall()

    conn.close()

    return render_template("admin_stats.html",
                           user={'username': session.get('username')},
                           total_users=total_users,
                           total_products=total_products,
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           top_brands=top_brands,
                           top_products=top_products,
                           top_searches=top_searches,
                           filter_counts=filter_counts,
                           sold_products=sold_products,
                           orders_by_date=orders_by_date,
                           rec_stats=rec_stats,
                           rec_by_date=rec_by_date)



@app.route('/track-recommendation-click', methods=['POST'])
def track_recommendation_click():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    source = data.get('source', None)

    if not product_id:
        return jsonify({'success': False, 'error': 'Немає product_id'}), 400

    log_recommendation_event(session['user_id'], int(product_id), "clicked", source)
    return jsonify({'success': True})

@app.route('/log_recommendation_event', methods=['POST'])
def log_recommendation_event_route():
    """Маршрут для логування подій рекомендаційної системи з frontend"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Користувач не авторизований'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Відсутні дані'}), 400
        
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        event_type = data.get('event_type')
        source = data.get('source', 'unknown')
        
        # Перевірка обов'язкових полів
        if not all([user_id, product_id, event_type]):
            return jsonify({'success': False, 'error': 'Відсутні обов\'язкові поля'}), 400
        
        # Перевірка, що user_id збігається з поточною сесією
        if int(user_id) != session['user_id']:
            return jsonify({'success': False, 'error': 'Невірний користувач'}), 403
        
        # Перевірка валідності event_type
        valid_events = ['shown', 'clicked', 'wishlisted', 'added_to_cart', 'purchased', 'removed_from_wishlist']
        if event_type not in valid_events:
            return jsonify({'success': False, 'error': f'Невалідний тип події. Дозволені: {valid_events}'}), 400
        
        # Перевірка існування товару
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Товар не знайдено'}), 404
        
        # Логування події
        success = log_recommendation_event(user_id, product_id, event_type, source)
        conn.close()
        
        if success:
            return jsonify({'success': True, 'message': 'Подія успішно залогована'})
        else:
            return jsonify({'success': False, 'error': 'Помилка при логуванні'}), 500
            
    except Exception as e:
        print(f"Помилка в log_recommendation_event_route: {e}")
        return jsonify({'success': False, 'error': 'Внутрішня помилка сервера'}), 500
    

def log_recommendation_event(user_id, product_id, event_type, source=None):
    """Розширена функція реєстрації подій рекомендацій (update якщо вже існує shown)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Перевірка наявності товару
        cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cursor.fetchone():
            print(f"⚠️ Warning: Product {product_id} not found")
            conn.close()
            return False

        if event_type == "shown":
            # Шукаємо чи вже є запис
            cursor.execute("""
                SELECT id FROM recommendation_logs 
                WHERE user_id = %s AND product_id = %s AND event_type = 'shown'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, product_id))
            existing = cursor.fetchone()

            if existing:
                # Якщо є — оновлюємо час і source
                cursor.execute("""
                    UPDATE recommendation_logs
                    SET created_at = NOW(), source = %s
                    WHERE id = %s
                """, (source, existing[0]))
            else:
                # Якщо немає — створюємо новий
                cursor.execute("""
                    INSERT INTO recommendation_logs (user_id, product_id, event_type, source, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (user_id, product_id, event_type, source))
        else:
            # Для інших подій завжди новий запис
            cursor.execute("""
                INSERT INTO recommendation_logs (user_id, product_id, event_type, source, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, product_id, event_type, source))

        conn.commit()
        conn.close()

        print(f"✅ Event logged: user={user_id}, product={product_id}, event={event_type}, source={source}")
        return True

    except Exception as e:
        print(f"❌ Error logging recommendation event: {e}")
        if 'conn' in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False




if __name__ == '__main__':
    app.run(debug=True)
