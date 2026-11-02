import os
import re
import json
import shutil
import logging
from types import SimpleNamespace
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.database import engine, Base, SessionLocal
from database.models import UserModel
from api import users  
from services.ocr_service import process_and_extract_text
from services.llm_extractor import extract_nutrition_with_llm
from ai.nutri_score import calculate_nutri_score  

logger = logging.getLogger("smartnutri")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartNutri AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include user profile router
app.include_router(users.router)

# Ensure upload directory exists for food/label images
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configure Gemini API Key for Phase 10 GenAI Explanations
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _num(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt(value) -> str:
    return f"{_num(value):g}"


# Safeguard to normalize and clean extracted nutrition metrics (Prevents impossible values like 60g salt)
def normalize_nutrition_data(data: dict) -> dict:
    cleaned = dict(data)
    
    # Normalize standard keys safely
    for key in ["calories", "protein", "fat", "carbs", "sugar", "salt", "sodium"]:
        if key in cleaned:
            cleaned[key] = _num(cleaned[key], 0.0)

    # Sanity fix for salt/sodium confusion: If salt is reported > 25g per serving, it's almost certainly milligrams (mg)
    salt_val = cleaned.get("salt", 0.0)
    sodium_val = cleaned.get("sodium", 0.0)
    
    if salt_val > 25.0:
        # Convert mg to grams if it looks like milligrams
        cleaned["salt"] = round(salt_val / 1000.0, 2)
    elif salt_val == 0.0 and sodium_val > 0.0:
        # Approximate salt from sodium if salt is missing: Salt (g) ≈ Sodium (mg) * 2.5 / 1000
        cleaned["salt"] = round((sodium_val * 2.5) / 1000.0, 2)

    # Ensure macroscopic macros don't stay 0 if calories are present but macros were missed
    calories = cleaned.get("calories", 0.0)
    if calories > 0 and cleaned.get("protein", 0) == 0 and cleaned.get("fat", 0) == 0 and cleaned.get("carbs", 0) == 0:
        # Fallback estimation distribution for generic items if raw numbers failed parsing
        cleaned["carbs"] = round(calories * 0.5 / 4.0, 1)
        cleaned["fat"] = round(calories * 0.3 / 9.0, 1)
        cleaned["protein"] = round(calories * 0.2 / 4.0, 1)

    return cleaned


# Helper Logic: Allergy & Ingredient Analysis against User Profile
def analyze_product_against_profile(product_data: dict, user_profile) -> dict:
    alerts = []
    warnings = []
    
    product_ingredients = [str(i).lower() for i in product_data.get("ingredients", [])]
    
    user_allergies = []
    if user_profile and user_profile.allergies:
        if isinstance(user_profile.allergies, list):
            user_allergies = [str(a).lower() for a in user_profile.allergies]
        elif isinstance(user_profile.allergies, str):
            user_allergies = [str(a).strip().lower() for a in user_profile.allergies.split(",")]

    detected_allergies = [
        allergy for allergy in user_allergies 
        if any(allergy in ing for ing in product_ingredients)
    ]
    
    if detected_allergies:
        alerts.append({
            "type": "ALLERGY_ALERT",
            "message": f"⚠️ ALLERGY ALERT: {', '.join(detected_allergies).capitalize()} detected!"
        })
        
    if product_data.get("sugar", 0) > 15.0:
        warnings.append("High sugar content (>15g)")
    if product_data.get("salt", 0) > 5.0 or product_data.get("sodium", 0) > 2000:
        warnings.append("High salt content")
    if product_data.get("fat", 0) > 17.5:
        warnings.append("High fat content (>17.5g)")
    if product_data.get("protein", 0) < 5.0:
        warnings.append("Low protein content (<5g)")
        
    return {
        "alerts": alerts,
        "warnings": warnings,
        "is_safe": len(detected_allergies) == 0
    }


# Personalized Recommendation Engine Logic
def generate_recommendation(product_data: dict, nutri_analysis: dict, user_profile) -> dict:
    reasons = []
    is_recommended = True

    user_allergies = []
    user_goal = ""
    user_preferences = []

    if user_profile:
        if user_profile.allergies:
            if isinstance(user_profile.allergies, list):
                user_allergies = [str(a).lower().strip() for a in user_profile.allergies]
            elif isinstance(user_profile.allergies, str):
                user_allergies = [str(a).strip().lower() for a in user_profile.allergies.split(",")]
        
        if hasattr(user_profile, 'goal') and user_profile.goal:
            user_goal = str(user_profile.goal).lower().strip()

        if hasattr(user_profile, 'preferences') and user_profile.preferences:
            if isinstance(user_profile.preferences, list):
                user_preferences = [str(p).lower().strip() for p in user_profile.preferences]
            elif isinstance(user_profile.preferences, str):
                user_preferences = [str(p).strip().lower() for p in user_profile.preferences.split(",")]

    ingredients = [str(i).lower().strip() for i in product_data.get("ingredients", [])]
    evaluations = nutri_analysis.get("evaluations", {})
    grade = nutri_analysis.get("grade", "C")

    for allergen in user_allergies:
        if allergen and allergen != "other":
            if any(allergen in ing for ing in ingredients):
                is_recommended = False
                reasons.append(f"Contains {allergen.capitalize()} (Allergy match)")

    non_veg_keywords = ["chicken", "fish", "meat", "beef", "pork", "gelatin", "rennet", "prawn", "lamb", "mutton"]
    for pref in user_preferences:
        if "vegetarian" in pref:
            detected_non_veg = [kw for kw in non_veg_keywords if any(kw in ing for ing in ingredients)]
            if detected_non_veg:
                is_recommended = False
                reasons.append(f"Contains non-vegetarian ingredient(s): {', '.join(detected_non_veg)}")

    if user_goal == "low sugar":
        if evaluations.get("sugar") == "HIGH":
            is_recommended = False
            reasons.append("High sugar content contradicts your Low Sugar goal")
        else:
            reasons.append("Aligns well with your Low Sugar goal")

    elif user_goal == "low salt":
        if evaluations.get("salt") == "HIGH":
            is_recommended = False
            reasons.append("High salt content contradicts your Low Salt goal")
        else:
            reasons.append("Aligns well with your Low Salt goal")

    elif user_goal == "high protein":
        if evaluations.get("protein") in ["LOW", "MEDIUM"]:
            is_recommended = False
            reasons.append("Does not meet your High Protein requirement")
        else:
            reasons.append("Great protein content matching your High Protein goal")

    elif user_goal == "weight loss":
        if grade in ['D', 'E'] or evaluations.get("sugar") == "HIGH":
            is_recommended = False
            reasons.append("Nutritional profile is too high in calories/sugar for Weight Loss")
        else:
            reasons.append("Good choice supporting your Weight Loss goal")

    elif user_goal == "weight gain":
        reasons.append("Supports your Weight Gain energy requirements")

    elif user_goal == "healthy eating":
        if grade in ['D', 'E']:
            is_recommended = False
            reasons.append(f"Nutri-Score {grade} does not align with Healthy Eating")
        else:
            reasons.append("Matches your Healthy Eating goals and preferences well!")

    if is_recommended and not reasons:
        if grade in ['A', 'B']:
            reasons.append("Good overall nutritional quality")
        else:
            reasons.append(f"Acceptable product, though Nutri-Score is {grade}")

    return {
        "is_recommended": is_recommended,
        "status": "Recommended" if is_recommended else "Not Recommended",
        "reasons": reasons
    }


# GenAI explanation + goal-aware tips
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "es": "Spanish", "fr": "French",
    "de": "German", "ta": "Tamil", "te": "Telugu", "bn": "Bengali", "gu": "Gujarati",
    "pt": "Portuguese", "ar": "Arabic", "zh": "Chinese", "ja": "Japanese",
}


