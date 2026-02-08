"""
This module manages the core trip lifecycle, including trip requests,
price calculations (with promo codes and urgency surges), driver assignments,
real-time status tracking and payment processing upon completion.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db

router = APIRouter(tags=["Trips"])


@router.post("/trip/request")
def request_trip(trip_data: schemas.TripCreate, db: Session = Depends(get_db)):
    """ Creates a new trip request. Uses TripCreate schema to handle multiple arguments efficiently. """
    new_trip = models.Trip(
        client_id=trip_data.client_id,
        pickup_location=trip_data.pickup_location,
        destination=trip_data.destination,
        car_category=trip_data.car_category,
        final_price=trip_data.final_price,
        status="searching",
        is_shared=trip_data.is_shared,
        is_urgent=trip_data.is_urgent
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    return {
        "message": "Request accepted. Searching for a driver...",
        "trip_id": new_trip.id
    }


@router.get("/trips/available-trips")
def get_available_trips(db: Session = Depends(get_db)):
    """
    Retrieves a list of all active taxi requests currently searching for a driver.
    Ordered by most recent.
    """

    available_trips = db.query(models.Trip).filter(
        models.Trip.status == "searching").order_by(models.Trip.id.desc()).all()

    return {
        "available trips": available_trips
    }


@router.patch("/trip/{trip_id}/accept")
def accept_trip(trip_id: int, driver_id: int, db: Session = Depends(get_db)):
    """Allows a driver to accept a pending trip.Verifies trip availability and driver validity."""
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    if trip.status != "searching":
        raise HTTPException(status_code=400, detail="This trip is already taken or cancelled")

    trip.driver_id = driver_id
    trip.status = "accepted"

    db.commit()
    db.refresh(trip)

    return {
        "message": "Trip accepted successfully"
    }


@router.patch("/trip/{trip_id}/cancel")
def cancel_trip(trip_id: int, db: Session = Depends(get_db)):
    """ Cancels a trip request. Allowed only if the trip is not already completed or cancelled. """
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Request not found")

    if trip.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel a trip with status: {trip.status}")

    trip.status = "cancelled"
    db.commit()

    return {
        "message": "Trip cancelled successfully"
    }


@router.get("/trip/calculate-price")
def calculate_price(original_price: float, is_urgent: bool = False, promo_code: str = None,
                    db: Session = Depends(get_db)):
    """ Calculates final price based on urgency surge and promotional discounts. """
    final_price = original_price

    if is_urgent:
        final_price *= 1.5

    if promo_code:
        promo = db.query(models.PromoCode).filter(models.PromoCode.code == promo_code.upper(),
                                                  models.PromoCode.is_active.is_(True)).first()
        if promo:
            final_price -= (promo.discount_percentage / 100) * final_price

    return {"final_price": round(final_price, 2)}


@router.patch("/trip/{trip_id}/complete")
def complete_and_process_payment(trip_id: int, db: Session = Depends(get_db)):
    """ Completes the trip, marks it as paid, and adds the amount to the driver's total earnings. """
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.status == "completed":
        raise HTTPException(status_code=400, detail="Trip has already been completed")

    trip.status = "completed"
    trip.payment_status = "paid"

    amount_to_pay = trip.final_price if trip.final_price > 0 else 10.0

    if trip.driver:
        trip.driver.total_earnings += amount_to_pay
    else:
        raise HTTPException(status_code=400, detail="No driver assigned to this trip")

    db.commit()

    return {
        "message": "Trip completed and payment processed successfully"
    }


@router.get("/trip/{trip_id}/status")
def track_taxi_status(trip_id: int, db: Session = Depends(get_db)):
    """ Allows the client.html to track trip status and driver location in real-time. """
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.status == "searching" or not trip.driver:
        return {
            "status": trip.status,
            "message": "Still searching for the nearest driver..."
        }

    driver_info = trip.driver
    user_info = driver_info.user

    return {
        "status": trip.status,
        "driver_details": {
            "name": user_info.full_name,
            "car": driver_info.car_model,
            "plate": driver_info.license_plate,
            "current_location": driver_info.current_location
        },
        "pickup_location": trip.pickup_location,
        "destination": trip.destination
    }


@router.get("/trips/shared/available")
def get_shared_trips(db: Session = Depends(get_db)):
    """ Retrieves all active shared-trip requests that are still searching for a driver. """
    shared_trips = (db.query(models.Trip).filter(models.Trip.is_shared.is_(True),
                                                 models.Trip.status == "searching"
                                                 ).order_by(models.Trip.id.desc()).all())

    return {
        "shared trips": shared_trips
    }
