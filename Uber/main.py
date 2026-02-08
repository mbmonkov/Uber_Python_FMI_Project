"""
Main entry point for the Uber Clone API application.
This module initializes the FastAPI app, configures static files and templates,
sets up database models, and includes all sub-routers for authentication,
trips, drivers, and user management.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, get_db
import models
from api import auth, drivers, trips, guests, users, messages, reviews, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Uber API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(reviews.router)
app.include_router(messages.router)
app.include_router(guests.router)
app.include_router(admin.router)


@app.get("/client", tags=["System"])
def read_index(request: Request, db: Session = Depends(get_db)):
    """
        Render the main landing page with real-time data from the database.
        Fetches online drivers who are not currently on a trip and retrieves
        the top 5 highest-rated drivers for the rankings list.
    """
    busy_drivers = db.query(models.Trip.driver_id).filter(
        models.Trip.status.in_(["accepted", "started"])
    ).all()
    busy_ids = [d[0] for d in busy_drivers if d[0] is not None]

    available_drivers = db.query(models.Driver).filter(
        models.Driver.is_online == True,
        ~models.Driver.id.in_(busy_ids)
    ).all()

    rankings = db.query(models.Driver).order_by(models.Driver.rating.desc()).limit(5).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "available_drivers": available_drivers,
        "rankings": rankings
    })


@app.get("/", tags=["System"])
def health_check():
    """Provide a simple health check endpoint to verify that the API is online and functional."""
    return {
        "status": "success", "message": "Uber API is online!"
    }


@app.get("/login", tags=["Frontend"])
def get_login_page(request: Request):
    """Serve the HTML login page to the user."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", tags=["Frontend"])
def get_register_page(request: Request):
    """Serve the HTML registration page for new clients and drivers."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard/client", tags=["Frontend"])
def client_dashboard(request: Request):
    """Render the specific dashboard interface for users logged in as Clients."""
    return templates.TemplateResponse("client.html", {"request": request})


@app.get("/dashboard/driver", tags=["Frontend"])
def driver_dashboard(request: Request, db: Session = Depends(get_db)):
    """
        Render the Driver's dashboard. Identifies the driver based on their full name
        to provide personalized trip requests and balance information.
    """
    full_name = request.query_params.get("full_name")

    driver_id = None
    if full_name:
        driver = db.query(models.Driver).filter(models.Driver.full_name == full_name).first()
        if driver:
            driver_id = driver.id

    return templates.TemplateResponse("driver.html", {
        "request": request,
        "driver_id": driver_id
    })
