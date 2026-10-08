from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Small demonstration training dataset.
# Add more representative examples for better predictions.

TRAINING_DATA = {
    "Food": [
        "pizza for dinner",
        "ordered burger and fries",
        "restaurant bill",
        "lunch at cafe",
        "morning breakfast",
        "grocery shopping",
        "bought vegetables and fruits",
        "coffee and sandwich",
        "milk and bread",
        "food delivery order",
        "dinner at restaurant",
        "snacks and juice",
    ],

    "Transport": [
        "uber ride to college",
        "ola cab booking",
        "metro ticket",
        "bus fare",
        "petrol for car",
        "diesel refill",
        "train ticket",
        "auto rickshaw fare",
        "taxi ride",
        "parking charges",
        "fuel for bike",
        "airport cab",
    ],

    "Shopping": [
        "bought new shoes",
        "shopping for clothes",
        "ordered jeans online",
        "purchased handbag",
        "new laptop accessories",
        "bought headphones",
        "shopping mall purchase",
        "purchased sunglasses",
        "new dress",
        "mobile phone cover",
        "bought cosmetics",
        "online clothing order",
    ],

    "Bills": [
        "electricity bill payment",
        "monthly wifi bill",
        "internet recharge",
        "mobile recharge",
        "water bill",
        "gas cylinder payment",
        "house rent",
        "phone bill",
        "broadband subscription",
        "utility payment",
        "maintenance charges",
        "monthly electricity charges",
    ],

    "Entertainment": [
        "movie tickets",
        "netflix subscription",
        "spotify premium",
        "concert ticket",
        "gaming subscription",
        "amusement park",
        "cinema booking",
        "music festival",
        "video game purchase",
        "bowling night",
        "streaming subscription",
        "theme park entry",
    ],

    "Health": [
        "doctor consultation",
        "hospital visit",
        "pharmacy medicines",
        "medical checkup",
        "dental appointment",
        "health insurance premium",
        "blood test",
        "medicine purchase",
        "clinic consultation",
        "eye examination",
        "prescription tablets",
        "physiotherapy session",
    ],

    "Other": [
        "charity donation",
        "birthday gift",
        "miscellaneous purchase",
        "office stationery",
        "printing documents",
        "college project materials",
        "postal charges",
        "courier service",
        "pet supplies",
        "household repair",
        "unexpected expense",
        "general supplies",
    ],
}

descriptions = []
labels = []

for category, examples in TRAINING_DATA.items():
    descriptions.extend(examples)
    labels.extend([category] * len(examples))

# TF-IDF converts descriptions to numerical features.
# Naive Bayes learns patterns associated with categories.

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            analyzer="char_wb",
            ngram_range=(2, 4)
        )
    ),
    (
        "classifier",
        MultinomialNB(alpha=0.5)
    )
])

model.fit(descriptions, labels)


def predict_category(description):
    """Return a category suggestion for an expense."""

    description = description.strip()

    if len(description) < 3:
        raise ValueError(
            "Please enter a longer description."
        )

    prediction = model.predict([description])[0]

    probabilities = model.predict_proba(
        [description]
    )[0]

    confidence = float(max(probabilities))

    return {
        "category": str(prediction),
        "confidence": round(confidence, 3)
    }