import sqlite3

def get_db_connection():
    return sqlite3.connect("tickets.db", check_same_thread=False)
