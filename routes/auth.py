from flask import Blueprint, request, jsonify
from db import get_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Всі поля обовʼязкові'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, password)
    )
    user_id = cursor.lastrowid  # Получаем ID нового пользователя
    conn.commit()
    conn.close()

    # Автоматически авторизуем пользователя после регистрации
    session['user_id'] = user_id
    session['username'] = username
    
    return jsonify({
        'message': 'Реєстрація успішна', 
        'user': {'id': user_id, 'username': username}
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    from flask import session
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s AND password_hash = %s", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'message': 'Вхід успішний', 'user': {'id': user['id'], 'username': user['username']}})
    else:
        return jsonify({'error': 'Невірний email або пароль'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    from flask import session
    session.clear()
    return jsonify({'message': 'Вихід виконано'})
