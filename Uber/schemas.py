"""Module for Pydantic schemas used in the FastAPI application."""
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base schema for user data containing common fields."""
    email: EmailStr
    full_name: str
    phone: str
    role: str = "client.html"


class UserCreate(UserBase):
    """Schema for creating a new user with a password."""
    password: str


class User(UserBase):
    """Detailed schema for a user, including database-specific fields."""
    id: int
    is_active: bool
    is_verified: bool
    home_address: Optional[str] = None
    preferences: Optional[str] = None

    class Config:
        """Pydantic configuration to allow ORM model compatibility."""
        from_attributes = True


class DriverBase(BaseModel):
    """Base schema for driver-specific vehicle and pricing information."""
    car_model: str
    car_category: str = "Economy"
    price_per_km: float = 1.20
    current_location: str = "Център"


class DriverCreate(DriverBase):
    """Schema for registering a new driver and their vehicle."""
    user_id: int
    license_plate: str


class Driver(DriverBase):
    """Detailed driver schema including ratings and earnings."""
    id: int
    rating: float
    is_online: bool
    total_earnings: float
    user: Optional[User] = None

    class Config:
        """Pydantic configuration to allow ORM model compatibility."""
        from_attributes = True


class TripCreate(BaseModel):
    """Schema for requesting a new trip."""
    client_id: int
    pickup_location: str
    destination: str
    car_category: str = "Standard"
    final_price: float = 0.0
    is_urgent: bool = False
    is_shared: bool = False


class Trip(TripCreate):
    """Full trip details including status and assigned driver."""
    id: int
    driver_id: Optional[int] = None
    status: str
    payment_status: str
    driver: Optional[Driver] = None

    class Config:
        """Pydantic configuration to allow ORM model compatibility."""
        from_attributes = True


class ReviewCreate(BaseModel):
    """Schema for submitting a new trip review."""
    trip_id: int
    rating: int
    comment: str


class Review(ReviewCreate):
    """Detailed review schema including driver ID and client.html info."""
    id: int
    driver_id: int
    client_name: str

    class Config:
        """Pydantic configuration to allow ORM model compatibility."""
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for sending a direct message between users."""
    sender_id: int
    receiver_id: int
    content: str


class Message(MessageCreate):
    """Full message schema including unique identifier."""
    id: int

    class Config:
        """Pydantic configuration to allow ORM model compatibility."""
        from_attributes = True


class PromoCode(BaseModel):
    """Schema for managing promotional codes."""
    code: str
    discount_percentage: int
    is_active: bool

    class Config:
        """Pydantic configuration to allow ORM model compatibility."""
        from_attributes = True
