wodoame: Write a custom logging mechanism that logs unhandled exceptions into the database.
log important information like the error stack trace, username of the user who encountered the error,  timestamp and any other useful information.

GitHub Copilot: To implement a custom logging mechanism for unhandled exceptions that logs to your database, follow these steps:

1. **Create an ExceptionLog model**  
Add a new model to store exception logs.

2. **Create a logging utility function**  
This function will insert logs into the database.

3. **Add a FastAPI exception handler**  
This handler will catch unhandled exceptions, log them, and return a generic error response.

Below is a suggested implementation:

````python
# ...existing code...

from sqlmodel import Session
import traceback

class ExceptionLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: Optional[str] = Field(default=None, index=True)
    error_message: str
    stack_trace: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = Field(default=None)
    method: Optional[str] = Field(default=None)
    client_ip: Optional[str] = Field(default=None)

# ...existing code...
````

**Logging utility:**

````python
from .models import ExceptionLog
from sqlmodel import Session
from fastapi import Request
import traceback

def log_exception_to_db(
    session: Session,
    exc: Exception,
    request: Request,
    username: str = None
):
    stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log = ExceptionLog(
        username=username,
        error_message=str(exc),
        stack_trace=stack,
        path=str(request.url),
        method=request.method,
        client_ip=request.client.host if request.client else None,
    )
    session.add(log)
    session.commit()
````

**FastAPI exception handler:**

````python
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session
from .utils import log_exception_to_db
from .models import ExceptionLog, User
from .database import get_session  # You should have a get_session dependency

app = FastAPI()

@app.exception_handler(Exception)
async def db_exception_handler(request: Request, exc: Exception, session: Session = Depends(get_session)):
    # Extract username if available (e.g., from request.state.user or JWT)
    username = getattr(request.state, "user", None)
    log_exception_to_db(session, exc, request, username)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

# ...existing code...
````

**Notes:**
- Make sure to create and apply the migration for the new `ExceptionLog` table.
- Adjust how you extract the username based on your authentication logic.
- Import and use the exception handler in your FastAPI app.

This setup will log unhandled exceptions with stack trace, username, timestamp, request path, method, and client IP.