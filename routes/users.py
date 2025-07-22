from flask import Blueprint, jsonify
from db import get_connection

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
def get_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)
