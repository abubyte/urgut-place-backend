from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.db.session import create_db_and_tables
from app.auth.router import router as auth_router
from app.shops.router import router as shops_router
from app.likes.router import router as likes_router 
from app.categories.router import router as categories_router 
from app.models import shop, category, user, like

app = FastAPI()

# Add JWT bearer authentication to Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="My App",
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
app.include_router(auth_router)
app.include_router(shops_router)
app.include_router(likes_router)
app.include_router(categories_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("Database and tables created.")

@app.get("/")
def read_root():
    return {"status": "ok"}
