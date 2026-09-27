# seed_firestore.py
import os
from google.cloud import firestore

# CRITICAL: Hardcode the project ID string.
# On Agent Platform, GOOGLE_CLOUD_PROJECT returns the project NUMBER, which breaks Firestore.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-0d643ff47544"

db = firestore.Client(project=FIRESTORE_PROJECT_ID)

recipes = [
    {
        "id": "recipe-1",
        "title": "Avocado & Tomato Caprese Salad",
        "cuisine": "Italian",
        "prep_time_minutes": 10,
        "calories_per_serving": 250,
        "ingredients": ["Ripe Avocados", "Cherry Tomatoes", "Fresh Mozzarella", "Balsamic Glaze", "Fresh Basil"],
        "instructions": "Slice avocados, tomatoes, and mozzarella. Arrange on a platter, top with fresh basil, and drizzle with balsamic glaze.",
        "dietary_tags": ["Vegetarian", "Gluten-Free", "Quick"]
    },
    {
        "id": "recipe-2",
        "title": "Garlic Butter Salmon with Asparagus",
        "cuisine": "American",
        "prep_time_minutes": 20,
        "calories_per_serving": 420,
        "ingredients": ["Salmon Fillets", "Fresh Asparagus", "Minced Garlic", "Butter", "Lemon Juice"],
        "instructions": "Sear salmon in garlic butter for 4 mins per side. Saute asparagus in the same pan with lemon juice until tender-crisp.",
        "dietary_tags": ["Keto", "High-Protein", "Gluten-Free"]
    },
    {
        "id": "recipe-3",
        "title": "Tofu & Vegetable Green Curry",
        "cuisine": "Thai",
        "prep_time_minutes": 25,
        "calories_per_serving": 380,
        "ingredients": ["Firm Tofu", "Thai Green Curry Paste", "Coconut Milk", "Bell Peppers", "Bamboo Shoots", "Jasmine Rice"],
        "instructions": "Cube tofu and pan-fry until golden. Simmer curry paste with coconut milk, add vegetables and tofu, serve warm over jasmine rice.",
        "dietary_tags": ["Vegan", "Dairy-Free", "Spicy"]
    }
]

def seed():
    print(f"Seeding Firestore collection 'recipes' in project '{FIRESTORE_PROJECT_ID}'...")
    collection_ref = db.collection("recipes")
    for r in recipes:
        doc_id = r["id"]
        collection_ref.document(doc_id).set(r)
        print(f"  - Seeded recipe: {r['title']} (ID: {doc_id})")
    print("Firestore seeding complete! ✅")

if __name__ == "__main__":
    seed()
