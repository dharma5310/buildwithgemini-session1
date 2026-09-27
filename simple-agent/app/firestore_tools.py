# app/firestore_tools.py
from google.cloud import firestore

# CRITICAL: Hardcode project ID as a string.
# On Agent Platform, reading GOOGLE_CLOUD_PROJECT or google.auth.default() returns project number, breaking Firestore.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-0d643ff47544"

db = firestore.Client(project=FIRESTORE_PROJECT_ID)

def get_recipes(cuisine: str = None, dietary_tag: str = None) -> str:
    """Fetch recipes from the Firestore 'recipes' collection.
    
    Args:
        cuisine: Optional filter by cuisine (e.g. 'Italian', 'Thai', 'American').
        dietary_tag: Optional filter by dietary preference (e.g. 'Vegan', 'Keto', 'Gluten-Free').
    """
    try:
        collection_ref = db.collection("recipes")
        docs = list(collection_ref.stream())
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            
            if cuisine and data.get("cuisine", "").lower() != cuisine.lower():
                continue
            if dietary_tag and not any(tag.lower() == dietary_tag.lower() for tag in data.get("dietary_tags", [])):
                continue
                
            results.append(data)
            
        if not results:
            return "No matching recipes found in the database."
            
        summary = []
        for r in results:
            tags = ", ".join(r.get("dietary_tags", []))
            summary.append(
                f"ID: {r.get('id')}\n"
                f"Title: {r.get('title')}\n"
                f"Cuisine: {r.get('cuisine')}\n"
                f"Prep Time: {r.get('prep_time_minutes')} mins | Calories: {r.get('calories_per_serving')} kcal\n"
                f"Dietary Tags: {tags}\n"
                f"Ingredients: {', '.join(r.get('ingredients', []))}\n"
                f"Instructions: {r.get('instructions')}\n"
            )
        return "\n---\n".join(summary)
    except Exception as e:
        return f"Error reading recipes from Firestore: {e}"

def get_recipe_by_id(recipe_id: str) -> str:
    """Retrieve details for a specific recipe from Firestore by its ID.
    
    Args:
        recipe_id: The unique document ID of the recipe (e.g. 'recipe-1').
    """
    try:
        doc_ref = db.collection("recipes").document(recipe_id)
        doc = doc_ref.get()
        if not doc.exists:
            return f"Recipe with ID '{recipe_id}' not found."
            
        data = doc.to_dict()
        tags = ", ".join(data.get("dietary_tags", []))
        return (
            f"ID: {data.get('id')}\n"
            f"Title: {data.get('title')}\n"
            f"Cuisine: {data.get('cuisine')}\n"
            f"Prep Time: {data.get('prep_time_minutes')} mins | Calories: {data.get('calories_per_serving')} kcal\n"
            f"Dietary Tags: {tags}\n"
            f"Ingredients:\n" + "\n".join(f"- {ing}" for tag in [data.get('ingredients', [])] for ing in tag) + "\n\n"
            f"Instructions:\n{data.get('instructions')}"
        )
    except Exception as e:
        return f"Error retrieving recipe '{recipe_id}': {e}"

def add_recipe(
    title: str,
    cuisine: str,
    prep_time_minutes: int,
    calories_per_serving: int,
    ingredients: list[str],
    instructions: str,
    dietary_tags: list[str] = None
) -> str:
    """Add a new recipe to the Firestore 'recipes' collection.
    
    Args:
        title: Title of the dish.
        cuisine: Cuisine style (e.g., 'Mexican', 'Indian', 'Mediterranean').
        prep_time_minutes: Preparation time in minutes.
        calories_per_serving: Approximate calories per serving.
        ingredients: List of ingredient strings.
        instructions: Step-by-step cooking instructions.
        dietary_tags: List of dietary tags (e.g., ['Vegetarian', 'Gluten-Free']).
    """
    try:
        collection_ref = db.collection("recipes")
        docs = list(collection_ref.stream())
        doc_id = f"recipe-{len(docs) + 1}"
        
        recipe_data = {
            "id": doc_id,
            "title": title,
            "cuisine": cuisine,
            "prep_time_minutes": prep_time_minutes,
            "calories_per_serving": calories_per_serving,
            "ingredients": ingredients,
            "instructions": instructions,
            "dietary_tags": dietary_tags or []
        }
        
        collection_ref.document(doc_id).set(recipe_data)
        return f"Successfully added recipe '{title}' to Firestore with ID: {doc_id}! ✅"
    except Exception as e:
        return f"Error adding recipe to Firestore: {e}"

def get_pantry_inventory() -> str:
    """Fetch current ingredient inventory from the Firestore 'pantry' collection."""
    try:
        docs = list(db.collection("pantry").stream())
        if not docs:
            return "Your pantry is currently empty."
        
        items = []
        for doc in docs:
            data = doc.to_dict()
            name = data.get("item_name", doc.id)
            qty = data.get("quantity", "")
            unit = data.get("unit", "")
            items.append(f"- {name}: {qty} {unit}".strip())
            
        return "Current Pantry Inventory:\n" + "\n".join(items)
    except Exception as e:
        return f"Error reading pantry inventory from Firestore: {e}"

def update_pantry_item(item_name: str, quantity: str, unit: str = "") -> str:
    """Add or update an ingredient item in the Firestore 'pantry' collection.
    
    Args:
        item_name: Name of the ingredient (e.g., 'Eggs', 'Flour', 'Olive Oil').
        quantity: Quantity amount (e.g., '6', '2', '500').
        unit: Optional unit of measurement (e.g., 'pcs', 'lbs', 'ml').
    """
    try:
        doc_id = item_name.lower().strip().replace(" ", "_")
        doc_ref = db.collection("pantry").document(doc_id)
        
        pantry_data = {
            "item_name": item_name.strip(),
            "quantity": quantity.strip(),
            "unit": unit.strip()
        }
        
        doc_ref.set(pantry_data, merge=True)
        unit_str = f" {unit.strip()}" if unit else ""
        return f"Updated pantry: '{item_name}' set to {quantity}{unit_str}! 🛒"
    except Exception as e:
        return f"Error updating pantry item '{item_name}': {e}"

