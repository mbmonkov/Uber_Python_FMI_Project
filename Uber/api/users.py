"""
This module manages user-specific actions, including profile settings updates, 
security credentials management (password and phone updates), favorite drivers 
list maintenance, and trip history retrieval for clients.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import get_db

router = APIRouter(tags=["Users"])


@router.patch("/user/{user_id}/settings")
def update_user_settings(user_id: int, address: str = None, prefs: str = None,
                         db: Session = Depends(get_db)):
    """ Updates the user's home address and personal preferences. """
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if address:
        user.home_address = address
    if prefs:
        user.preferences = prefs

    db.commit()
    return {
        "message": "Profile updated successfully"
    }


@router.put("/user/{user_id}/security")
def update_user_security(user_id: int, password: str, new_password: str = None,
                         phone: str = None, db: Session = Depends(get_db)):
    """ Updates password or phone number after verifying the current password. """
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid current password!")

    if new_password:
        user.password = new_password
    if phone:
        user.phone = phone

    db.commit()
    return {
        "message": "Security settings updated successfully"
    }


@router.post("/user/favorites/add")
def add_favorite_driver(user_id: int, driver_id: int, db: Session = Depends(get_db)):
    """ Adds a driver to the user's favorites list. """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_favorites = user.favorites.split(",") if user.favorites else []

    if str(driver_id) not in current_favorites:
        current_favorites.append(str(driver_id))
        user.favorites = ",".join(current_favorites).strip(",")
        db.commit()
        return {
            "message": "Driver added to favorites"
        }

    return {
        "message": "Driver is already in your favorites list"
    }


@router.get("/user/{user_id}/favorites")
def get_favorite_drivers(user_id: int, db: Session = Depends(get_db)):
    """ Retrieves detailed information about favorite drivers using database relations. """
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user or not user.favorites:
        return {
            "message": "No favorite drivers found"
        }

    favorites = [int(fid.strip()) for fid in user.favorites.split(",") if fid.strip()]
    drivers = db.query(models.Driver).filter(models.Driver.id.in_(favorites)).all()

    result = [
        {
            "id": driver.id,
            "full_name": driver.user.full_name,
            "car": driver.car_model,
            "rating": driver.rating,
            "is_online": driver.is_online
        } for driver in drivers
    ]

    return {
        "favorite drivers": result
    }


@router.get("/user/{user_id}/history")
def get_client_trip_history(user_id: int, db: Session = Depends(get_db)):
    """ Retrieves the history of completed trips for a client.html. """
    trips = db.query(models.Trip).filter(models.Trip.client_id == user_id,
                                         models.Trip.status == "completed"
                                         ).order_by(models.Trip.id.desc()).all()

    return {
        "trip history": trips
    }
