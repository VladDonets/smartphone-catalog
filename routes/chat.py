from flask import Blueprint, request, jsonify, session
import json
import google.generativeai as genai
from db import get_connection

chat_bp = Blueprint('chat', __name__)

# Налаштування Gemini
genai.configure(api_key="AIzaSyDYTlA9IPnGIgxQ5cUE6QtdI5R9ceE1iMs")  # ваш ключ
model = genai.GenerativeModel("gemini-1.5-flash")

from decimal import Decimal

def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # або str(obj), якщо потрібна строка
    raise TypeError

def get_products_context():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, title, brand, os, price, ram, rom, main_camera, 
               battery_capacity, screen_size, color
        FROM products 
        ORDER BY RAND() 
        LIMIT 700
    """)
    products = cursor.fetchall()

    # 🔑 Конвертуємо Decimals у float
    for p in products:
        for key, value in p.items():
            if isinstance(value, Decimal):
                p[key] = float(value)

    cursor.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL LIMIT 10")
    brands = [row['brand'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT os FROM products WHERE os IS NOT NULL")
    os_list = [row['os'] for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'products': products[:20],
        'brands': brands,
        'os_list': os_list,
        'base_url': request.host_url
    }

def get_user_context():
    """Отримує контекст користувача"""
    if 'user_id' not in session:
        return None
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT wishlist, cart, view_history FROM users WHERE id = %s", 
                  (session['user_id'],))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        return None
    
    context = {'user_id': session['user_id']}
    
    try:
        wishlist = json.loads(user_data.get('wishlist') or '[]')
        cart = json.loads(user_data.get('cart') or '{}')
        views = json.loads(user_data.get('view_history') or '[]')
        
        context.update({
            'wishlist_count': len(wishlist),
            'cart_count': len(cart),
            'recent_views': len(views)
        })
    except:
        pass
    
    return context

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Порожнє повідомлення'}), 400
    
    try:
        # Контекст
        products_context = get_products_context()
        user_context = get_user_context()
        
        # Промпт
        system_prompt = f"""
Ти AI-консультант інтернет-магазину смартфонів SmartShop. 

ДОСТУПНІ ТОВАРИ (приклади):
{json.dumps(products_context['products'], ensure_ascii=False, indent=2)}


ДОСТУПНІ БРЕНДИ: {', '.join(products_context['brands'])}
ДОСТУПНІ ОС: {', '.join(products_context['os_list'])}

КОНТЕКСТ КОРИСТУВАЧА: {user_context if user_context else 'Не авторизований'}

ПРАВИЛА:
1. Відповідай коротко і по суті українською мовою
2. Допомагай з вибором за бюджетом і потребами 
3. Задавай уточнюючі питання для кращих рекомендацій П
4. орівнюй товари за характеристиками 
5. Завжди надавай посилання: {products_context['base_url']}product/[ID]
6. Рекомендуй товари з доступного списку
7. Максимум 400 символів у відповіді
"""
        
        # Запит до Gemini API
        response = model.generate_content([
            system_prompt,
            user_message
        ])
        
        ai_message = response.text.strip()
        
        return jsonify({'message': ai_message})
    
    except Exception as e:
        return jsonify({'error': f'Помилка: {str(e)}'}), 500

@chat_bp.route('/api/search-products', methods=['POST'])
def search_products():
    """Пошук товарів для чат-бота"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'products': []})
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
    SELECT id, title, brand, os, price, ram, rom, main_camera, 
           battery_capacity, screen_size, color
    FROM products
    """)

    products = cursor.fetchall()
    conn.close()
    
    return jsonify({'products': products})

