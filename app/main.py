from fastapi import FastAPI

app = FastAPI(title = "Headlinely Backend")

@app.get("/")
def root():
    return { "message" : "Headlinely Backend Server is Running..." }