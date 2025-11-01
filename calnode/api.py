from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from calnode.calendars import CalDAVCalendar, Calendars, IcalCalendar
from dotenv import load_dotenv
import logging

from calnode.config import load_calendars_from_env


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="calnode.log",
    filemode="w"
    )

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CalDAV OpenAPI Service", 
    version="0.1.0"
    )

# Allow all origins by default.  Adjust this for production if needed.
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)

@app.middleware("http")
async def readonly_guard(request: Request, call_next):
    if request.method in ("PUT", "DELETE", "MKCOL", "PROPPATCH", "MOVE", "COPY", "LOCK", "UNLOCK", "POST"):
        logging.warning(f"Attempted write operation blocked: {request.method} {request.url}")
        raise HTTPException(status_code=403, detail="Read-only mode: write operations are disabled.")
    return await call_next(request)

def get_service() -> Calendars:
    """Lazily instantiate the CalDAVService from environment variables.

    This helper is used as a FastAPI dependency to ensure that a
    single instance of CalDAVService is created and reused across
    requests - minimizing initialization overhead. All configuration 
    is read from environment variables.
    """
    return load_calendars_from_env()

@app.get("/health", tags=["health"])
async def health(

        calendars: Calendars = Depends(get_service),
    ) -> JSONResponse:
    """Perform a simple health check of the service.

    Returns
    -------
    JSONResponse
        A JSON response indicating the health status of the service as well as the status of connected calendars.

    """
    health_caldav = calendars.health_check()
    return JSONResponse(content={"status": "ok", "calendars_status": health_caldav})

@app.get("/events/next/{days}", tags=["events"])
async def events_next(
    days: int,
    calendars: Calendars = Depends(get_service),
) -> JSONResponse:
    """Return events starting within the next ``days`` days.

    Parameters
    ----------
    days: int
        The positive integer number of days ahead to search for events.
    """
    if not days > 0:
        raise HTTPException(status_code=400, detail="days must be positive integer")
    try:
        results = calendars.get_events_next_days(days)
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e), headers={"X-Error": str(e)})