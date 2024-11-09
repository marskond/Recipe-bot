import os
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from datetime import datetime, timedelta


TELEGRAM_TOKEN = '7793938959:AAFcCJyvsMAUtr5zDCK2khs6aMqACrSPguY'
SPOONACULAR_API_KEY = '12313f8e74ba4d3b93ad2980f3135c75'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'
RANDOM_RECIPE_URL = 'https://api.spoonacular.com/recipes/random'
RECIPE_DIET_URL = 'https://api.spoonacular.com/recipes/complexSearch'

# Функция для поиска рецептов по ингредиентам
def find_recipes(ingredients, num_results=5):
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'ingredients': ingredients,
        'number': num_results,
        'ranking': 1
    }
    response = requests.get(SPOONACULAR_URL, params=params)
    return response.json()

# Функция для получения случайного рецепта
def get_random_recipe():
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'number': 1  # Получаем только один рецепт
    }
    response = requests.get(RANDOM_RECIPE_URL, params=params)
    return response.json()

# Функция для поиска рецептов по типу блюда (завтрак, обед, ужин и т.д.)
def find_recipe_by_type(meal_type, num_results=5):
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'type': meal_type,
        'number': num_results
    }
    response = requests.get(SPOONACULAR_URL, params=params)
    return response.json()

# Функция для поиска рецептов по диете (например, веганская, безглютеновая)
def find_recipe_by_diet(diet_type, num_results=5):
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'diet': diet_type,
        'number': num_results
    }
    response = requests.get(RECIPE_DIET_URL, params=params)
    return response.json()

# Функция для добавления рецепта в базу данных
def save_recipe_to_db(user_id, recipe_id, title, link):
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO saved_recipes (user_id, recipe_id, title, link)
        VALUES (?, ?, ?, ?)
    ''', (user_id, recipe_id, title, link))
    conn.commit()
    conn.close()

# Функция для получения сохранённых рецептов
def get_saved_recipes(user_id):
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT title, link FROM saved_recipes WHERE user_id = ?', (user_id,))
    recipes = cursor.fetchall()
    conn.close()
    return recipes

# Функция для удаления рецепта из базы данных
def delete_recipe_from_db(user_id, recipe_id):
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM saved_recipes WHERE user_id = ? AND recipe_id = ?
    ''', (user_id, recipe_id))
    conn.commit()
    conn.close()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I can help you find recipes by ingredients, meal type, diet, and more.\n\n"
        "Commands:\n"
        "/saved - View saved recipes\n"
        "/recommend - Get daily recipe recommendations\n"
        "/random - Get a random recipe\n"
        "/clear - Clear saved recipes\n"
        "/meal - Find recipes by meal type (e.g., breakfast, lunch, dinner)\n"
        "/diet - Find recipes by diet type (e.g., vegan, gluten-free, keto)\n"
        "/info - Get information about the bot\n"
        "/help - Get help with bot usage"
    )

# Обработчик команды /saved для отображения сохранённых рецептов
async def view_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    saved_recipes = get_saved_recipes(user_id)

    if not saved_recipes:
        await update.message.reply_text("You have no saved recipes.")
    else:
        message = "Your saved recipes:\n\n"
        for title, link in saved_recipes:
            message += f"• [{title}]({link})\n"
        await update.message.reply_text(message, parse_mode='Markdown')

# Обработчик команды /recommend для ежедневных рекомендаций
async def recommend_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recommended_ingredients = "chicken, rice, tomato"
    recipes = find_recipes(recommended_ingredients, num_results=1)

    if recipes:
        recipe = recipes[0]
        recipe_title = recipe['title']
        recipe_id = recipe['id']
        recipe_link = f"https://spoonacular.com/recipes/{recipe_title.replace(' ', '-')}-{recipe_id}"
        await update.message.reply_text(
            f"Today's recommended recipe:\n\n*{recipe_title}*\n[View Recipe]({recipe_link})",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("No recommendations available at the moment.")

# Обработчик команды /random для случайного рецепта
async def random_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipe_data = get_random_recipe()
    
    if recipe_data:
        recipe = recipe_data['recipes'][0]
        recipe_title = recipe['title']
        recipe_id = recipe['id']
        recipe_link = f"https://spoonacular.com/recipes/{recipe_title.replace(' ', '-')}-{recipe_id}"
        await update.message.reply_text(
            f"Here's a random recipe for you!\n\n*{recipe_title}*\n[View Recipe]({recipe_link})",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Could not fetch a random recipe at the moment.")

# Обработчик команды /clear для очистки сохранённых рецептов
async def clear_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM saved_recipes WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("All your saved recipes have been cleared.")

# Обработчик команды /meal для поиска рецептов по типу блюда
async def find_by_meal_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meal_type = ' '.join(context.args).lower()
    if not meal_type:
        await update.message.reply_text("Please provide a meal type (e.g., breakfast, lunch, dinner).")
        return

    recipes = find_recipe_by_type(meal_type)

    if not recipes:
        await update.message.reply_text(f"No {meal_type} recipes found.")
        return

    message = f"Here are some {meal_type} recipes:\n\n"
    for recipe in recipes:
        recipe_title = recipe['title']
        recipe_id = recipe['id']
        recipe_link = f"https://spoonacular.com/recipes/{recipe_title.replace(' ', '-')}-{recipe_id}"
        message += f"• [{recipe_title}]({recipe_link})\n"

    await update.message.reply_text(message, parse_mode='Markdown')

# Обработчик команды /diet для поиска рецептов по диете
async def find_by_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diet_type = ' '.join(context.args).lower()
    if not diet_type:
        await update.message.reply_text("Please provide a diet type (e.g., vegan, gluten-free, keto).")
        return

    recipes = find_recipe_by_diet(diet_type)

    if not recipes:
        await update.message.reply_text(f"No {diet_type} recipes found.")
        return

    message = f"Here are some {diet_type} recipes:\n\n"
    for recipe in recipes:
        recipe_title = recipe['title']
        recipe_id = recipe['id']
        recipe_link = f"https://spoonacular.com/recipes/{recipe_title.replace(' ', '-')}-{recipe_id}"
        message += f"• [{recipe_title}]({recipe_link})\n"

    await update.message.reply_text(message, parse_mode='Markdown')

# Обработчик команды /help для получения справки по использованию бота
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "Here are the commands you can use:\n"
        "/start - Start the bot\n"
        "/saved - View saved recipes\n"
        "/recommend - Get daily recipe recommendations\n"
        "/random - Get a random recipe\n"
        "/clear - Clear saved recipes\n"
        "/meal <meal_type> - Find recipes by meal type (e.g., breakfast, lunch, dinner)\n"
        "/diet <diet_type> - Find recipes by diet type (e.g., vegan, gluten-free, keto)\n"
        "/info - Get information about the bot\n"
        "/help - Get help with bot usage"
    )
    await update.message.reply_text(help_message)

# Инициализация базы данных (если ещё не создана)
def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_recipes (
            user_id INTEGER,
            recipe_id INTEGER,
            title TEXT,
            link TEXT,
            PRIMARY KEY (user_id, recipe_id)
        )
    ''')
    conn.commit()
    conn.close()

# Запуск бота
async def main():
    init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("saved", view_saved))
    application.add_handler(CommandHandler("recommend", recommend_recipe))
    application.add_handler(CommandHandler("random", random_recipe))
    application.add_handler(CommandHandler("clear", clear_saved))
    application.add_handler(CommandHandler("meal", find_by_meal_type))
    application.add_handler(CommandHandler("diet", find_by_diet))
    application.add_handler(CommandHandler("help", help))

    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
