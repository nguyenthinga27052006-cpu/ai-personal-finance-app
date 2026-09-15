import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.accounts.routes import router as accounts_router
from app.admin.routes import router as admin_router
from app.ai.routes import router as ai_router
from app.analytics.routes import router as analytics_router
from app.auth.routes import me_router
from app.auth.routes import router as auth_router
from app.budget_goals.routes import router as budget_goals_router
from app.catalog.routes import router as catalog_router
from app.core.config import get_settings
from app.dashboard.routes import router as dashboard_router
from app.error_tracking import LocalErrorTracker
from app.health import router as health_router
from app.insights.routes import router as insights_router
from app.notifications.routes import router as notifications_router
from app.observability import configure_logging, metrics
from app.recommendations.routes import router as recommendations_router
from app.tracing import (
	extract_trace_context,
	request_id_context,
	set_current_trace,
	span_id_context,
	trace_id_context,
)
from contextlib import asynccontextmanager
from app.transactions.routes import router as transactions_router
from app.transactions.routes import transfer_router

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.db.session import SessionLocal
        from app.db.seed import seed_system_categories, seed_super_admin
        session = SessionLocal()
        try:
            seed_system_categories(session)
            seed_super_admin(session)
        finally:
            session.close()
    except Exception as exc:
        logger.warning(f"Auto-seed on startup skipped or failed: {exc}")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://10.0.2.2:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|10\.0\.2\.2)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

error_tracker = LocalErrorTracker(release=settings.release, environment=settings.app_env)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
	started = time.perf_counter()
	trace_context = extract_trace_context(request)
	request_id, trace_id = trace_context.request_id, trace_context.trace_id
	request.state.observability = trace_context
	current_tokens = set_current_trace(trace_context)
	try:
		content_length = request.headers.get("content-length")
		if content_length and content_length.isdigit() and int(content_length) > 1_000_000:
			response = JSONResponse(
				status_code=413, content={"detail": "Request body is too large"}
			)
		else:
			try:
				response = await call_next(request)
			except Exception as exc:
				error_tracker.capture_exception(
					exc,
					request_id=request_id,
					trace_id=trace_id,
					context={"method": request.method, "path": request.url.path},
					traceback=exc.__traceback__,
				)
				request.state.error_captured = True
				raise
		response.headers["X-Content-Type-Options"] = "nosniff"
		response.headers["X-Frame-Options"] = "DENY"
		response.headers["Referrer-Policy"] = "no-referrer"
		response.headers["Cache-Control"] = "no-store"
		response.headers["X-Request-ID"] = request_id
		response.headers["X-Trace-ID"] = trace_id
		response.headers["X-Span-ID"] = span_id_context.get()
		metrics.observe_request(
			getattr(request.scope.get("route"), "path", request.url.path),
			request.method,
			response.status_code,
			(time.perf_counter() - started) * 1000,
		)
		logger.info(
			"http_request",
			extra={"route": request.url.path, "status": response.status_code},
		)
		return response
	finally:
		from app.tracing import reset_current_trace
		reset_current_trace(current_tokens)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
	trace_context = getattr(request.state, "observability", None)
	request_id = trace_context.request_id if trace_context else request_id_context.get()
	trace_id = trace_context.trace_id if trace_context else trace_id_context.get()
	if not getattr(request.state, "error_captured", False):
		error_tracker.capture_exception(
			exc,
			request_id=request_id,
			trace_id=trace_id,
			context={"method": request.method, "path": request.url.path},
			traceback=exc.__traceback__,
		)
	return JSONResponse(
		status_code=500,
		content={
			"detail": "Internal server error",
			"request_id": request_id,
			"trace_id": trace_id,
		},
		headers={"X-Request-ID": request_id, "X-Trace-ID": trace_id},
	)


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint() -> PlainTextResponse:
	return PlainTextResponse(metrics.prometheus(), media_type="text/plain; version=0.0.4")
app.include_router(health_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(accounts_router)
app.include_router(catalog_router)
app.include_router(transactions_router)
app.include_router(transfer_router)
app.include_router(budget_goals_router)
app.include_router(analytics_router)
app.include_router(insights_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(recommendations_router)
app.include_router(ai_router)
