"""This module manages the feedback system. """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
import models
from database import get_db

router = APIRouter(tags=["Reviews"])


@router.post("/reviews/add")
def leave_review(trip_id: int, rating: int, comment: str, db: Session = Depends(get_db)):
    """
    Adds a review for a completed trip.
    The client.html's name and driver's ID are automatically retrieved from the trip records.
    """
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.status != "completed":
        raise HTTPException(status_code=400, detail="You can only rate completed trips")

    client_name = trip.client.full_name
    driver_id = trip.driver_id

    new_review = models.Review(
        trip_id=trip_id,
        driver_id=driver_id,
        client_name=client_name,
        rating=rating,
        comment=comment
    )
    db.add(new_review)
    db.commit()

    avg_rating_result = db.query(func.avg(models.Review.rating)).filter(
        models.Review.driver_id == driver_id).scalar()

    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if driver and avg_rating_result is not None:
        driver.rating = round(float(avg_rating_result), 1)
        db.commit()

    return {
        "review_id": new_review.id,
        "message": f"Thank you for your feedback, {client_name}!"
    }
