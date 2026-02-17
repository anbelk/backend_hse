import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.model import DEFAULT_MODEL_PATH

MODEL_PATH = ROOT / DEFAULT_MODEL_PATH


def train_model():
    np.random.seed(42)
    X = np.random.rand(1000, 4)
    y = ((X[:, 0] < 0.3) & (X[:, 1] < 0.2)).astype(int)

    model = LogisticRegression()
    model.fit(X, y)
    return model


def main():
    model = train_model()
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
