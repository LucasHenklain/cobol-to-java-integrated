"""
COBOL Parser Agent - Analyzes COBOL code and generates AST
"""

import logging
import re
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class COBOLParserAgent:
    """
    Agent responsible for parsing COBOL programs
    and generating Abstract Syntax Tree (AST)
    
    For MVP, uses regex-based parsing.
    In production, use ANTLR grammar or ProLeap/Strumenta parser.
    """
    
    def __init__(self):
        self.name = "COBOLParserAgent"
    
    async def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute COBOL parsing
        
        Args:
            task_input: Dictionary containing:
                - job_id: Job identifier
                - programs: List of program information
                - repo_path: Path to repository
        
        Returns:
            Dictionary with parsing results
        """
        try:
            job_id = task_input["job_id"]
            programs = task_input["programs"]
            repo_path = task_input.get("repo_path")
            
            logger.info(f"[{job_id}] Starting COBOL parsing for {len(programs)} programs")
            
            ast_data = {}
            
            for program in programs:
                program_path = program["path"]
                program_name = program["name"]
                
                logger.info(f"[{job_id}] Parsing program: {program_name}")
                
                # Parse COBOL file
                ast = self._parse_cobol_file(program_path)
                ast_data[program_name] = ast
                
                logger.info(f"[{job_id}] Parsed {program_name}: "
                          f"{len(ast.get('data_items', []))} data items, "
                          f"{len(ast.get('procedures', []))} procedures")
            
            return {
                "success": True,
                "job_id": job_id,
                "ast_data": ast_data,
                "programs_parsed": len(programs)
            }
            
        except Exception as e:
            logger.error(f"COBOLParserAgent failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_cobol_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a COBOL file and extract structure
        
        This is a simplified parser for MVP.
        In production, use proper COBOL grammar parser.
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        ast = {
            "program_id": self._extract_program_id(content),
            "divisions": self._extract_divisions(content),
            "data_items": self._extract_data_items(content),
            "procedures": self._extract_procedures(content),
            "file_controls": self._extract_file_controls(content)
        }
        
        return ast
    
    def _extract_program_id(self, content: str) -> str:
        """Extract PROGRAM-ID"""
        match = re.search(r'PROGRAM-ID\.\s+(\S+)', content, re.IGNORECASE)
        return match.group(1) if match else "UNKNOWN"
    
    def _extract_divisions(self, content: str) -> List[str]:
        """Extract division names"""
        divisions = []
        pattern = r'(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            divisions.append(match.group(1).upper())
        
        return divisions
    
    def _extract_data_items(self, content: str) -> List[Dict]:
        """
        Extract data items from WORKING-STORAGE SECTION
        
        Simplified extraction for MVP
        """
        data_items = []
        
        # Find WORKING-STORAGE SECTION
        ws_match = re.search(
            r'WORKING-STORAGE\s+SECTION\.(.*?)(?:PROCEDURE\s+DIVISION|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if ws_match:
            ws_content = ws_match.group(1)
            
            # Extract data items (simplified)
            pattern = r'^\s*(\d{2})\s+(\S+)\s+PIC\s+([^\s.]+)(?:\s+VALUE\s+([^.]+))?'
            
            for match in re.finditer(pattern, ws_content, re.MULTILINE):
                level = match.group(1)
                name = match.group(2)
                pic = match.group(3)
                value = match.group(4).strip() if match.group(4) else None
                
                data_items.append({
                    "level": level,
                    "name": name,
                    "picture": pic,
                    "value": value,
                    "type": self._infer_type_from_pic(pic)
                })
        
        return data_items
    
    def _infer_type_from_pic(self, pic: str) -> str:
        """Infer Java type from COBOL PIC clause"""
        pic = pic.upper()
        
        if 'X' in pic:
            return "String"
        elif '9' in pic:
            if 'V' in pic or '.' in pic:
                return "BigDecimal"
            else:
                # Count digits
                digits = pic.count('9')
                if digits <= 4:
                    return "short"
                elif digits <= 9:
                    return "int"
                else:
                    return "long"
        elif 'S' in pic:
            return "int"  # Signed numeric
        else:
            return "String"
    
    def _extract_procedures(self, content: str) -> List[Dict]:
        """Extract procedure/paragraph names"""
        procedures = []
        
        # Find PROCEDURE DIVISION
        proc_match = re.search(
            r'PROCEDURE\s+DIVISION\.(.*?)$',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if proc_match:
            proc_content = proc_match.group(1)
            
            # Extract paragraph names (simplified)
            pattern = r'^\s*([A-Z][A-Z0-9-]+)\.'
            
            for match in re.finditer(pattern, proc_content, re.MULTILINE):
                para_name = match.group(1)
                
                # Skip COBOL keywords
                if para_name not in ['STOP', 'DISPLAY', 'MOVE', 'ADD', 'COMPUTE', 
                                     'PERFORM', 'IF', 'ELSE', 'END-IF']:
                    procedures.append({
                        "name": para_name,
                        "type": "paragraph"
                    })
        
        return procedures
    
    def _extract_file_controls(self, content: str) -> List[Dict]:
        """Extract FILE-CONTROL entries"""
        file_controls = []
        
        # Find FILE-CONTROL section
        fc_match = re.search(
            r'FILE-CONTROL\.(.*?)(?:DATA\s+DIVISION|$)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if fc_match:
            fc_content = fc_match.group(1)
            
            # Extract SELECT statements
            pattern = r'SELECT\s+(\S+)\s+ASSIGN\s+TO\s+(\S+)'
            
            for match in re.finditer(pattern, fc_content, re.IGNORECASE):
                file_name = match.group(1)
                assign_to = match.group(2)
                
                file_controls.append({
                    "file_name": file_name,
                    "assign_to": assign_to
                })
        
        return file_controls
