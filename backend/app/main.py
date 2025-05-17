from fastapi import FastAPI
from app.db.session import create_db_and_tables
from app.auth.router import router as auth_router

app = FastAPI()

# Include the authentication router
app.include_router(auth_router)

@app.on_event("startup")
def on_startup():
    """
    Create the database and tables on startup.
    """
    create_db_and_tables()
    print("Database and tables created.")

@app.get("/")
def read_root():
    """
    Root endpoint.
    """
    return {"status": "ok"}