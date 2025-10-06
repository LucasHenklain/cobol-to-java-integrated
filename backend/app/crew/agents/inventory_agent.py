"""
Inventory Agent - Scans repositories and lists COBOL programs
"""

import os
import logging
from pathlib import Path
import tempfile
import shutil
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class InventoryAgent:
    """
    Agent responsible for scanning COBOL repositories
    and creating an inventory of programs, copybooks, and JCL files
    """
    
    def __init__(self):
        self.name = "InventoryAgent"
        self.cobol_extensions = [".cbl", ".cob", ".cobol"]
        self.copybook_extensions = [".cpy", ".copy"]
        self.jcl_extensions = [".jcl"]
    
    async def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute inventory scan
        
        Args:
            task_input: Dictionary containing:
                - job_id: Job identifier
                - repo_url: Git repository URL
                - branch: Git branch name
                - selected_programs: Optional list of specific programs to process
        
        Returns:
            Dictionary with scan results
        """
        try:
            job_id = task_input["job_id"]
            repo_url = task_input["repo_url"]
            branch = task_input.get("branch", "main")
            selected_programs = task_input.get("selected_programs")
            
            logger.info(f"[{job_id}] Starting repository scan: {repo_url}")
            
            # For MVP, we'll simulate repository cloning
            # In production, use GitPython to clone the repository
            repo_path = self._simulate_repo_clone(repo_url, branch, job_id)
            
            # Scan for COBOL files
            programs = self._scan_cobol_files(repo_path, selected_programs)
            
            # Scan for copybooks
            copybooks = self._scan_copybooks(repo_path)
            
            # Scan for JCL files
            jcl_files = self._scan_jcl_files(repo_path)
            
            logger.info(f"[{job_id}] Scan complete: {len(programs)} programs, "
                       f"{len(copybooks)} copybooks, {len(jcl_files)} JCL files")
            
            return {
                "success": True,
                "job_id": job_id,
                "repo_path": repo_path,
                "programs": programs,
                "copybooks": copybooks,
                "jcl_files": jcl_files,
                "summary": {
                    "total_programs": len(programs),
                    "total_copybooks": len(copybooks),
                    "total_jcl": len(jcl_files)
                }
            }
            
        except Exception as e:
            logger.error(f"InventoryAgent failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _simulate_repo_clone(self, repo_url: str, branch: str, job_id: str) -> str:
        """
        Simulate repository cloning for MVP
        In production, use GitPython to actually clone the repository
        """
        # Create temporary directory for this job
        temp_dir = tempfile.mkdtemp(prefix=f"cobol_migration_{job_id}_")
        
        # For MVP, create sample COBOL files
        self._create_sample_cobol_files(temp_dir)
        
        logger.info(f"Simulated repo clone to: {temp_dir}")
        return temp_dir
    
    def _create_sample_cobol_files(self, base_path: str):
        """Create sample COBOL files for demonstration"""
        
        # Create directory structure
        src_dir = Path(base_path) / "src" / "cobol"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        copybook_dir = Path(base_path) / "copybooks"
        copybook_dir.mkdir(parents=True, exist_ok=True)
        
        # Sample COBOL program 1
        sample_program_1 = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO-WORLD.
       AUTHOR. MIGRATION-SYSTEM.
       
       ENVIRONMENT DIVISION.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-MESSAGE        PIC X(30) VALUE 'Hello from COBOL!'.
       01  WS-COUNTER        PIC 9(4) VALUE ZERO.
       
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           DISPLAY WS-MESSAGE.
           PERFORM PROCESS-LOOP 10 TIMES.
           STOP RUN.
       
       PROCESS-LOOP.
           ADD 1 TO WS-COUNTER.
           DISPLAY 'Counter: ' WS-COUNTER.
"""
        
        with open(src_dir / "HELLO.cbl", "w") as f:
            f.write(sample_program_1)
        
        # Sample COBOL program 2
        sample_program_2 = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALCULATOR.
       
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-NUM1           PIC 9(5) VALUE 100.
       01  WS-NUM2           PIC 9(5) VALUE 200.
       01  WS-RESULT         PIC 9(6) VALUE ZERO.
       
       PROCEDURE DIVISION.
       MAIN-PARA.
           COMPUTE WS-RESULT = WS-NUM1 + WS-NUM2.
           DISPLAY 'Result: ' WS-RESULT.
           STOP RUN.
"""
        
        with open(src_dir / "CALC.cbl", "w") as f:
            f.write(sample_program_2)
        
        # Sample copybook
        sample_copybook = """       01  CUSTOMER-RECORD.
           05  CUST-ID           PIC 9(10).
           05  CUST-NAME         PIC X(50).
           05  CUST-ADDRESS      PIC X(100).
           05  CUST-PHONE        PIC X(15).
"""
        
        with open(copybook_dir / "CUSTOMER.cpy", "w") as f:
            f.write(sample_copybook)
        
        logger.info(f"Created sample COBOL files in {base_path}")
    
    def _scan_cobol_files(self, repo_path: str, selected_programs: List[str] = None) -> List[Dict]:
        """Scan for COBOL program files"""
        programs = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.cobol_extensions):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # If specific programs selected, filter
                    if selected_programs and rel_path not in selected_programs:
                        continue
                    
                    programs.append({
                        "path": file_path,
                        "relative_path": rel_path,
                        "name": Path(file).stem,
                        "extension": Path(file).suffix,
                        "size_bytes": os.path.getsize(file_path)
                    })
        
        return programs
    
    def _scan_copybooks(self, repo_path: str) -> List[Dict]:
        """Scan for copybook files"""
        copybooks = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.copybook_extensions):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    copybooks.append({
                        "path": file_path,
                        "relative_path": rel_path,
                        "name": Path(file).stem,
                        "size_bytes": os.path.getsize(file_path)
                    })
        
        return copybooks
    
    def _scan_jcl_files(self, repo_path: str) -> List[Dict]:
        """Scan for JCL files"""
        jcl_files = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.jcl_extensions):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    jcl_files.append({
                        "path": file_path,
                        "relative_path": rel_path,
                        "name": Path(file).stem,
                        "size_bytes": os.path.getsize(file_path)
                    })
        
        return jcl_files
