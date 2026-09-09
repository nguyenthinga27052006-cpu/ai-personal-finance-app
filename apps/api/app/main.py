import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.accounts.routes import router as accounts_router
from app.ai.routes import router as ai_router
from app.analytics.routes import router as analytics_router
from app.auth.routes import me_router
from app.auth.routes import router as auth_router
from app.budget_goals.routes import router as budget_goals_router
from app.catalog.routes import router as catalog_router
from app.core.config import get_settings
from app.dashboard.routes import router as dashboard_router
from app.health import router as health_router
from app.insights.routes import router as insights_router
from app.notifications.routes import router as notifications_router
from app.observability import (
	configure_logging,
	correlation_ids,
	metrics,
	request_id_context,
	trace_id_context,
)
from app.recommendations.routes import router as recommendations_router
from app.transactions.routes import router as transactions_router
from app.transactions.routes import transfer_router

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
	started = time.perf_counter()
	request_id, trace_id = correlation_ids(request)
	request_token = request_id_context.set(request_id)
	trace_token = trace_id_context.set(trace_id)
	try:
		content_length = request.headers.get("content-length")
		if content_length and content_length.isdigit() and int(content_length) > 1_000_000:
			response = JSONResponse(
				status_code=413, content={"detail": "Request body is too large"}
			)
		else:
			response = await call_next(request)
		response.headers["X-Content-Type-Options"] = "nosniff"
		response.headers["X-Frame-Options"] = "DENY"
		response.headers["Referrer-Policy"] = "no-referrer"
		response.headers["Cache-Control"] = "no-store"
		response.headers["X-Request-ID"] = request_id
		response.headers["X-Trace-ID"] = trace_id
		metrics.observe_request(
			request.url.path,
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
		request_id_context.reset(request_token)
		trace_id_context.reset(trace_token)


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint() -> PlainTextResponse:
	return PlainTextResponse(metrics.prometheus(), media_type="text/plain; version=0.0.4")
app.include_router(health_router)
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
