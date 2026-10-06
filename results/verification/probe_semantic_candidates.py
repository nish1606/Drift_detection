from backend.detection.semantic_drift import detect_semantic_drift

candidates = [
    ("card vs loan", ["credit card"], ["loan"]),
    ("card+loan vs card", ["credit card", "loan"], ["credit card"]),
    ("card+loan vs loan", ["credit card", "loan"], ["loan"]),
    ("card+loan vs card+loan", ["credit card", "loan"], ["credit card", "loan"]),
    ("card vs card+loan", ["credit card"], ["credit card", "loan"]),
    ("loan vs card+loan", ["loan"], ["credit card", "loan"]),
    ("fraud vs fraudulent", ["fraud"], ["fraudulent"]),
    ("fraud detection vs fraud detection", ["fraud detection required"], ["fraud detection required"]),
    ("travel vs grocery", ["travel"], ["grocery"]),
    ("travel+grocery vs travel+grocery", ["travel", "grocery"], ["travel", "grocery"]),
    ("travel+grocery vs travel", ["travel", "grocery"], ["travel"]),
    ("travel+grocery vs grocery", ["travel", "grocery"], ["grocery"]),
    ("credit card transaction vs loan application", ["credit card transaction"], ["loan application"]),
    ("online purchase vs loan", ["online purchase"], ["loan"]),
    ("merchant travel vs merchant grocery", ["merchant travel"], ["merchant grocery"]),
]
for label, ref, cur in candidates:
    print(f"{label:38s} all_pairs={detect_semantic_drift(ref, cur):.6f}  paired={detect_semantic_drift(ref, cur, mode='paired_best_match'):.6f}")