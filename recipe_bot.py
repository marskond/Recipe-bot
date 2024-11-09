import sqlite3
import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes


SPOONACULAR_API_KEY = "12313f8e74ba4d3b93ad2980f3135c75"
SPOONACULAR_API_URL = "https://api.spoonacular.com/recipes/complexSearch"

# Создание подключения к базе данных
def setup_database():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Таблица для избранных рецептов с заметками
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
    
    # Таблица для рейтингов рецептов
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

# Функция для поиска рецептов через Spoonacular API
def find_recipes(ingredients="", category=None, calories=None):
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": ingredients,
        "type": category,
        "maxCalories": calories,
        "number": 5  # Количество рецептов для возврата
    }

    response = requests.get(SPOONACULAR_API_URL, params=params)
    
    if response.status_code == 200:
        recipes = response.json().get('results', [])
        return [{"id": recipe["id"], "title": recipe["title"], "link": f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"} for recipe in recipes]
    else:
        return []

# Функция для фильтрации по категории
async def filter_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = ['Breakfast', 'Lunch', 'Dinner', 'Dessert']
    keyboard = [[category] for category in categories]
    
    await update.message.reply_text(
        "Choose a category:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    recipes = find_recipes(category=category)
    
    if recipes:
        await update.message.reply_text(f"Recipes for {category}:")
        for recipe in recipes:
            recipe_title = recipe['title']
            recipe_link = recipe['link']
            await update.message.reply_text(f"{recipe_title}\n{recipe_link}")
    else:
        await update.message.reply_text(f"No recipes found for {category}.")

# Функция для фильтрации по калорийности
async def filter_by_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Please specify the calorie limit. Example: /calories 500")
        return
    
    try:
        calorie_limit = int(context.args[0])
        recipes = find_recipes(calories=calorie_limit)
        
        if recipes:
            await update.message.reply_text(f"Recipes under {calorie_limit} calories:")
            for recipe in recipes:
                recipe_title = recipe['title']
                recipe_link = recipe['link']
                await update.message.reply_text(f"{recipe_title}\n{recipe_link}")
        else:
            await update.message.reply_text("No recipes found within that calorie range.")
    
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a number.")

# Функция для добавления заметки к рецепту
async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /note <recipe_id> <note>")
        return
    
    recipe_id = context.args[0]
    note = " ".join(context.args[1:])
    user_id = update.message.from_user.id
    
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO saved_recipes (user_id, recipe_id, title, link, note) VALUES (?, ?, ?, ?, ?)",
        (user_id, recipe_id, "Sample Title", "Sample Link", note)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text("Note saved successfully.")

# Функция для списка покупок
async def shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipe_id = context.args[0] if context.args else None
    ingredients = ["Sample Ingredient 1", "Sample Ingredient 2"]  # Здесь должен быть реальный список ингредиентов
    
    await update.message.reply_text("Shopping List:\n" + "\n".join(ingredients))

# Функция для рейтинга рецептов
async def rate_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /rate <recipe_id> <rating>")
        return

    recipe_id = context.args[0]
    rating = int(context.args[1])
    user_id = update.message.from_user.id
    
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO recipe_ratings (user_id, recipe_id, rating) VALUES (?, ?, ?)",
        (user_id, recipe_id, rating)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text("Rating saved successfully.")

# Главная функция запуска бота
def main():
    setup_database()
    application = ApplicationBuilder().token("7793938959:AAFcCJyvsMAUtr5zDCK2khs6aMqACrSPguY").build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("filter", filter_by_category))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection))
    application.add_handler(CommandHandler("calories", filter_by_calories))
    application.add_handler(CommandHandler("note", add_note))
    application.add_handler(CommandHandler("shopping_list", shopping_list))
    application.add_handler(CommandHandler("rate", rate_recipe))
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
