from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1 import routes_auth_proxy, routes_projects_proxy, routes_defects_proxy, routes_reports_proxy
from core.config import settings
from core.middleware import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI"""
    # Startup
    print(f"Starting svc_gateway on {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"Proxying to:")
    print(f"  - AUTH: {settings.AUTH_SERVICE_URL}")
    print(f"  - PROJECTS: {settings.PROJECTS_SERVICE_URL}")
    print(f"  - DEFECTS: {settings.DEFECTS_SERVICE_URL}")
    print(f"  - REPORTS: {settings.REPORTS_SERVICE_URL}")
    yield
    # Shutdown
    print("Shutting down svc_gateway")


app = FastAPI(
    title="API Gateway",
    description="Central API Gateway for microservices defect management system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)


# Exception handlers for unified response format
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors(),
            },
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": "HTTP_ERROR", "message": exc.detail},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
            },
        },
    )


# Include proxy routers
app.include_router(routes_auth_proxy.router, prefix="/api/v1")
app.include_router(routes_projects_proxy.router, prefix="/api/v1")
app.include_router(routes_defects_proxy.router, prefix="/api/v1")
app.include_router(routes_reports_proxy.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "success": True,
        "data": {
            "service": "svc_gateway",
            "version": "1.0.0",
            "status": "running",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True
    )
