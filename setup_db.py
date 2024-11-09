import sqlite3

def setup_database():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Создаём таблицу для сохранения рецептов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_recipes (
            user_id INTEGER,
            recipe_id INTEGER,
            title TEXT,
            link TEXT,
            UNIQUE(user_id, recipe_id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database setup complete.")

setup_database()