import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and attach X-Request-ID to each request.

    If the client provides X-Request-ID header, it will be preserved.
    Otherwise, a new UUID will be generated.
    """

    async def dispatch(self, request: Request, call_next):
        # Get existing request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store request_id in request state for access in routes
        request.state.request_id = request_id

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
