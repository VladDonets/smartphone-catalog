import json
from collections import defaultdict
from db import get_connection


class RecommendationEngine:
    def __init__(self):
        self.weights = {
            'purchase': 10,
            'cart': 8,
            'wishlist': 6,
            'view': 3,
            'search': 2,
            'filter': 1
        }

    def get_user_recommendations(self, user_id, limit=10, exclude_ids=None, recent_views=None):
        """
        Получаем персонализированные рекомендации для пользователя
        """
        if exclude_ids is None:
            exclude_ids = []
        if recent_views is None:
            recent_views = []

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                return self.get_popular_products(limit, exclude_ids)

            user_preferences = self._analyze_user_preferences(
                user_id, user_data, cursor, recent_views=recent_views
            )

            recommendations = self._generate_recommendations(
                user_preferences, cursor, limit, exclude_ids
            )

            if len(recommendations) < limit:
                popular = self.get_popular_products(
                    limit - len(recommendations),
                    exclude_ids + [r['id'] for r in recommendations]
                )
                recommendations.extend(popular)

            return recommendations[:limit]
        finally:
            conn.close()

    def _analyze_user_preferences(self, user_id, user_data, cursor, recent_views=None):
        """
        Анализируем предпочтения пользователя на основе JSON-полей в users
        и списка recent_views из cookie.
        """
        if recent_views is None:
            recent_views = []

        preferences = {
            'brands': defaultdict(int),
            'os': defaultdict(int),
            'price_ranges': [],
            'features': defaultdict(int),
            'categories': defaultdict(int),
            'colors': defaultdict(int)
        }

        # ---------- Покупки ----------
        try:
            purchased = json.loads(user_data.get('purchased') or '[]')
        except json.JSONDecodeError:
            purchased = []

        qty_by_id = defaultdict(int)
        for entry in purchased:
            items = entry.get('items') or {}
            for pid_str, qty in items.items():
                try:
                    pid = int(pid_str)
                    qty_by_id[pid] += int(qty)
                except Exception:
                    continue

        if qty_by_id:
            format_strings = ','.join(['%s'] * len(qty_by_id))
            cursor.execute(
                f"SELECT * FROM products WHERE id IN ({format_strings})",
                tuple(qty_by_id.keys())
            )
            for product in cursor.fetchall():
                weight = self.weights['purchase'] * qty_by_id.get(product['id'], 1)
                self._update_preferences(preferences, product, weight)

        # ---------- Корзина ----------
        try:
            cart = json.loads(user_data.get('cart') or '{}')
        except json.JSONDecodeError:
            cart = {}

        if cart:
            product_ids = list(cart.keys())
            format_strings = ','.join(['%s'] * len(product_ids))
            cursor.execute(
                f"SELECT * FROM products WHERE id IN ({format_strings})",
                tuple(map(int, product_ids))
            )
            for product in cursor.fetchall():
                q = int(cart.get(str(product['id']), 1))
                weight = self.weights['cart'] * q
                self._update_preferences(preferences, product, weight)

        # ---------- Вишлист ----------
        try:
            wishlist_ids = json.loads(user_data.get('wishlist') or '[]')
        except json.JSONDecodeError:
            wishlist_ids = []

        if wishlist_ids:
            format_strings = ','.join(['%s'] * len(wishlist_ids))
            cursor.execute(
                f"SELECT * FROM products WHERE id IN ({format_strings})",
                tuple(wishlist_ids)
            )
            for product in cursor.fetchall():
                self._update_preferences(preferences, product, self.weights['wishlist'])

        # ---------- История просмотров ----------
        try:
            view_history = json.loads(user_data.get('view_history') or '[]')
        except json.JSONDecodeError:
            view_history = []

        view_ids = [vh.get('product_id') for vh in view_history if isinstance(vh, dict) and vh.get('product_id')]
        for rid in recent_views:
            if isinstance(rid, int) and rid not in view_ids:
                view_ids.append(rid)

        if view_ids:
            format_strings = ','.join(['%s'] * len(view_ids))
            cursor.execute(
                f"SELECT * FROM products WHERE id IN ({format_strings})",
                tuple(map(int, view_ids))
            )
            for product in cursor.fetchall():
                self._update_preferences(preferences, product, self.weights['view'])

        # ---------- Поиск ----------
        try:
            search_history = json.loads(user_data.get('search_history') or '[]')
        except json.JSONDecodeError:
            search_history = []

        queries = [s.get('query', '') for s in search_history if isinstance(s, dict)]
        if queries:
            cursor.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != ''")
            brand_list = [b['brand'] for b in cursor.fetchall()]
            for q in queries:
                ql = str(q).lower()
                for brand in brand_list:
                    if brand and brand.lower() in ql:
                        preferences['brands'][brand] += self.weights['search']

        # ---------- Фильтры ----------
        try:
            filter_history = json.loads(user_data.get('filter_history') or '[]')
        except json.JSONDecodeError:
            filter_history = []

        for fh in filter_history:
            f = fh.get('filters') or {}
            if f.get('brand'):
                preferences['brands'][f['brand']] += self.weights['filter']
            if f.get('os'):
                preferences['os'][f['os']] += self.weights['filter']
            if f.get('color'):
                preferences['colors'][f['color']] += self.weights['filter']

            for bf in [
                'microsd_support', 'optical_stabilization', 'wireless_charge',
                'reverse_charge', 'support_5g', 'gps', 'nfc', 'ir_port',
                'volte_support', 'face_unlock'
            ]:
                if str(f.get(bf, '')).lower() in ('1', 'true', 'on', 'yes'):
                    preferences['features'][bf] += self.weights['filter']

            if f.get('ram'):
                try:
                    ram_int = self._extract_number(f['ram'])
                    if ram_int >= 12:
                        preferences['categories']['high_performance'] += self.weights['filter']
                    elif ram_int >= 8:
                        preferences['categories']['mid_performance'] += self.weights['filter']
                except Exception:
                    pass

        return preferences

    def _update_preferences(self, preferences, product, weight):
        if product.get('brand'):
            preferences['brands'][product['brand']] += weight

        if product.get('os'):
            preferences['os'][product['os']] += weight

        if product.get('price') is not None:
            preferences['price_ranges'].append(float(product['price']))

        if product.get('color'):
            preferences['colors'][product['color']] += weight

        boolean_features = [
            'microsd_support', 'optical_stabilization', 'wireless_charge',
            'reverse_charge', 'support_5g', 'gps', 'nfc', 'ir_port',
            'volte_support', 'face_unlock'
        ]
        for feature in boolean_features:
            if product.get(feature) == 1:
                preferences['features'][feature] += weight

        if product.get('ram'):
            ram_int = self._extract_number(product['ram'])
            if ram_int >= 12:
                preferences['categories']['high_performance'] += weight
            elif ram_int >= 8:
                preferences['categories']['mid_performance'] += weight

        if product.get('main_camera'):
            camera_mp = self._extract_number(product['main_camera'])
            if camera_mp >= 100:
                preferences['categories']['photography'] += weight

    def _extract_number(self, text):
        import re
        if not text:
            return 0
        numbers = re.findall(r'\d+', str(text))
        return int(numbers[0]) if numbers else 0

    def _generate_recommendations(self, preferences, cursor, limit, exclude_ids):
        recommendations = []

        exclude_condition = ""
        if exclude_ids:
            exclude_condition = f"AND id NOT IN ({','.join(map(str, exclude_ids))})"

        # бренды
        top_brands = sorted(preferences['brands'].items(), key=lambda x: x[1], reverse=True)[:3]
        for brand, _ in top_brands:
            cursor.execute(f"""
                SELECT *, RAND() as rand_score 
                FROM products 
                WHERE brand = %s {exclude_condition}
                ORDER BY rand_score
                LIMIT 3
            """, (brand,))
            recommendations.extend(cursor.fetchall())

        # ОС
        top_os = sorted(preferences['os'].items(), key=lambda x: x[1], reverse=True)[:2]
        for os, _ in top_os:
            cursor.execute(f"""
                SELECT *, RAND() as rand_score 
                FROM products 
                WHERE os = %s {exclude_condition}
                ORDER BY rand_score
                LIMIT 2
            """, (os,))
            recommendations.extend(cursor.fetchall())

        # Цена
        if preferences['price_ranges']:
            avg_price = sum(preferences['price_ranges']) / len(preferences['price_ranges'])
            min_price = avg_price * 0.7
            max_price = avg_price * 1.3
            cursor.execute(f"""
                SELECT *, RAND() as rand_score 
                FROM products 
                WHERE price BETWEEN %s AND %s {exclude_condition}
                ORDER BY rand_score
                LIMIT 3
            """, (min_price, max_price))
            recommendations.extend(cursor.fetchall())

        # Особенности
        top_features = sorted(preferences['features'].items(), key=lambda x: x[1], reverse=True)[:3]
        for feature, _ in top_features:
            cursor.execute(f"""
                SELECT *, RAND() as rand_score 
                FROM products 
                WHERE {feature} = 1 {exclude_condition}
                ORDER BY rand_score
                LIMIT 2
            """)
            recommendations.extend(cursor.fetchall())

        # Убираем дубли
        seen_ids = set()
        unique_recommendations = []
        for product in recommendations:
            if product['id'] not in seen_ids:
                seen_ids.add(product['id'])
                unique_recommendations.append(product)

        return unique_recommendations[:limit]

    def get_popular_products(self, limit=10, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = []

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            exclude_condition = ""
            params = []
            if exclude_ids:
                exclude_condition = f"WHERE p.id NOT IN ({','.join(['%s']*len(exclude_ids))})"
                params.extend(exclude_ids)

            try:
                cursor.execute(f"""
                    SELECT p.*, 
                           COALESCE(ph.count, 0) * 10 AS popularity_score
                    FROM products p
                    LEFT JOIN (
                        SELECT product_id, COUNT(*) AS count
                        FROM purchase_history
                        GROUP BY product_id
                    ) ph ON p.id = ph.product_id
                    {exclude_condition}
                    ORDER BY popularity_score DESC, RAND()
                    LIMIT %s
                """, params + [limit])
                return cursor.fetchall()
            except Exception:
                order_sql = "ORDER BY release_date DESC"
                cursor.execute(f"""
                    SELECT * FROM products
                    {('WHERE id NOT IN (' + ','.join(['%s']*len(exclude_ids)) + ')') if exclude_ids else ''}
                    {order_sql}
                    LIMIT %s
                """, (exclude_ids + [limit]) if exclude_ids else [limit])
                rows = cursor.fetchall()
                if rows:
                    return rows
                cursor.execute(f"""
                    SELECT * FROM products
                    {('WHERE id NOT IN (' + ','.join(['%s']*len(exclude_ids)) + ')') if exclude_ids else ''}
                    ORDER BY RAND()
                    LIMIT %s
                """, (exclude_ids + [limit]) if exclude_ids else [limit])
                return cursor.fetchall()
        finally:
            conn.close()

    def get_similar_products(self, product_id, limit=6):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if not product:
                return []

            conditions = []
            params = []

            if product.get('brand'):
                conditions.append("brand = %s")
                params.append(product['brand'])

            if product.get('os'):
                conditions.append("os = %s")
                params.append(product['os'])

            if product.get('price'):
                price = float(product['price'])
                conditions.append("price BETWEEN %s AND %s")
                params.extend([price * 0.7, price * 1.3])

            where_clause = " OR ".join(conditions) if conditions else "1=1"

            cursor.execute(f"""
                SELECT *, RAND() as rand_score
                FROM products 
                WHERE id != %s AND ({where_clause})
                ORDER BY rand_score
                LIMIT %s
            """, [product_id] + params + [limit])

            return cursor.fetchall()
        finally:
            conn.close()

    def save_current_session_filters(self, user_id, filters):
        """no-op: фильтры сохраняются в users.filter_history"""
        return
