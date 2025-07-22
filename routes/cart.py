from flask import jsonify

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Неавторизований'}), 401

    data = request.get_json()
    product_id = str(data.get('product_id'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cart FROM users WHERE id = %s", (session['user_id'],))
    result = cursor.fetchone()

    cart = []
    if result['cart']:
        cart = result['cart'].split(',')

    cart.append(product_id)  # на відміну від вішлисту, дозволяємо дублікати

    cart_str = ','.join(cart)
    cursor.execute("UPDATE users SET cart = %s WHERE id = %s", (cart_str, session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True})