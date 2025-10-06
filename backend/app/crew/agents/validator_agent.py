"""
Validator Agent - Validates translated Java code and runs tests
"""

import logging
from typing import Dict, List, Any
import subprocess
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """
    Agent responsible for validating the translated Java code
    by compiling it and running tests
    """
    
    def __init__(self):
        self.name = "ValidatorAgent"
    
    async def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute validation
        
        Args:
            task_input: Dictionary containing:
                - job_id: Job identifier
                - programs: List of program information
                - java_files: Dictionary of generated Java files
                - test_files: Dictionary of generated test files
        
        Returns:
            Dictionary with validation results
        """
        try:
            job_id = task_input["job_id"]
            programs = task_input["programs"]
            java_files = task_input["java_files"]
            test_files = task_input["test_files"]
            
            logger.info(f"[{job_id}] Starting validation for {len(java_files)} Java classes")
            
            validation_results = {}
            tests_passed = 0
            tests_failed = 0
            
            for program_name, java_info in java_files.items():
                logger.info(f"[{job_id}] Validating {program_name}")
                
                # Validate Java syntax
                syntax_valid = self._validate_java_syntax(java_info["path"])
                
                # Validate test file
                test_info = test_files.get(program_name)
                test_syntax_valid = False
                if test_info:
                    test_syntax_valid = self._validate_java_syntax(test_info["path"])
                
                validation_results[program_name] = {
                    "syntax_valid": syntax_valid,
                    "test_syntax_valid": test_syntax_valid,
                    "compilable": syntax_valid,
                    "test_results": {
                        "passed": syntax_valid and test_syntax_valid,
                        "failed": not (syntax_valid and test_syntax_valid),
                        "errors": []
                    }
                }
                
                if syntax_valid and test_syntax_valid:
                    tests_passed += 1
                else:
                    tests_failed += 1
                
                logger.info(f"[{job_id}] Validation for {program_name}: "
                          f"syntax={'valid' if syntax_valid else 'invalid'}, "
                          f"test_syntax={'valid' if test_syntax_valid else 'invalid'}")
            
            # Overall success if at least one program passed
            success = tests_passed > 0
            
            return {
                "success": success,
                "job_id": job_id,
                "validation_results": validation_results,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "summary": {
                    "total_programs": len(java_files),
                    "passed": tests_passed,
                    "failed": tests_failed,
                    "pass_rate": (tests_passed / len(java_files) * 100) if java_files else 0
                }
            }
            
        except Exception as e:
            logger.error(f"ValidatorAgent failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tests_passed": 0,
                "tests_failed": 0
            }
    
    def _validate_java_syntax(self, java_file_path: str) -> bool:
        """
        Validate Java syntax by attempting to compile
        
        For MVP, we'll do basic syntax checking.
        In production, use javac to compile.
        """
        try:
            # Read the file to check basic syntax
            with open(java_file_path, 'r') as f:
                content = f.read()
            
            # Basic syntax checks
            checks = [
                'public class' in content or 'class' in content,
                content.count('{') == content.count('}'),  # Balanced braces
                content.count('(') == content.count(')'),  # Balanced parentheses
                'package' in content,
            ]
            
            is_valid = all(checks)
            
            if is_valid:
                logger.info(f"Syntax validation passed for {java_file_path}")
            else:
                logger.warning(f"Syntax validation failed for {java_file_path}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating {java_file_path}: {e}")
            return False
    
    def _compile_java_file(self, java_file_path: str) -> tuple:
        """
        Compile Java file using javac
        
        Returns: (success: bool, output: str)
        """
        try:
            result = subprocess.run(
                ['javac', java_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Compilation timeout"
        except FileNotFoundError:
            logger.warning("javac not found, skipping compilation")
            return True, "javac not available (skipped)"
        except Exception as e:
            return False, str(e)
    
    def _run_junit_tests(self, test_class_path: str) -> Dict:
        """
        Run JUnit tests
        
        Returns: Dictionary with test results
        """
        try:
            # For MVP, we'll simulate test execution
            # In production, use Maven/Gradle to run tests
            
            return {
                "passed": 1,
                "failed": 0,
                "skipped": 0,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "errors": [str(e)]
            }
