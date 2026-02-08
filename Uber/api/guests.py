"""Guest access API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session
import models
from database import get_db

router = APIRouter(tags=["Guests"])


@router.get("/driver/{driver_id}/profile")
def get_driver_public_profile(driver_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a driver's public profile by their unique ID.
    Returns only the information necessary for a client.html to make a booking.
    """
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail=f"Driver with ID {driver_id} not found")

    return {
        "id": driver.id,
        "full_name": driver.user.full_name,
        "car_model": driver.car_model,
        "car_category": driver.car_category,
        "rating": round(driver.rating, 1),
        "location": driver.current_location,
        "price_per_km": driver.price_per_km
    }


@router.get("/drivers/rankings")
def get_drivers_and_ratings(db: Session = Depends(get_db)):
    """
    Returns a list of all drivers, ordered by their rating.
    """
    drivers = db.query(models.Driver).all()

    result = []
    for d in drivers:
        result.append({
            "id": d.id,
            "full_name": d.user.full_name,
            "rating": d.rating
        })

    result.sort(key=lambda x: x["rating"], reverse=True)

    return {"rankings": result}


@router.get("/search/drivers")
def get_available_drivers(db: Session = Depends(get_db)):
    """
    Returns a list of all drivers who are online and currently not on a trip.
    """
    busy_drivers_ids = db.query(models.Trip.driver_id).filter(
        models.Trip.status.in_(["accepted", "started"])).all()

    busy_ids = [d[0] for d in busy_drivers_ids if d[0] is not None]

    available_drivers = db.query(models.Driver).filter(and_(models.Driver.is_online.is_(True),
                                                            ~models.Driver.id.in_(busy_ids))).all()

    result = []
    for d in available_drivers:
        result.append({
            "id": d.id,
            "full_name": d.user.full_name,
            "car_model": d.car_model,
            "car_category": d.car_category,
            "rating": d.rating,
            "current_location": d.current_location
        })

    return {
        "available drivers": result
    }
