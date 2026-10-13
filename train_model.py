
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

# Load preprocessed dataset from this project folder
PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "cleaned_dataset.csv"
if not DATA_PATH.is_file():
    raise FileNotFoundError(f"{DATA_PATH} not found. Run preprocess.py or run_pipeline.py first.")
df = pd.read_csv(DATA_PATH)

# Separate target
y = df["label"].astype(int)

# Use numeric features only
# Exclude URL and other text columns
X = df.drop(
    columns=["label", "URL", "Domain", "TLD", "FILENAME"],
    errors="ignore"
)

X = X.select_dtypes(include=np.number)
X = X.replace([np.inf, -np.inf], np.nan)
X = X.dropna(axis=1, how="all")

# Remove constant columns
X = X.loc[:, X.nunique(dropna=True) > 1]

print("Dataset size:", X.shape)
print("Label distribution:")
print(y.value_counts())

# Check that training is possible
if X.shape[1] == 0:
    raise ValueError("No usable numeric feature columns remain after cleaning.")
if y.nunique() < 2:
    raise ValueError("Training requires both label classes (0=phishing, 1=legitimate).")

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Models to compare
models = {
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ),
    "Extra Trees": ExtraTreesClassifier(
        n_estimators=200,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ),
    "Gradient Boosting": HistGradientBoostingClassifier(
        max_iter=150,
        random_state=42
    )
}

# Cross-validation on training data only
cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

best_model = None
best_name = ""
best_score = -1

for name, classifier in models.items():
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        classifier
    )

    scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=cv,
        scoring="f1",
        n_jobs=1
    )

    print(name, "Cross-validation F1:", round(scores.mean(), 4))

    if scores.mean() > best_score:
        best_score = scores.mean()
        best_model = model
        best_name = name

# Train the best model
best_model.fit(X_train, y_train)

# Evaluate on unseen test data
predictions = best_model.predict(X_test)

print("\nBest model:", best_name)
print("Test accuracy:", round(accuracy_score(y_test, predictions) * 100, 2), "%")
print("Test F1-score:", round(f1_score(y_test, predictions), 4))

print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    labels=[0, 1],
    target_names=["Phishing", "Legitimate"],
    zero_division=0
))

print("Confusion matrix:")
print(confusion_matrix(y_test, predictions, labels=[0, 1]))

# Save model and feature order
joblib.dump(
    {
        "model": best_model,
        "features": X.columns.tolist()
    },
    PROJECT_DIR / "scam_detection_model.pkl"
)

print(f"\nModel saved as {PROJECT_DIR / 'scam_detection_model.pkl'}")
