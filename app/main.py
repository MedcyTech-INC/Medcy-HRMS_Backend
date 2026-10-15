from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import settings
from app.database.engine import engine
from app.database.session import get_db
from app.routers import auth, employees, attendance, breaks, leaves, advances, tasks, field_ops, doctor_visits, asha_encounters, payroll


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    yield
    # Shutdown actions
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers=headers,
    )

# Mount domain routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(breaks.router, prefix="/api/breaks", tags=["Breaks"])
app.include_router(leaves.router, prefix="/api/leaves", tags=["Leaves"])
app.include_router(advances.router, prefix="/api/advances", tags=["Advances"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(field_ops.router, prefix="/api/field-ops", tags=["Field Operations"])
app.include_router(doctor_visits.router, prefix="/api/doctor-visits", tags=["Doctor Visits"])
app.include_router(asha_encounters.router, prefix="/api/asha-encounters", tags=["ASHA Encounters"])
app.include_router(payroll.router, prefix="/api", tags=["Payroll & Invoices"])


@app.get("/api/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check verifying app and database connection."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "database": db_status,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
