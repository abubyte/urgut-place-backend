from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.utils import get_openapi
import logging

from app.db.session import create_db_and_tables
from app.users.router import router as users_router
from app.shops.router import router as shops_router
from app.likes.router import router as likes_router 
from app.categories.router import router as categories_router 
from app.ratings.router import router as ratings_router
from app.models import shop, category, user, like, rating

# Set up logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    print("Database and tables created.")
    
    yield

app = FastAPI(lifespan=lifespan)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Add JWT bearer authentication to Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="UrgutPlease API",
        version="1.0.0",
        description="JWT Auth with Swagger",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation.setdefault("security", []).append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(users_router)
app.include_router(shops_router)
app.include_router(likes_router)
app.include_router(categories_router)
app.include_router(ratings_router)

@app.get("/")
def read_root():
    return RedirectResponse("/docs")
