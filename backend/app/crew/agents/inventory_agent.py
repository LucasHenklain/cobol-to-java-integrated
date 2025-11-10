"""
Inventory Agent - Scans repositories and lists COBOL programs
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

from app.services.repository import clone_or_update_repository

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

            repo_path, commit_hash, resolved_branch = await asyncio.to_thread(
                clone_or_update_repository,
                job_id,
                repo_url,
                branch
            )
            
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
                "commit_hash": commit_hash,
                "branch": resolved_branch,
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
    
    def _scan_cobol_files(self, repo_path: str, selected_programs: List[str] = None) -> List[Dict]:
        """Scan for COBOL program files"""
        programs = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.cobol_extensions):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)

                    if selected_programs:
                        normalized = {p.lower() for p in selected_programs}
                        if (
                            rel_path.lower() not in normalized
                            and Path(rel_path).name.lower() not in normalized
                        ):
                            continue

                    programs.append({
                        "path": file_path,
                        "relative_path": rel_path,
                        "name": Path(file).stem,
                        "extension": Path(file).suffix,
                        "size_bytes": os.path.getsize(file_path),
                        "lines_of_code": self._count_lines_of_code(file_path),
                        "copybooks": self._extract_copybooks(file_path)
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

    def _count_lines_of_code(self, file_path: str) -> int:
        """Count non-empty lines of code in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for line in f if line.strip())
        except OSError:
            return 0

    def _extract_copybooks(self, file_path: str) -> List[str]:
        """Extract COPY statements to identify copybook dependencies."""
        copybooks = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_upper = line.upper()
                    if " COPY " in line_upper:
                        parts = line_upper.strip().replace(".", "").split()
                        if "COPY" in parts:
                            idx = parts.index("COPY")
                            if idx + 1 < len(parts):
                                copybooks.append(parts[idx + 1])
        except OSError:
            pass
        return copybooks
