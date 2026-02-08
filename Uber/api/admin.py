"""
Administrative API module for system management.
Handles statistics, drivers verification, promo codes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """ Computes key system financial and user metrics. """
    total_users = db.query(models.User).count()

    activate_drivers = db.query(models.Driver).filter(models.Driver.is_online).count()

    completed_trips = db.query(models.Trip).filter(models.Trip.status == "completed").count()

    total_incomes = db.query(func.sum(models.Trip.final_price)).filter(
        models.Trip.status == "completed").scalar() or 0

    return {
        "total_users": total_users,
        "active_drivers": activate_drivers,
        "completed_trips": completed_trips,
        "total_incomes_bgn": round(float(total_incomes), 2)
    }


@router.get("/unverified-drivers")
def get_unverified_drivers(db: Session = Depends(get_db)):
    """ Returns a list of drivers awaiting approval. """

    drivers = db.query(models.User).filter(models.User.role == "driver",
                                           models.User.is_verified.is_(False)).all()

    unverified_drivers = []
    for d in drivers:
        unverified_drivers.append({"user_id": d.id, "full_name": d.full_name})

    return {
        "drivers": unverified_drivers
    }


@router.patch("/verify-driver/{user_id}")
def verify_driver(user_id: int, db: Session = Depends(get_db)):
    """ Performs verification on a driver's profile. """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in the database.")

    user.is_verified = True
    db.commit()
    return {
        "message": f"Driver {user.full_name} is verified."
    }


@router.patch("/users/{user_id}/block")
def block_user(user_id: int, db: Session = Depends(get_db)):
    """ Blocks user access to the system. """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User is not found")

    user.is_active = False
    db.commit()
    return {
        "message": f"User {user.full_name} is blocked."
    }


@router.get("/reviews/all")
def get_all_reviews(db: Session = Depends(get_db)):
    """ Provides a list of all reviews for admin review and moderation. """
    reviews = db.query(models.Review).all()

    result = []
    for review in reviews:
        driver_name = review.driver.user.full_name
        result.append({
            "id": review.id,
            "trip_id": review.trip_id,
            "client_name": review.client_name,
            "driver_name": driver_name,
            "rating": review.rating,
            "comment": review.comment
        })

    return {
        "all reviews": result
    }


@router.delete("/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """ Removes reviews identified as obscene or fraudulent. """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review is not found.")

    db.delete(review)
    db.commit()
    return {
        "message": "Review removed successfully."
    }


@router.post("/promo-codes/create")
def create_promo_code(code: str, discount: int, db: Session = Depends(get_db)):
    """ Creates a new promo code with a fixed percentage discount. """
    existing = db.query(models.PromoCode).filter(models.PromoCode.code == code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="This code already exists")

    new_promo = models.PromoCode(code=code.upper(), discount_percentage=discount, is_active=True)
    db.add(new_promo)
    db.commit()
    return {
        "message": f"Promo-code {code.upper()} is active."
    }


@router.get("/promo-codes/active")
def get_all_promo_codes(db: Session = Depends(get_db)):
    """ Returns a list of all active promo codes. """
    promos = db.query(models.PromoCode).filter(models.PromoCode.is_active.is_(True)).all()
    return {
        "promo codes": promos
    }


@router.delete("/promo-codes/{code}")
def delete_promo_code(code: str, db: Session = Depends(get_db)):
    """ Deletes a promo code from the system. """
    promo = db.query(models.PromoCode).filter(models.PromoCode.code == code.upper()).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found.")

    db.delete(promo)
    db.commit()
    return {
        "message": f"Promo code {code.upper()} has been deleted."
    }
