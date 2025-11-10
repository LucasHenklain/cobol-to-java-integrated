"""
Crew Manager - Orchestrates AI agents for COBOL to Java migration
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
import asyncio

from app.models.job import MigrationJob, Program, JobStatus
from app.crew.agents.inventory_agent import InventoryAgent
from app.crew.agents.parser_agent import COBOLParserAgent
from app.crew.agents.translator_agent import TranslatorAgent
from app.crew.agents.test_generator_agent import TestGeneratorAgent
from app.crew.agents.validator_agent import ValidatorAgent
from app.crew.agents.db_vetorial_agent import DBVetorialAgent
from app.crew.agents.ai_translator_agent import AITranslatorAgent

logger = logging.getLogger(__name__)


class CrewManager:
    """
    Manages the crew of AI agents for migration tasks
    """
    
    def __init__(self, job_id: str, db_session: AsyncSession):
        self.job_id = job_id
        self.db = db_session
        self.job = None
        
        # Initialize agents
        self.inventory_agent = InventoryAgent()
        self.parser_agent = COBOLParserAgent()
        self.translator_agent = TranslatorAgent()
        self.test_generator_agent = TestGeneratorAgent()
        self.validator_agent = ValidatorAgent()
        self.db_vetorial_agent = DBVetorialAgent()
        self.ai_translator_agent = AITranslatorAgent()
    
    async def load_job(self):
        """Load job from database"""
        result = await self.db.execute(
            select(MigrationJob).where(MigrationJob.id == self.job_id)
        )
        self.job = result.scalar_one_or_none()
        
        if not self.job:
            raise ValueError(f"Job {self.job_id} not found")
    
    async def update_job_status(self, status: JobStatus, progress: int = None, 
                               current_agent: str = None, error_message: str = None):
        """Update job status in database"""
        if not self.job:
            await self.load_job()
        
        self.job.status = status
        
        if progress is not None:
            self.job.progress = progress
        
        if current_agent:
            self.job.current_agent = current_agent
        
        if error_message:
            self.job.error_message = error_message
        
        if status == JobStatus.RUNNING and not self.job.started_at:
            self.job.started_at = datetime.utcnow()
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            self.job.completed_at = datetime.utcnow()
        
        self.job.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(self.job)
    
    async def run(self):
        """
        Execute the migration workflow
        
        Workflow:
        1. InventoryAgent - Scan repository and list programs
        2. COBOLParserAgent - Parse COBOL programs and generate AST
        3. TranslatorAgent - Translate COBOL to Java
        4. TestGeneratorAgent - Generate JUnit tests
        5. ValidatorAgent - Validate and run tests
        """
        try:
            await self.load_job()
            
            logger.info(f"Starting migration job: {self.job_id}")
            await self.update_job_status(JobStatus.RUNNING, progress=0)
            
            # Step 1: Inventory - Scan repository
            logger.info(f"[{self.job_id}] Running InventoryAgent...")
            await self.update_job_status(JobStatus.RUNNING, progress=10, 
                                        current_agent="InventoryAgent")
            
            inventory_result = await self.inventory_agent.run({
                "job_id": self.job_id,
                "repo_url": self.job.repo_url,
                "branch": self.job.branch,
                "selected_programs": self.job.selected_programs
            })
            
            if not inventory_result.get("success"):
                raise Exception(f"InventoryAgent failed: {inventory_result.get('error')}")
            
            programs = inventory_result.get("programs", [])
            logger.info(f"[{self.job_id}] Found {len(programs)} programs")
            
            # Create program records in database
            for prog_info in programs:
                program = Program(
                    job_id=self.job_id,
                    file_path=prog_info["path"],
                    program_name=prog_info["name"],
                    status=JobStatus.PENDING
                )
                self.db.add(program)
            
            await self.db.commit()
            
            # Step 2: Parse COBOL programs
            logger.info(f"[{self.job_id}] Running COBOLParserAgent...")
            await self.update_job_status(JobStatus.RUNNING, progress=30,
                                        current_agent="COBOLParserAgent")
            
            parser_result = await self.parser_agent.run({
                "job_id": self.job_id,
                "programs": programs,
                "repo_path": inventory_result.get("repo_path")
            })
            
            if not parser_result.get("success"):
                raise Exception(f"COBOLParserAgent failed: {parser_result.get('error')}")
            
            # Step 3: Translate to Java
            logger.info(f"[{self.job_id}] Running TranslatorAgent...")
            await self.update_job_status(JobStatus.RUNNING, progress=50,
                                        current_agent="TranslatorAgent")
            
            translator_result = await self.translator_agent.run({
                "job_id": self.job_id,
                "programs": programs,
                "ast_data": parser_result.get("ast_data"),
                "target_stack": self.job.target_stack
            })
            
            if not translator_result.get("success"):
                raise Exception(f"TranslatorAgent failed: {translator_result.get('error')}")
            
            ##

            await self.db_vetorial_agent.run({
                "job_id": self.job_id,
                "programs": programs,
                "java_files": translator_result.get("java_files")
            })


            await self.ai_translator_agent.run({
                "job_id": self.job_id,
                "programs": programs,
                "java_files": translator_result.get("java_files")
            })

            # Step 4: Generate tests
            logger.info(f"[{self.job_id}] Running TestGeneratorAgent...")
            await self.update_job_status(JobStatus.RUNNING, progress=70,
                                        current_agent="TestGeneratorAgent")
            
            test_gen_result = await self.test_generator_agent.run({
                "job_id": self.job_id,
                "programs": programs,
                "java_files": translator_result.get("java_files")
            })
            
            if not test_gen_result.get("success"):
                raise Exception(f"TestGeneratorAgent failed: {test_gen_result.get('error')}")
            
            # Step 5: Validate
            logger.info(f"[{self.job_id}] Running ValidatorAgent...")
            await self.update_job_status(JobStatus.RUNNING, progress=85,
                                        current_agent="ValidatorAgent")
            
            validator_result = await self.validator_agent.run({
                "job_id": self.job_id,
                "programs": programs,
                "java_files": translator_result.get("java_files"),
                "test_files": test_gen_result.get("test_files")
            })
            
            if not validator_result.get("success"):
                logger.warning(f"ValidatorAgent reported issues: {validator_result.get('error')}")
            
            # Collect metrics
            metrics = {
                "programs_processed": len(programs),
                "programs_translated": translator_result.get("translated_count", 0),
                "tests_generated": test_gen_result.get("tests_count", 0),
                "tests_passed": validator_result.get("tests_passed", 0),
                "tests_failed": validator_result.get("tests_failed", 0),
                "validation_success": validator_result.get("success", False)
            }
            
            self.job.metrics = metrics
            
            # Complete job
            logger.info(f"[{self.job_id}] Migration job completed successfully")
            await self.update_job_status(JobStatus.COMPLETED, progress=100,
                                        current_agent="Completed")
            
            return {
                "success": True,
                "job_id": self.job_id,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"[{self.job_id}] Migration job failed: {e}", exc_info=True)
            await self.update_job_status(JobStatus.FAILED, error_message=str(e))
            
            return {
                "success": False,
                "job_id": self.job_id,
                "error": str(e)
            }


async def start_migration_job(job_id: str, db_session: AsyncSession):
    """
    Start a migration job
    
    This function should be called asynchronously (e.g., via Celery task)
    For MVP, we call it directly
    """
    manager = CrewManager(job_id, db_session)
    result = await manager.run()
    return result
