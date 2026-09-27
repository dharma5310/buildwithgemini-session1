# app/external_tools.py
import json
import os
import urllib.parse
import urllib.request

def search_external_recipes(query: str = "") -> str:
    """Search global web recipes using TheMealDB public API.
    
    Args:
        query: Recipe or dish name to search for (e.g. 'pasta', 'tacos', 'curry'). If empty, fetches a random recipe.
    """
    try:
        api_key = os.environ.get("THEMEALDB_API_KEY", "1")
        if query.strip():
            encoded = urllib.parse.quote(query.strip())
            url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded}"
        else:
            url = f"https://www.themealdb.com/api/json/v1/{api_key}/random.php"
            
        req = urllib.request.Request(url, headers={"User-Agent": "ChefGemini/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        meals = data.get("meals")
        if not meals:
            return f"No external web recipes found for '{query}'. Try another search query!"
            
        results = []
        for meal in meals[:3]:  # Top 3 results
            name = meal.get("strMeal", "Unknown")
            category = meal.get("strCategory", "General")
            area = meal.get("strArea", "International")
            instructions = meal.get("strInstructions", "").strip()
            if len(instructions) > 250:
                instructions = instructions[:250] + "..."
                
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                measure = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ingredients.append(f"{measure.strip() if measure else ''} {ing.strip()}".strip())
                    
            ing_str = ", ".join(ingredients) if ingredients else "N/A"
            results.append(
                f"Dish: {name}\n"
                f"Category: {category} | Cuisine: {area}\n"
                f"Ingredients: {ing_str}\n"
                f"Instructions: {instructions}"
            )
        return "\n---\n".join(results)
    except Exception as e:
        return f"Error fetching external web recipe: {e}"
