# bot.py
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from api import find_recipes
from database import setup_database, save_recipe, save_rating

async def filter_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = ['Breakfast', 'Lunch', 'Dinner', 'Dessert']
    keyboard = [[category] for category in categories]
    await update.message.reply_text(
        "Choose a category:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    recipes = await find_recipes(category=category)
    if recipes:
        await update.message.reply_text(f"Recipes for {category}:")
        for recipe in recipes:
            await update.message.reply_text(f"{recipe['title']}\n{recipe['link']}")
    else:
        await update.message.reply_text(f"No recipes found for {category}.")

async def filter_by_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        calorie_limit = int(context.args[0])
        recipes = await find_recipes(calories=calorie_limit)
        if recipes:
            await update.message.reply_text(f"Recipes under {calorie_limit} calories:")
            for recipe in recipes:
                await update.message.reply_text(f"{recipe['title']}\n{recipe['link']}")
        else:
            await update.message.reply_text("No recipes found within that calorie range.")
    except (ValueError, IndexError):
        await update.message.reply_text("Please specify a valid calorie limit. Example: /calories 500")

async def add_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /note <recipe_id> <note>")
        return
    recipe_id = context.args[0]
    note = " ".join(context.args[1:])
    user_id = update.message.from_user.id
    save_recipe(user_id, recipe_id, "Sample Title", "Sample Link", note)
    await update.message.reply_text("Note saved successfully.")

async def rate_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /rate <recipe_id> <rating>")
        return
    recipe_id = context.args[0]
    try:
        rating = int(context.args[1])
        save_rating(update.message.from_user.id, recipe_id, rating)
        await update.message.reply_text("Rating saved successfully.")
    except ValueError:
        await update.message.reply_text("Rating must be a number.")

def main():
    setup_database()
    application = ApplicationBuilder().token("7793938959:AAFcCJyvsMAUtr5zDCK2khs6aMqACrSPguY").build()
    application.add_handler(CommandHandler("filter", filter_by_category))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection))
    application.add_handler(CommandHandler("calories", filter_by_calories))
    application.add_handler(CommandHandler("note", add_note_command))
    application.add_handler(CommandHandler("rate", rate_recipe))
    application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())