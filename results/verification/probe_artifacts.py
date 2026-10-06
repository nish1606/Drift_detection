import joblib
from pathlib import Path

store = Path("ml_model/artifacts")
for p in sorted(store.glob("*.joblib")):
    print(p.name, p.stat().st_size)
print()
meta = store / "model_meta.pkl"
if meta.exists():
    print("model_meta:", joblib.load(meta))
print()
src = Path("results/verification/train_and_publish.py")
print(src.read_text()[:1800] if src.exists() else "no train_and_publish.py")