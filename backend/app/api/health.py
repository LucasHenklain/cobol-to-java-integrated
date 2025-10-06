"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import logging

from app.services.database import get_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cobol-to-java-migration"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_session)):
    """Detailed health check with dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection OK"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    # Check Redis (TODO: implement when Redis is configured)
    health_status["checks"]["redis"] = {
        "status": "not_configured",
        "message": "Redis check not implemented"
    }
    
    # Check S3 (TODO: implement when S3 is configured)
    health_status["checks"]["storage"] = {
        "status": "not_configured",
        "message": "Storage check not implemented"
    }
    
    return health_status
