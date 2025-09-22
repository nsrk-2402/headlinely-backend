from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router   # 👈 import your auth router

app = FastAPI(title = "Headlinely Backend")

# Allow requests from your frontend (Vite)
origins = [
    "http://localhost:5173",   # frontend dev server
    "http://127.0.0.1:5173",   # sometimes vite uses 127.0.0.1
    # Add production URL when deployed
    "https://your-frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # allowed origins
    allow_credentials=True,         # allow cookies/auth headers
    allow_methods=["*"],            # allow all methods (GET, POST, etc.)
    allow_headers=["*"],            # allow all headers
)

app.include_router(auth_router)

@app.get("/")
def root():
    return { "message" : "Headlinely Backend Server is Running..." }