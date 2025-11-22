from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1 import projects
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events 4;O FastAPI"""
    # Startup
    print(f"Starting svc_projects on {settings.APP_HOST}:{settings.APP_PORT}")
    yield
    # Shutdown
    print("Shutting down svc_projects")


app = FastAPI(
    title="Projects Service",
    description="8:@>A5@28A C?@02;5=8O AB@>8B5;L=K<8 ?@>5:B0<8",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #  production 70<5=8BL =0 :>=:@5B=K5 4><5=K
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers 4;O 548=>3> D>@<0B0 >B25B>2
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """1@01>B:0 >H81>: 20;840F88 Pydantic"""
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
    """1@01>B:0 HTTP 8A:;NG5=89"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """1@01>B:0 2A5E >AB0;L=KE 8A:;NG5=89"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error"
            }
        }
    )


# >4:;NG5=85 @>CB5@>2
app.include_router(projects.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "success": True,
        "data": {
            "service": "svc_projects",
            "version": "1.0.0",
            "status": "running"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )
