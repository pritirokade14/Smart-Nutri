from sqlalchemy import Column, Integer, String, Float, ARRAY, DateTime
from sqlalchemy.sql import func
from database.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    preference = Column(String, nullable=False)
    allergies = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())