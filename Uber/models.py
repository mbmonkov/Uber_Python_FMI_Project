"""
Database models definition module.
Utilizes SQLAlchemy to define the database schema, table structures,
and relationships between users, drivers, trips, and messaging.
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """
        User model representing individuals in the system.
        Supports roles: 'client', 'driver', and 'admin'.
        Stores authentication details, contact info, and user-specific preferences.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="client.html")
    home_address = Column(String, nullable=True)
    preferences = Column(String, nullable=True)
    favorites = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class Driver(Base):
    """
        Driver model extending User information for taxi service providers.
        Includes vehicle details, pricing, real-time availability (online status),
        location tracking, and accumulated earnings.
    """
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    car_model = Column(String)
    car_category = Column(String, default="Economy")
    license_plate = Column(String)
    description = Column(String, nullable=True)
    price_per_km = Column(Float, default=1.20)
    schedule = Column(String, default="24/7")
    current_location = Column(String, default="Център")
    rating = Column(Float, default=5.0)
    is_online = Column(Boolean, default=False)
    total_earnings = Column(Float, default=0.0)

    user = relationship("User")


class Trip(Base):
    """
        Trip model representing ride requests and bookings.
        Connects clients with drivers and stores route details, status updates,
        ride categories, and final pricing.
    """
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    pickup_location = Column(String)
    destination = Column(String)
    status = Column(String, default="searching")
    payment_status = Column(String, default="pending")
    is_shared = Column(Boolean, default=False)
    seats_available = Column(Integer, default=4)
    is_urgent = Column(Boolean, default=False)
    final_price = Column(Float, default=0.0)
    car_category = Column(String, default="Standard")

    client = relationship("User")
    driver = relationship("Driver")


class Review(Base):
    """
        Review model for feedback and ratings after a completed trip.
        Links specific trips to driver performance evaluations.
    """
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    client_name = Column(String)
    rating = Column(Integer)
    comment = Column(String)

    trip = relationship("Trip")
    driver = relationship("Driver")


class Message(Base):
    """
        Message model for real-time communication between users.
        Tracks sender, receiver, content, and the time of exchange.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    timestamp = Column(String, nullable=True)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class PromoCode(Base):
    """
        PromoCode model for managing discount campaigns.
        Stores unique codes and their respective discount percentages.
    """
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    discount_percentage = Column(Integer)
    is_active = Column(Boolean, default=True)