def build_fallback_tips(goal: str, nutrients: dict, grade: str, evaluations: dict) -> list:
    g = (goal or "").lower().strip()
    cal, protein = _num(nutrients.get("calories")), _num(nutrients.get("protein"))
    sugar, salt, fat = _num(nutrients.get("sugar")), _num(nutrients.get("salt")), _num(nutrients.get("fat"))
    tips = []

    if g == "low sugar":
        tips.append(f"Sugar is {_fmt(sugar)} g - " + ("keep the portion small." if sugar > 5 else "a good fit for a low-sugar diet."))
        tips.append("Pair it with fiber or protein to slow sugar absorption.")
    elif g == "low salt":
        tips.append(f"Salt is {_fmt(salt)} g - " + ("balance the rest of your day with low-salt foods." if salt > 0.6 else "comfortably low for your goal."))
        tips.append("Drink water and avoid adding extra salt or salty sides.")
    elif g == "high protein":
        tips.append(f"Protein is {_fmt(protein)} g - " + ("a solid protein source." if protein >= 10 else "add eggs, yogurt, paneer or lentils to raise it."))
        tips.append("Spread protein across meals, and have some within 2 hours of exercise.")
    elif g == "weight loss":
        tips.append(f"At {_fmt(cal)} kcal, measure your portion instead of eating from the pack.")
        tips.append("Pair with vegetables or protein to stay full longer.")
    elif g == "weight gain":
        tips.append(f"Provides {_fmt(cal)} kcal - combine with a protein source to build muscle rather than only fat.")
        tips.append("Add nuts, milk or peanut butter for extra healthy calories.")
    else:
        tips.append("Pair with vegetables, fruit or whole grains for a more balanced meal.")
        tips.append("Check the ingredient list - shorter lists usually mean less processing.")

    if evaluations.get("sugar") == "HIGH":
        tips.append("High in sugar - best kept as an occasional treat.")
    if evaluations.get("salt") == "HIGH":
        tips.append("High in salt - avoid pairing it with other salty foods.")
    if evaluations.get("fat") == "HIGH" or fat > 17.5:
        tips.append("High in fat - limit how often you eat it.")
    if grade in ("D", "E"):
        tips.append(f"Nutri-Score {grade}: consider the healthier alternatives shown below.")

    return tips[:4]


