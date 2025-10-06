"""
Database models for migration jobs
"""

from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVIEWING = "reviewing"


class ArtifactType(str, enum.Enum):
    """Artifact type enumeration"""
    JAVA_SOURCE = "java_source"
    TEST_SOURCE = "test_source"
    DOCUMENTATION = "documentation"
    BUILD_CONFIG = "build_config"
    AST = "ast"
    INVENTORY = "inventory"


class ReviewStatus(str, enum.Enum):
    """Review status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class MigrationJob(Base):
    """Migration job model"""
    __tablename__ = "migration_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Repository information
    repo_url = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    commit_hash = Column(String(40), nullable=True)
    
    # Configuration
    target_stack = Column(String(50), default="springboot")
    selected_programs = Column(JSON, nullable=True)  # List of program paths
    mapping_rules_id = Column(String(36), nullable=True)
    
    # Status
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    current_agent = Column(String(100), nullable=True)
    
    # Metadata
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Metrics
    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    programs = relationship("Program", back_populates="job", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "repo_url": self.repo_url,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "target_stack": self.target_stack,
            "selected_programs": self.selected_programs,
            "status": self.status.value,
            "progress": self.progress,
            "current_agent": self.current_agent,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metrics": self.metrics,
            "error_message": self.error_message
        }


class Program(Base):
    """COBOL program model"""
    __tablename__ = "programs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("migration_jobs.id"), nullable=False)
    
    # Program information
    file_path = Column(String(500), nullable=False)
    program_name = Column(String(255), nullable=False)
    
    # Analysis
    cyclomatic_complexity = Column(Integer, nullable=True)
    lines_of_code = Column(Integer, nullable=True)
    io_type = Column(String(50), nullable=True)  # file, db, batch, online
    copybooks = Column(JSON, nullable=True)  # List of copybook dependencies
    
    # Status
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    translator_version = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("MigrationJob", back_populates="programs")
    artifacts = relationship("Artifact", back_populates="program", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "file_path": self.file_path,
            "program_name": self.program_name,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "lines_of_code": self.lines_of_code,
            "io_type": self.io_type,
            "copybooks": self.copybooks,
            "status": self.status.value,
            "translator_version": self.translator_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Artifact(Base):
    """Generated artifact model"""
    __tablename__ = "artifacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=False)
    
    # Artifact information
    artifact_type = Column(SQLEnum(ArtifactType), nullable=False)
    file_name = Column(String(255), nullable=False)
    s3_path = Column(String(500), nullable=False)
    
    # Git information
    commit_hash = Column(String(40), nullable=True)
    pr_url = Column(String(500), nullable=True)
    
    # Metadata
    size_bytes = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    program = relationship("Program", back_populates="artifacts")
    reviews = relationship("Review", back_populates="artifact", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "program_id": self.program_id,
            "artifact_type": self.artifact_type.value,
            "file_name": self.file_name,
            "s3_path": self.s3_path,
            "commit_hash": self.commit_hash,
            "pr_url": self.pr_url,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Review(Base):
    """Human review model"""
    __tablename__ = "reviews"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String(36), ForeignKey("artifacts.id"), nullable=False)
    
    # Review information
    reviewer_id = Column(String(100), nullable=False)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    comments = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    artifact = relationship("Artifact", back_populates="reviews")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "artifact_id": self.artifact_id,
            "reviewer_id": self.reviewer_id,
            "status": self.status.value,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None
        }
