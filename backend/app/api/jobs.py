"""
Migration jobs API endpoints
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import settings
from app.crew.crew_manager import start_migration_job
from app.models.job import JobStatus, MigrationJob, Program
from app.services.database import get_session, session_scope


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


class JobSummary(BaseModel):
    """Aggregate job summary"""
    status_counts: Dict[str, int]
    average_progress: float
    running_jobs: int


class JobListResponse(BaseModel):
    """Job list response model"""
    total: int
    jobs: List[JobResponse]
    summary: Optional[JobSummary] = None


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

    # dentro da função create_job, após criar e commitar o job:
        logger.info(f"Created migration job: {job.id}")

        async def _background_start(job_id: str):
            try:
                async with session_scope() as session:
                    await start_migration_job(job_id, session)
            except Exception as exc:
                logger.exception("Background migration job %s failed: %s", job_id, exc)

        # start background task with its own DB session
        task = asyncio.create_task(_background_start(job.id))
        task.add_done_callback(
            lambda t: logger.error(
                "Migration job %s failed: %s", job.id, t.exception()
            ) if t.exception() else None
        )

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
        status_enum: Optional[JobStatus] = None

        if status_filter:
            try:
                status_enum = JobStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
            query = query.where(MigrationJob.status == status_enum)

        # Get total count
        count_query = select(func.count()).select_from(MigrationJob)
        if status_enum:
            count_query = count_query.where(MigrationJob.status == status_enum)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get jobs
        query = query.order_by(MigrationJob.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()

        summary = await _build_summary(db, status_enum)

        return JobListResponse(
            total=total,
            jobs=[JobResponse(**job.to_dict()) for job in jobs],
            summary=summary
        )

    except HTTPException:
        raise
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


def _safe_read_text(path: Optional[str]) -> Optional[str]:
    """Safely read a text file returning None if missing or unreadable."""
    if not path:
        return None

    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _ensure_java_files(
    job_id: str,
    java_files: Dict[str, Dict[str, Any]],
    programs: List[Program]
) -> Dict[str, Dict[str, Any]]:
    """Ensure we have Java artifact metadata, discovering files if metrics are empty."""

    if not isinstance(java_files, dict):
        java_files = {}

    cleaned: Dict[str, Dict[str, Any]] = {}
    for key, info in java_files.items():
        if isinstance(info, dict):
            cleaned[key] = info
    java_files = cleaned

    program_index = {program.program_name.lower(): program for program in programs}

    if java_files:
        for key, info in java_files.items():
            if not info.get("program_id"):
                program = program_index.get(key.lower())
                if program:
                    info["program_id"] = program.id
        return java_files

    output_dir = Path(settings.ARTIFACTS_DIR) / job_id / "java"
    if not output_dir.exists():
        logger.warning(
            "[Job %s] Translator metrics missing and output directory %s not found",
            job_id,
            output_dir
        )
        return {}

    discovered: Dict[str, Dict[str, Any]] = {}
    for java_file in output_dir.glob("**/*.java"):
        class_name = java_file.stem
        program = program_index.get(class_name.lower())
        discovered[class_name] = {
            "program_id": program.id if program else None,
            "path": str(java_file),
            "class_name": class_name,
            "package": "com.ford.migration.cobol",
        }

    logger.info(
        "[Job %s] Discovered %d java files directly from %s",
        job_id,
        len(discovered),
        output_dir
    )

    return discovered


@router.get("/{job_id}/artifacts")
async def get_job_artifacts(
    job_id: str,
    db: AsyncSession = Depends(get_session)
):
    """Return aggregated artifacts and contents generated for a job."""
    try:
        result = await db.execute(select(MigrationJob).where(MigrationJob.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        metrics = job.metrics or {}
        inventory_metrics = metrics.get("inventory", {})
        parser_metrics = metrics.get("parser", {})
        translator_metrics = metrics.get("translator", {})
        tests_metrics = metrics.get("tests", {})
        validation_metrics = metrics.get("validation", {})
        pipeline_metrics = metrics.get("pipeline", {})

        programs_result = await db.execute(
            select(Program).where(Program.job_id == job_id)
        )
        programs = programs_result.scalars().all()

        repo_path = inventory_metrics.get("repo_path")
        java_files = translator_metrics.get("java_files") or {}
        test_files = tests_metrics.get("test_files", {})
        validation_results = validation_metrics.get("validation_results", {})

        logger.info(
            "[Job %s] Assembling artifacts: %d programs, %d java files, %d test files",
            job_id,
            len(programs),
            len(java_files),
            len(test_files)
        )

        java_files = _ensure_java_files(job_id, java_files, programs)

        java_files_by_id = {
            info.get("program_id"): info
            for info in java_files.values()
            if isinstance(info, dict) and info.get("program_id")
        }
        test_files_by_id = {
            info.get("program_id"): info
            for info in test_files.values()
            if isinstance(info, dict) and info.get("program_id")
        }

        artifacts: List[Dict] = []

        java_output_dir = Path(settings.ARTIFACTS_DIR) / job_id / "java"
        tests_output_dir = Path(settings.ARTIFACTS_DIR) / job_id / "tests"
        default_java_package = next(
            (info.get("package") for info in java_files.values()
             if isinstance(info, dict) and info.get("package")),
            "com.ford.migration.cobol"
        )

        for program in programs:
            # Try to construct COBOL path from repo_path
            cobol_path = None
            cobol_content = None
            
            if repo_path:
                cobol_path = str(Path(repo_path) / program.file_path)
                cobol_content = _safe_read_text(cobol_path)
            
            # Fallback: Try to find COBOL file in common repository locations
            if not cobol_content and program.file_path:
                # Try in the standard cloned repositories location
                potential_paths = [
                    Path(settings.REPOS_DIR) / job_id / program.file_path,
                    Path(settings.TEMP_DIR) / "repos" / job_id / program.file_path,
                ]
                
                for potential_path in potential_paths:
                    if potential_path.exists():
                        cobol_path = str(potential_path)
                        cobol_content = _safe_read_text(cobol_path)
                        logger.info(
                            "[Job %s] Found COBOL file via fallback: %s",
                            job_id,
                            potential_path
                        )
                        break

            java_info = (
                java_files.get(program.program_name)
                or java_files_by_id.get(program.id)
                or next(
                    (info for key, info in java_files.items()
                     if key.lower() == program.program_name.lower()),
                    None
                )
            )

            if not java_info:
                candidate = java_output_dir / f"{program.program_name}.java"
                if candidate.exists():
                    java_info = {
                        "program_id": program.id,
                        "path": str(candidate),
                        "class_name": candidate.stem,
                        "package": default_java_package,
                    }
                    logger.info(
                        "[Job %s] Reconstructed Java artifact for %s from %s",
                        job_id,
                        program.program_name,
                        candidate
                    )

            java_payload = None
            if java_info:
                java_path = java_info.get("path")
                java_info.setdefault("program_id", program.id)
                java_payload = {**java_info, "content": _safe_read_text(java_path)}
            else:
                logger.warning(
                    "[Job %s] Missing Java artifact for program %s (available keys: %s)",
                    job_id,
                    program.program_name,
                    list(java_files.keys())
                )

            test_info = (
                test_files.get(program.program_name)
                or test_files_by_id.get(program.id)
                or next(
                    (info for key, info in test_files.items()
                     if key.lower() == program.program_name.lower()),
                    None
                )
            )

            if not test_info:
                fallback_candidates = [
                    tests_output_dir / f"{program.program_name}Test.java",
                    java_output_dir / f"{program.program_name}Test.java"
                ]
                for candidate in fallback_candidates:
                    if candidate.exists():
                        test_info = {
                            "program_id": program.id,
                            "path": str(candidate),
                            "class_name": candidate.stem,
                        }
                        break

            test_payload = None
            if test_info:
                test_path = test_info.get("path")
                test_payload = {**test_info, "content": _safe_read_text(test_path)}

            validation_info = validation_results.get(program.program_name)

            artifacts.append({
                "program": program.to_dict(),
                "cobol": {
                    "path": cobol_path,
                    "content": cobol_content
                },
                "java": java_payload,
                "test": test_payload,
                "validation": validation_info
            })

        return {
            "job": job.to_dict(),
            "artifacts": artifacts,
            "inventory": inventory_metrics,
            "parser": parser_metrics,
            "translator": translator_metrics,
            "tests": tests_metrics,
            "validation": validation_metrics,
            "pipeline": pipeline_metrics,
            "debug_java_keys": list(java_files.keys()),
            "debug_java_dir": str(java_output_dir)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifacts for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get artifacts: {str(e)}"
        )


async def _build_summary(
    db: AsyncSession,
    status_filter: Optional[JobStatus]
) -> Optional[JobSummary]:
    """Aggregate job metrics for dashboard consumption."""
    try:
        status_query = select(MigrationJob.status, func.count()).group_by(MigrationJob.status)
        if status_filter:
            status_query = status_query.where(MigrationJob.status == status_filter)

        status_results = await db.execute(status_query)
        status_counts = {status.value: count for status, count in status_results.all()}

        avg_query = select(func.avg(MigrationJob.progress))
        if status_filter:
            avg_query = avg_query.where(MigrationJob.status == status_filter)

        avg_result = await db.execute(avg_query)
        average_progress = avg_result.scalar() or 0.0

        running_jobs = status_counts.get(JobStatus.RUNNING.value, 0)

        return JobSummary(
            status_counts=status_counts,
            average_progress=float(average_progress),
            running_jobs=running_jobs
        )
    except Exception as exc:
        logger.warning(f"Failed to build job summary: {exc}")
        return None
