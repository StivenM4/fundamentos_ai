from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import make_pipeline


RANDOM_STATE = 42
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "tickets_soporte.csv"
TARGETS = ["categoria", "prioridad", "incidente"]

data = pd.read_csv(DATA_PATH)
X = data["texto"]
y = data[TARGETS]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=RANDOM_STATE,
    stratify=y["categoria"],
)

model = make_pipeline(
    TfidfVectorizer(strip_accents="unicode"),
    MultiOutputClassifier(
        LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    ),
)

model.fit(X_train, y_train)
pred = model.predict(X_test)

print(f"Muestras entrenamiento: {len(X_train)}")
print(f"Muestras prueba: {len(X_test)}")

for index, target in enumerate(TARGETS):
    expected = y_test[target]
    precision, recall, f1, _ = precision_recall_fscore_support(
        expected,
        pred[:, index],
        average="macro",
        zero_division=0,
    )
    print(f"\n{target.capitalize()}:")
    print(f"Accuracy: {accuracy_score(expected, pred[:, index]):.3f}")
    print(f"Precisión macro: {precision:.3f}")
    print(f"Recall macro: {recall:.3f}")
    print(f"F1 macro: {f1:.3f}")
    print("Matriz de confusión:")
    print(confusion_matrix(expected, pred[:, index]))
