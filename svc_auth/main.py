from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1 import auth, users
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events для FastAPI"""
    # Startup
    print(f"Starting svc_auth on {settings.APP_HOST}:{settings.APP_PORT}")
    yield
    # Shutdown
    print("Shutting down svc_auth")


app = FastAPI(title="svc_auth - Authentication Service", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers для единого формата
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработка ошибок валидации Pydantic"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors(),
            },
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Обработка всех необработанных исключений"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)},
        },
    )


# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"service": "svc_auth", "version": "1.0.0", "status": "running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
