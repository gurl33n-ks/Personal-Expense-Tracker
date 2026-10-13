from pathlib import Path
import json
import random
import re
from collections import defaultdict

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "transactions.parquet"
MODEL_DIR = BASE_DIR / "models"
MODEL_FILE = MODEL_DIR / "expense_classifier.joblib"
REPORT_FILE = MODEL_DIR / "evaluation.json"

# Only map clearly compatible dataset categories.
# Unmatched categories are excluded from training.
CATEGORY_MAP = {
    "Food & Dining": "Food",
    "Transportation": "Transport",
    "Shopping & Retail": "Shopping",
    "Entertainment & Recreation": "Entertainment",
    "Healthcare & Medical": "Health",
    "Utilities & Services": "Bills",
}

MAX_PER_CATEGORY = 2000
RANDOM_SEED = 42


def clean_text(value):
    if not isinstance(value, str):
        return ""

    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def load_training_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset missing: {DATA_FILE}\n"
            "Download the Parquet dataset first."
        )

    rng = random.Random(RANDOM_SEED)

    samples = defaultdict(list)
    seen = defaultdict(int)

    parquet = pq.ParquetFile(DATA_FILE)

    columns = [
        "transaction_description",
        "category",
    ]

    # Read batches to avoid loading millions
    # of records into memory at once.
    for batch in parquet.iter_batches(
        batch_size=10000,
        columns=columns
    ):
        frame = batch.to_pandas()

        for row in frame.itertuples(index=False):
            description = clean_text(
                row.transaction_description
            )

            category = CATEGORY_MAP.get(row.category)

            if not category or len(description) < 3:
                continue

            seen[category] += 1
            bucket = samples[category]

            # Reservoir sampling provides a bounded,
            # randomized sample from the full dataset.
            if len(bucket) < MAX_PER_CATEGORY:
                bucket.append(description)
            else:
                position = rng.randrange(seen[category])

                if position < MAX_PER_CATEGORY:
                    bucket[position] = description

    rows = [
        {
            "description": description,
            "category": category,
        }
        for category, descriptions in samples.items()
        for description in descriptions
    ]

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError(
            "No compatible categories found. "
            "Check the dataset schema and labels."
        )

    # Avoid duplicate descriptions appearing
    # in both training and evaluation.
    ambiguous = (
        df.groupby("description")["category"]
        .nunique()
    )

    ambiguous = set(
        ambiguous[ambiguous > 1].index
    )

    df = df[
        ~df["description"].isin(ambiguous)
    ].drop_duplicates(
        subset=["description", "category"]
    )

    if df["category"].nunique() < 2:
        raise ValueError(
            "Not enough categories to train a classifier."
        )

    return df.reset_index(drop=True)


def train():
    MODEL_DIR.mkdir(exist_ok=True)

    df = load_training_data()

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.2,
        random_state=RANDOM_SEED,
    )

    train_idx, test_idx = next(
        splitter.split(
            df,
            df["category"],
            groups=df["description"],
        )
    )

    train_df = df.iloc[train_idx]
    test_df = df.iloc[test_idx]

    missing = (
        set(CATEGORY_MAP.values())
        - set(train_df["category"])
    )

    if missing:
        raise ValueError(
            f"Missing training categories: {missing}"
        )

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 4),
                max_features=20000,
                sublinear_tf=True,
            ),
        ),
        (
            "classifier",
            MultinomialNB(alpha=0.5),
        ),
    ])

    model.fit(
        train_df["description"],
        train_df["category"],
    )

    predicted = model.predict(
        test_df["description"]
    )

    accuracy = accuracy_score(
        test_df["category"],
        predicted,
    )

    weighted_f1 = f1_score(
        test_df["category"],
        predicted,
        average="weighted",
        zero_division=0,
    )

    report = classification_report(
        test_df["category"],
        predicted,
        zero_division=0,
        output_dict=True,
    )

    results = {
        "dataset_records_used": int(len(df)),
        "training_records": int(len(train_df)),
        "test_records": int(len(test_df)),
        "accuracy": float(np.round(accuracy, 4)),
        "weighted_f1": float(
            np.round(weighted_f1, 4)
        ),
        "classification_report": report,
    }

    joblib.dump(model, MODEL_FILE)

    REPORT_FILE.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print("\nMODEL TRAINING COMPLETE")
    print("-----------------------")
    print(f"Records: {len(df)}")
    print(f"Training: {len(train_df)}")
    print(f"Testing: {len(test_df)}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"Weighted F1: {weighted_f1:.3f}")
    print("\nSaved model:", MODEL_FILE)
    print("Saved report:", REPORT_FILE)

if __name__ == "__main__":
    train()
    
# ----------------------------------------
# DATASET-TRAINED MODEL INTEGRATION
# ----------------------------------------

from pathlib import Path
import joblib

_original_predict_category = predict_category

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "expense_classifier.joblib"
)

_trained_model = None


def predict_category(description):
    """
    Use the dataset-trained classifier if available.
    Otherwise use the existing demo classifier.
    """

    global _trained_model

    if not isinstance(description, str):
        raise ValueError("Invalid description.")

    description = description.strip()

    if len(description) < 3:
        raise ValueError(
            "Please enter a longer description."
        )

    if not MODEL_PATH.exists():
        return _original_predict_category(description)

    if _trained_model is None:
        _trained_model = joblib.load(MODEL_PATH)

    category = str(
        _trained_model.predict([description])[0]
    )

    probabilities = _trained_model.predict_proba(
        [description]
    )[0]

    confidence = float(max(probabilities))

    return {
        "category": category,
        "confidence": round(confidence, 3),
    }