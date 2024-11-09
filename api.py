# api.py
import aiohttp
from config import SPOONACULAR_API_KEY, SPOONACULAR_API_URL

async def find_recipes(ingredients="", category=None, calories=None):
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": ingredients,
        "type": category,
        "maxCalories": calories,
        "number": 5
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SPOONACULAR_API_URL, params=params) as response:
            if response.status == 200:
                recipes = await response.json()
                return [
                    {
                        "id": recipe["id"],
                        "title": recipe["title"],
                        "link": f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"
                    } for recipe in recipes.get('results', [])
                ]
            return []