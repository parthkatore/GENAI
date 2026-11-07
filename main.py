
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Product Model
class Product(BaseModel):
    id: int
    name: str
    price: float
    rating: str
    description: str


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Product Records
products = [
    {"id": 1, "name": "Laptop", "price": 55000.0, "rating": "4.5/5", "description": "High-performance laptop for programming."},
    {"id": 2, "name": "Smartphone", "price": 25000.0, "rating": "4.3/5", "description": "Smartphone with a powerful processor."},
    {"id": 3, "name": "Headphones", "price": 1999.0, "rating": "4.2/5", "description": "Wireless headphones with noise cancellation."},
    {"id": 4, "name": "Smart Watch", "price": 3500.0, "rating": "4.1/5", "description": "Smart watch with fitness tracking."},
    {"id": 5, "name": "Keyboard", "price": 1200.0, "rating": "4.4/5", "description": "Mechanical keyboard for daily use."},
    {"id": 6, "name": "Mouse", "price": 799.0, "rating": "4.0/5", "description": "Wireless optical mouse."},
    {"id": 7, "name": "Monitor", "price": 15000.0, "rating": "4.6/5", "description": "24-inch Full HD monitor."},
    {"id": 8, "name": "Bluetooth Speaker", "price": 2499.0, "rating": "4.3/5", "description": "Portable Bluetooth speaker."},
    {"id": 9, "name": "Tablet", "price": 18000.0, "rating": "4.2/5", "description": "Lightweight tablet for studying."},
    {"id": 10, "name": "Power Bank", "price": 1499.0, "rating": "4.1/5", "description": "10000mAh power bank with fast charging."}
]


# Home Route
@app.get("/")
def home():
    return {"message": "Welcome to Product API"}


# Get All Products
@app.get("/products")
def get_products():
    return products


# FILTER PRODUCTS BY PRICE RANGE
@app.get("/products/price-range")
def filter_products(min_price: float, max_price: float):

    result = []

    for prod in products:
        if min_price <= prod["price"] <= max_price:
            result.append(prod)

    return result