def build_fallback_explanation(food_name: str, goal: str, grade: str, recommendation: dict,
                               nutrients: dict, evaluations: dict) -> str:
    status = recommendation.get("status", "Recommended").lower()
    reasons = recommendation.get("reasons", [])
    parts = [f"{food_name} is {status} for your goal of {goal} (Nutri-Score {grade})."]
    if reasons:
        parts.append(" ".join(r.rstrip(".") + "." for r in reasons))
    parts.append(
        f"It has {_fmt(nutrients.get('calories'))} kcal, {_fmt(nutrients.get('protein'))} g protein, "
        f"{_fmt(nutrients.get('fat'))} g fat, {_fmt(nutrients.get('carbs'))} g carbs, "
        f"{_fmt(nutrients.get('sugar'))} g sugar and {_fmt(nutrients.get('salt'))} g salt."
    )
    high = [k for k, v in evaluations.items() if v == "HIGH"]
    good = [k for k, v in evaluations.items() if v == "GOOD"]
    if high:
        parts.append(f"Watch the {', '.join(high)} content.")
    if good:
        parts.append(f"On the plus side, {', '.join(good)} looks good.")
    return " ".join(parts)


def generate_llm_explanation(food_name: str, product_data: dict, nutri_analysis: dict, user_profile,
                             base_recommendation: dict, goal: str, language: str = "en") -> dict:
    name = getattr(user_profile, "full_name", None) or "User"
    preferences = getattr(user_profile, "preferences", []) or []
    allergies = getattr(user_profile, "allergies", []) or []
    grade = nutri_analysis.get("grade", "C")
    evaluations = nutri_analysis.get("evaluations", {})
    status = base_recommendation.get("status", "Recommended")
    reasons = base_recommendation.get("reasons", [])
    lang_name = LANGUAGE_NAMES.get(language, f"the language with ISO code '{language}'")

    prompt = f"""You are a friendly, expert nutrition coach. Analyze this product for this specific user.

USER
- Name: {name}
- Primary goal: {goal}
- Dietary preferences: {preferences}
- Allergies: {allergies}

PRODUCT: {food_name}
- Nutri-Score: {grade}
- Per serving: {_fmt(product_data.get('calories'))} kcal, protein {_fmt(product_data.get('protein'))} g,
  fat {_fmt(product_data.get('fat'))} g, carbs {_fmt(product_data.get('carbs'))} g,
  sugar {_fmt(product_data.get('sugar'))} g, salt {_fmt(product_data.get('salt'))} g
- Nutrient ratings: {evaluations}
- Ingredients: {product_data.get('ingredients', [])}
- Engine verdict: {status}
- Engine reasons: {reasons}

TASK
1. "explanation": 4-6 sentences. Cover (a) whether it fits the goal "{goal}" and why, using the actual numbers,
   (b) the best and the worst nutrient for THIS goal, (c) how to eat it (portion, pairing, timing).
   Stay consistent with the engine verdict ({status}). Be encouraging and specific, not generic.
2. "tips": exactly 3 short, actionable tips (max 15 words each) written specifically for goal "{goal}" and
   this product's numbers. Do not give generic advice like "stay hydrated".

Write everything in {lang_name}.
Respond with ONLY valid JSON, no markdown: {{"explanation": "...", "tips": ["...", "...", "..."]}}"""

    try:
        # Fixed: Removed unsupported response_mime_type key to avoid protobuf compatibility crashes
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"temperature": 0.6},
        )
        response = model.generate_content(prompt)
        text = re.sub(r"^```(?:json)?|```$", "", response.text.strip(), flags=re.MULTILINE).strip()
        parsed = json.loads(text)

        explanation = str(parsed.get("explanation", "")).strip()
        tips = [str(t).strip() for t in parsed.get("tips", []) if str(t).strip()]
        if not explanation:
            raise ValueError("LLM returned an empty explanation")
        if not tips:
            tips = build_fallback_tips(goal, product_data, grade, evaluations)
        return {"explanation": explanation, "tips": tips[:4], "source": "llm"}
    except Exception as exc:
        logger.exception("Gemini explanation failed (model=%s) - using rule-based fallback", GEMINI_MODEL)
        return {
            "explanation": build_fallback_explanation(food_name, goal, grade, base_recommendation, product_data, evaluations),
            "tips": build_fallback_tips(goal, product_data, grade, evaluations),
            "source": "fallback",
            "error": f"{type(exc).__name__}: {exc}"[:300],
        }

