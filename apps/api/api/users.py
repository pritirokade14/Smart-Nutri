from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database.database import get_db
from database.models import UserModel

router = APIRouter(prefix="/api/users", tags=["Users"])

class UserProfileCreate(BaseModel):
    name: str
    age: int
    gender: str
    height: float
    weight: float
    goal: str
    preference: str
    allergies: List[str] = []

@router.post("/profile")
def save_user_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    db_user = UserModel(
        name=profile.name,
        age=profile.age,
        gender=profile.gender,
        height=profile.height,
        weight=profile.weight,
        goal=profile.goal,
        preference=profile.preference,
        allergies=profile.allergies
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "status": "success", 
        "message": "User profile saved successfully in PostgreSQL!", 
        "user_id": db_user.id
    }