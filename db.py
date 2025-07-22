import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="127.127.126.1",
        user="root",
        password="",         
        database="shop_db"
    )
