"""
This module handles all driver-specific operations, including profile setup,
service management, shift status updates, location tracking, and performance
metrics such as earnings and reviews.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import get_db

router = APIRouter(tags=["Drivers"])


@router.post("/driver/setup")
def setup_driver(user_id: int, car_model: str, license_plate: str, db: Session = Depends(get_db)):
    """
    Configures the driver's profile by adding vehicle details.
    Verifies user existence and ensures the 'driver' role is assigned.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.role != "driver":
        raise HTTPException(status_code=400, detail="User does not have permission to be a driver")

    driver = db.query(models.Driver).filter(models.Driver.user_id == user_id).first()

    if driver:
        response_data = {
            "message": "Driver profile is already set up",
            "driver_id": driver.id
        }
    else:
        new_driver = models.Driver(
            user_id=user_id,
            car_model=car_model,
            license_plate=license_plate
        )
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)

        response_data = {
            "message": "Driver profile is ready for use",
            "driver_id": new_driver.id
        }

    return response_data


@router.put("/driver/{driver_id}/manage-service")
def manage_service(driver_id: int, price: float = None, schedule: str = None,
                   location: str = None, db: Session = Depends(get_db)):
    """ Updates service parameters for a specific driver, including price per km, schedule, and location. """
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    if price is not None:
        driver.price_per_km = price

    if schedule:
        driver.schedule = schedule

    if location:
        driver.current_location = location

    db.commit()

    return {
        "message": "Service parameters updated successfully"
    }


@router.patch("/driver/{driver_id}/shift")
def update_status(driver_id: int, db: Session = Depends(get_db)):
    """
     Toggles the driver's status between 'Online' and 'Offline'.
     Used for starting and ending work shifts.
      """
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    driver.is_online = not driver.is_online
    db.commit()

    return {
        "message": "Shift status updated successfully"
    }


@router.get("/driver/{driver_id}/earnings")
def get_driver_earnings(driver_id: int, db: Session = Depends(get_db)):
    """
    Retrieves total earnings and the count of completed trips for a driver.
    Returns zero values if the driver is not found.
    """
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail=f"Driver with ID {driver_id} not found")

    trips_count = db.query(models.Trip).filter(models.Trip.driver_id == driver_id,
                                               models.Trip.status == "completed").count()

    return {
        "balance": round(driver.total_earnings, 2),
        "trips_count": trips_count
    }


@router.patch("/driver/{driver_id}/location")
def update_location(driver_id: int, new_location: str, db: Session = Depends(get_db)):
    """ Updates the driver's current geographic location in the database. """
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    driver.current_location = new_location
    db.commit()

    return {
        "message": "Location updated successfully"
    }


@router.get("/driver/{driver_id}/trips/history")
def get_driver_trip_history(driver_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a chronological list of all completed trips for the driver,
     showing the most recent trips first.
     """
    trips = db.query(models.Trip).filter(models.Trip.driver_id == driver_id,
                                         models.Trip.status == "completed"
                                         ).order_by(models.Trip.id.desc()).all()

    return {
        "trips": trips
    }


@router.get("/driver/{driver_id}/reviews")
def get_driver_reviews(driver_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all customer reviews for a
    specific driver, including client.html name, rating, and comments.
    """

    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    reviews = db.query(models.Review).filter(models.Review.driver_id == driver_id).all()

    result = []
    for review in reviews:
        result.append({
            "client_name": review.client_name,
            "rating": review.rating,
            "comment": review.comment
        })

    return {
        "total_reviews": len(result),
        "reviews": result
    }
