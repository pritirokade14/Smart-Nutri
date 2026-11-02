# ai/nutri_score.py

def calculate_nutri_score(nutrients: dict) -> dict:
    calories = float(nutrients.get("calories", 0) or 0)
    sugar = float(nutrients.get("sugar", 0) or 0)
    fat = float(nutrients.get("fat", 0) or 0)
    salt = float(nutrients.get("salt", 0) or nutrients.get("sodium", 0) / 400 or 0) # estimate salt from sodium if needed
    protein = float(nutrients.get("protein", 0) or 0)
    fiber = float(nutrients.get("fiber", 0) or 0)

    # 1. Qualitative Evaluation for Display
    sugar_level = "HIGH" if sugar > 15 else ("MEDIUM" if sugar > 5 else "GOOD")
    fat_level = "HIGH" if fat > 17.5 else ("MEDIUM" if fat > 3 else "GOOD")
    salt_level = "HIGH" if salt > 1.5 else ("MEDIUM" if salt > 0.3 else "GOOD")
    protein_level = "GOOD" if protein > 8 else ("MEDIUM" if protein > 4 else "LOW")

    # 2. Point-based scoring heuristic (Nutri-Score model approximation)
    neg_points = 0
    if calories > 335: neg_points += 4
    elif calories > 200: neg_points += 2
    
    if sugar > 15: neg_points += 4
    elif sugar > 5: neg_points += 2

    if fat > 10: neg_points += 3
    elif fat > 5: neg_points += 1

    if salt > 1.0: neg_points += 3
    elif salt > 0.5: neg_points += 1

    pos_points = 0
    if protein > 8: pos_points += 2
    elif protein > 4: pos_points += 1
    
    if fiber > 3: pos_points += 2
    elif fiber > 1: pos_points += 1

    final_score = neg_points - pos_points

    # 3. Map to A-E Letter Grade
    if final_score <= -1: grade = "A"
    elif final_score <= 2: grade = "B"
    elif final_score <= 10: grade = "C"
    elif final_score <= 18: grade = "D"
    else: grade = "E"

    return {
        "grade": grade,
        "evaluations": {
            "sugar": sugar_level,
            "fat": fat_level,
            "salt": salt_level,
            "protein": protein_level
        }
    }