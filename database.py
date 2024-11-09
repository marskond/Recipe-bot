# database.py
import sqlite3

def setup_database():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_recipes (
            user_id INTEGER,
            recipe_id INTEGER,
            title TEXT,
            link TEXT,
            note TEXT,
            UNIQUE(user_id, recipe_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ratings (
            user_id INTEGER,
            recipe_id INTEGER,
            rating INTEGER,
            UNIQUE(user_id, recipe_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_recipe(user_id, recipe_id, title, link, note):
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO saved_recipes (user_id, recipe_id, title, link, note) VALUES (?, ?, ?, ?, ?)",
        (user_id, recipe_id, title, link, note)
    )
    conn.commit()
    conn.close()

def save_rating(user_id, recipe_id, rating):
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO recipe_ratings (user_id, recipe_id, rating) VALUES (?, ?, ?)",
        (user_id, recipe_id, rating)
    )
    conn.commit()
    conn.close()