@app.post("/api/voice-query")
async def voice_query(
    question: str = Form(...),
    product_name: str = Form(...),
    calories: float = Form(0.0),
    protein: float = Form(0.0),
    sugar: float = Form(0.0),
    fat: float = Form(0.0),
    salt: float = Form(0.0),
    grade: str = Form("C"),
    goal: str = Form("Healthy Eating"),
    language: str = Form("en")
):
    """
    Phase 16: Handles Voice Assistant queries ("Ask AI") by passing the spoken question
    and current product context to Gemini for a precise conversational response.
    """
    lang_name = LANGUAGE_NAMES.get(language, "English")
    
    prompt = f"""You are a helpful, conversational voice assistant for a nutrition app.
The user is asking a question about a food product they just scanned.

USER GOAL: {goal}
PRODUCT: {product_name}
- Nutri-Score: {grade}
- Calories: {calories} kcal
- Protein: {protein} g
- Sugar: {sugar} g
- Fat: {fat} g
- Salt: {salt} g

USER'S SPOKEN QUESTION: "{question}"

TASK:
Provide a concise, direct, and conversational answer (1-3 sentences) suitable for text-to-speech reading. Be specific to the product numbers and user goal. Write your response in {lang_name}.
"""

    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"temperature": 0.5},
        )
        response = model.generate_content(prompt)
        answer = response.text.strip()
        return {
            "status": "success",
            "question": question,
            "answer": answer
        }
    except Exception as e:
        logger.exception("Voice query LLM failed")
        # Rule-based fallback if LLM encounters any issue
        q = question.lower()
        if "sugar" in q:
            fallback_ans = f"{product_name} contains {sugar}g of sugar. " + ("That is quite high for your goal." if sugar > 15 else "That's within a reasonable limit.")
        elif "calorie" in q or "calories" in q:
            fallback_ans = f"{product_name} has {calories} calories per serving with a Nutri-Score grade of {grade}."
        else:
            fallback_ans = f"{product_name} is evaluated as grade {grade} under your {goal} objective."
        
        return {
            "status": "success",
            "question": question,
            "answer": fallback_ans
        }


