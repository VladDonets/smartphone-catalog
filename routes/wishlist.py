from flask import jsonify

@app.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'Неавторизований'}), 401

    data = request.get_json()
    product_id = str(data.get('product_id'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT wishlist FROM users WHERE id = %s", (session['user_id'],))
    result = cursor.fetchone()

    wishlist = []
    if result['wishlist']:
        wishlist = result['wishlist'].split(',')

    if product_id not in wishlist:
        wishlist.append(product_id)

    wishlist_str = ','.join(wishlist)
    cursor.execute("UPDATE users SET wishlist = %s WHERE id = %s", (wishlist_str, session['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True})
