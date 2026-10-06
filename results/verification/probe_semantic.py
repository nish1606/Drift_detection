from backend.detection.semantic_drift import detect_semantic_drift

card_vs_loan = ["credit card", "loan"]
card_current = ["credit card"]
print("card vs loan:", detect_semantic_drift(card_vs_loan, card_current))

similar_phrases = ["fraud detection required", "fraud detection required"]
print("similar phrases:", detect_semantic_drift(similar_phrases, similar_phrases))

identical = ["travel", "grocery"]
print("identical all_pairs:", detect_semantic_drift(identical, identical))
print("identical paired_best_match:", detect_semantic_drift(identical, identical, mode="paired_best_match"))

print("paired on mismatched:", detect_semantic_drift(["travel", "grocery"], ["travel", "grocery", "travel"], mode="paired_best_match"))