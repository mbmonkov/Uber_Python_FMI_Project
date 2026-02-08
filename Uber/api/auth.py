"""Authentication API endpoints for user registration and login."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db

router = APIRouter(tags=["Authentication"])


@router.post("/register")
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user in the system.
    Checks for email and phone number uniqueness.
    """
    existing_user = db.query(models.User).filter(
        (models.User.email == user_in.email) | (models.User.phone == user_in.phone)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email or phone number is already registered!"
        )

    new_user = models.User(
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        password=user_in.password,
        role=user_in.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "full_name": new_user.full_name,
        "role": new_user.role
    }


@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    """
    Authenticates the user and returns their full profile.
    """
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    if user.is_active is False:
        raise HTTPException(
            status_code=403,
            detail="Account is blocked. Please contact an administrator."
        )

    return {
        "id": user.id,
        "full_name": user.full_name,
        "role": user.role
    }
