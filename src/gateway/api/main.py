"""
FastAPI application for AI Command Gateway.
Provides REST API for Docker command execution via natural language intents.
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from gateway.config.settings import get_settings, Settings
from gateway.core.models import (
    GatewayRequest, 
    GatewayResponse, 
    HealthStatus,
    ErrorDetails
)

# Import prometheus client for metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    
    # Define custom metrics
    REQUEST_COUNT = Counter('gateway_requests_total', 'Total number of gateway requests', ['source_id', 'status'])
    REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Gateway request duration', ['source_id'])
    COMMAND_GENERATION_COUNT = Counter('gateway_command_generation_total', 'Total command generations', ['status'])
    COMMAND_EXECUTION_COUNT = Counter('gateway_command_execution_total', 'Total command executions', ['command_type', 'status'])
    ACTIVE_REQUESTS = Gauge('gateway_active_requests', 'Number of active requests')
    
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    try:
        settings = get_settings()
        
        logger.info(
            f"AI Command Gateway starting up",
            extra={
                "gateway_id": settings.gateway_instance_id,
                "execution_strategy": settings.execution_strategy,
                "log_level": settings.log_level
            }
        )
        
        # Validate configuration
        if settings.execution_strategy == "ssh":
            if not settings.ssh_target_host:
                raise ValueError("SSH configuration incomplete")
        
        logger.info("AI Command Gateway startup complete")
        
    except Exception as e:
        logger.error(f"FATAL: Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("AI Command Gateway shutting down")


# Create FastAPI application
app = FastAPI(
    title="AI Command Gateway",
    description="Intelligent execution bridge for Docker commands via natural language",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup middleware during app creation
try:
    settings = get_settings()
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
except Exception as e:
    logger.error(f"Failed to setup middleware: {e}")
    # Set basic CORS as fallback
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthStatus)
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint."""
    try:
        checks = {
            "configuration": "ok",
            "execution_strategy": settings.execution_strategy,
            "container_mappings": len(settings.get_container_name_mapping())
        }
        
        # Add strategy-specific checks
        if settings.execution_strategy == "ssh":
            checks.update({
                "ssh_host": settings.ssh_target_host,
                "ssh_user": settings.ssh_target_user,
                "ssh_key_configured": bool(settings.ssh_private_key_path)
            })
        
        return HealthStatus(
            status="healthy",
            checks=checks
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            checks={"error": str(e)}
        )


@app.post("/execute-docker-command", response_model=GatewayResponse)
async def execute_docker_command(
    request: GatewayRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Execute Docker command based on natural language intent.
    
    This is the main API endpoint that:
    1. Validates the incoming request
    2. Resolves logical service names to actual container names
    3. Generates Docker commands using LLM with enhanced context
    4. Executes commands using configured strategy
    5. Returns optimized structured response with execution results
    """
    # Start metrics tracking
    start_time = datetime.utcnow()
    if PROMETHEUS_AVAILABLE:
        ACTIVE_REQUESTS.inc()
    
    logger.info(
        f"Processing request",
        extra={
            "source_id": request.source_id,
            "target_name": request.target_resource.name,
            "intent": request.action_request.intent,
            "context": request.action_request.context,
            "priority": request.action_request.priority
        }
    )
    
    try:
        # Process request using complete gateway service
        from gateway.services.gateway_service import get_gateway_service
        
        gateway_service = get_gateway_service()
        response = await gateway_service.process_request(request)
        
        # Track metrics on success
        if PROMETHEUS_AVAILABLE:
            duration = (datetime.utcnow() - start_time).total_seconds()
            REQUEST_DURATION.labels(source_id=request.source_id).observe(duration)
            REQUEST_COUNT.labels(source_id=request.source_id, status=response.overall_status).inc()
            
            # Track command type if available
            if response.execution_details and response.execution_details.command:
                command_type = response.execution_details.command.split()[1] if len(response.execution_details.command.split()) > 1 else 'unknown'
                COMMAND_EXECUTION_COUNT.labels(
                    command_type=command_type, 
                    status=response.execution_details.execution_result.status
                ).inc()
        
        return response
        
    except Exception as e:
        # Track metrics on error
        if PROMETHEUS_AVAILABLE:
            duration = (datetime.utcnow() - start_time).total_seconds()
            REQUEST_DURATION.labels(source_id=request.source_id).observe(duration)
            REQUEST_COUNT.labels(source_id=request.source_id, status="INTERNAL_ERROR").inc()
        
        logger.error(
            f"Request processing failed",
            extra={
                "source_id": request.source_id,
                "error": str(e)
            }
        )
        
        return GatewayResponse(
            overall_status="INTERNAL_ERROR",
            error_details=ErrorDetails(
                error_code="GATEWAY_ERROR",
                error_message=str(e)
            )
        )
    finally:
        # Always decrement active requests
        if PROMETHEUS_AVAILABLE:
            ACTIVE_REQUESTS.dec()


@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Prometheus metrics endpoint."""
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(status_code=404, detail="Metrics not available")
    
    return generate_latest()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "gateway.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=True
    )