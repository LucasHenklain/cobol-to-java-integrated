"""
Migration jobs API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from app.services.database import get_session
from app.models.job import MigrationJob, Program, JobStatus
from app.crew.crew_manager import start_migration_job

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateJobRequest(BaseModel):
    """Create job request model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    repo_url: str = Field(..., min_length=1)
    branch: str = "main"
    target_stack: str = "springboot"
    selected_programs: Optional[List[str]] = None
    created_by: str = "demo_user"  # TODO: Extract from JWT token


class JobResponse(BaseModel):
    """Job response model"""
    id: str
    name: str
    description: Optional[str]
    repo_url: str
    branch: str
    target_stack: str
    status: str
    progress: int
    current_agent: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    metrics: Optional[dict]
    error_message: Optional[str]


class JobListResponse(BaseModel):
    """Job list response model"""
    total: int
    jobs: List[JobResponse]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: CreateJobRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new migration job
    """
    try:
        # Create job in database
        job = MigrationJob(
            name=request.name,
            description=request.description,
            repo_url=request.repo_url,
            branch=request.branch,
            target_stack=request.target_stack,
            selected_programs=request.selected_programs,
            created_by=request.created_by,
            status=JobStatus.PENDING
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"Created migration job: {job.id}")
        
        # Start migration job asynchronously
        # TODO: Use Celery task queue for production
        # For MVP, we'll start it directly
        try:
            await start_migration_job(job.id, db)
        except Exception as e:
            logger.error(f"Failed to start migration job {job.id}: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.commit()
        
        return JobResponse(**job.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    List migration jobs with pagination and filtering
    """
    try:
        # Build query
        query = select(MigrationJob)
        
        if status_filter:
            query = query.where(MigrationJob.status == status_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(MigrationJob)
        if status_filter:
            count_query = count_query.where(MigrationJob.status == status_filter)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get jobs
        query = query.order_by(MigrationJob.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return JobListResponse(
            total=total,
            jobs=[JobResponse(**job.to_dict()) for job in jobs]
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get job details by ID
    """
    try:
        result = await db.execute(
            select(MigrationJob).where(MigrationJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return JobResponse(**job.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}"
        )


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get job status and progress
    """
    try:
        result = await db.execute(
            select(MigrationJob).where(MigrationJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return {
            "job_id": job.id,
            "status": job.status.value,
            "progress": job.progress,
            "current_agent": job.current_agent,
            "metrics": job.metrics,
            "error_message": job.error_message,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Delete a migration job
    """
    try:
        result = await db.execute(
            select(MigrationJob).where(MigrationJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        await db.delete(job)
        await db.commit()
        
        logger.info(f"Deleted job: {job_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


@router.get("/{job_id}/programs")
async def get_job_programs(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get programs for a job
    """
    try:
        result = await db.execute(
            select(Program).where(Program.job_id == job_id)
        )
        programs = result.scalars().all()
        
        return {
            "job_id": job_id,
            "total": len(programs),
            "programs": [program.to_dict() for program in programs]
        }
        
    except Exception as e:
        logger.error(f"Failed to get programs for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get programs: {str(e)}"
        )