@app.get("/")
def read_root():
    return {"message": "Welcome to SmartNutri AI API! Go to /docs for API documentation."}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "PostgreSQL connected"}


@app.post("/api/scan")
async def scan_food_image(
    file: UploadFile = File(...),
    goal: str = Form(None),
    language: str = Form("en"),
    db: Session = Depends(get_db)
):
    try:
        safe_name = os.path.basename(file.filename or "scan.png")
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. OpenCV Preprocessing + EasyOCR
        ocr_result = process_and_extract_text(file_path)
        if ocr_result["status"] == "error":
            raise HTTPException(status_code=500, detail=ocr_result["message"])
        raw_text = ocr_result["extracted_text"]

        # 2. LLM Nutrition & Ingredient Extraction via Groq
        raw_structured_data = extract_nutrition_with_llm(raw_text)

        # 2b. Normalize data to prevent impossible values (e.g. 60g salt)
        structured_data = normalize_nutrition_data(raw_structured_data)

        # 3. Nutri-Score & evaluations
        nutri_analysis = calculate_nutri_score(structured_data)

        # 4. Latest user profile, with the goal sent by the app applied on top.
        latest_user = db.query(UserModel).order_by(UserModel.id.desc()).first()
        saved_goal = getattr(latest_user, "goal", None)
        goal = (goal or "").strip() or (str(saved_goal).strip() if saved_goal else "") or "Healthy Eating"
        profile = SimpleNamespace(
            full_name=getattr(latest_user, "full_name", None) or "User",
            allergies=getattr(latest_user, "allergies", None) or [],
            preferences=getattr(latest_user, "preferences", None) or [],
            goal=goal,
        )

        food_name = safe_name.rsplit(".", 1)[0].replace("_", " ").title()

        # 5. Allergy & ingredient analysis
        profile_analysis = analyze_product_against_profile(structured_data, profile)

        # 6. Personalized recommendation engine
        recommendation_result = generate_recommendation(structured_data, nutri_analysis, profile)

        # 7. GenAI explanation + tips
        ai = generate_llm_explanation(
            food_name, structured_data, nutri_analysis, profile, recommendation_result, goal, language
        )

        # 8. Response for Flutter
        return {
            "status": "success",
            "filename": file.filename,
            "goal": goal,
            "message": "Scan analyzed successfully.",
            "analysis": {
                "food_name": food_name,
                "grade": nutri_analysis["grade"],
                "evaluations": nutri_analysis["evaluations"],
                "raw_ocr_text": raw_text,
                **structured_data
            },
            "recommendation": recommendation_result,
            "genai_explanation": ai["explanation"],
            "tips": ai["tips"],
            "explanation_source": ai["source"],
            "explanation_error": ai.get("error"),
            "alerts": profile_analysis["alerts"],
            "warnings": profile_analysis["warnings"],
            "is_safe": profile_analysis["is_safe"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Scan failed")
        raise HTTPException(status_code=500, detail=str(e))