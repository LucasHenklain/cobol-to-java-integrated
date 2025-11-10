"""
Translator Agent - Converts COBOL code to Java
"""

import logging
from typing import Any, Dict, Iterable, Optional
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class TranslatorAgent:
    """
    Agent responsible for translating COBOL code to Java
    
    For MVP, uses template-based translation.
    In production, integrate with LLM for complex translations.
    """
    
    def __init__(self):
        self.name = "TranslatorAgent"
    
    async def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute COBOL to Java translation
        
        Args:
            task_input: Dictionary containing:
                - job_id: Job identifier
                - programs: List of program information
                - ast_data: Parsed AST data
                - target_stack: Target Java stack (springboot, jakarta, etc.)
                - repo_path: Optional path to the cloned repository
        
        Returns:
            Dictionary with translation results
        """
        try:
            job_id = task_input["job_id"]
            programs = task_input["programs"]
            ast_data = task_input.get("ast_data", {}) or {}
            target_stack = task_input.get("target_stack", "springboot")
            repo_path = task_input.get("repo_path")
            
            logger.info(f"[{job_id}] Starting COBOL to Java translation "
                       f"for {len(programs)} programs (stack: {target_stack})")
            
            java_files: Dict[str, Dict[str, Any]] = {}
            translated_count = 0
            skipped_programs = []
            
            # Create output directory under artifacts
            output_dir = Path(settings.ARTIFACTS_DIR) / job_id / "java"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for program in programs:
                program_name = self._resolve_program_name(program)
                program_id = program.get("program_id")
                
                if not program_name:
                    logger.warning(f"[{job_id}] Program without identifiable name, skipping entry: {program}")
                    skipped_programs.append(program)
                    continue
                
                ast = self._resolve_ast(program, ast_data)
                if not ast:
                    logger.warning(
                        f"[{job_id}] No AST data for {program_name}; generating placeholder structure"
                    )
                    ast = self._build_placeholder_ast(program_name)
                
                logger.info(f"[{job_id}] Translating {program_name} to Java")
                
                # Generate Java class
                java_code = self._generate_java_class(program_name, ast, target_stack)
                
                # Write to file
                java_file_path = output_dir / f"{program_name}.java"
                java_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(java_file_path, 'w', encoding='utf-8') as f:
                    f.write(java_code)
                
                java_files[program_name] = {
                    "program_id": program_id,
                    "path": str(java_file_path),
                    "class_name": program_name,
                    "package": "com.ford.migration.cobol",
                    "source_relative_path": program.get("relative_path"),
                    "source_path": program.get("path"),
                    "repo_path": repo_path
                }
                
                translated_count += 1
                
                logger.info(f"[{job_id}] Translated {program_name} successfully")
            
            if skipped_programs:
                logger.info(
                    f"[{job_id}] Translation completed with {len(skipped_programs)} programs lacking identifiers"
                )
            
            return {
                "success": True,
                "job_id": job_id,
                "java_files": java_files,
                "output_dir": str(output_dir),
                "translated_count": translated_count,
                "skipped": len(skipped_programs)
            }
            
        except Exception as e:
            logger.error(f"TranslatorAgent failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _resolve_program_name(self, program: Dict[str, Any]) -> Optional[str]:
        name = program.get("name")
        if name:
            return name

        relative_path = program.get("relative_path")
        if relative_path:
            return Path(relative_path).stem

        absolute_path = program.get("path")
        if absolute_path:
            return Path(absolute_path).stem

        return None

    def _resolve_ast(self, program: Dict[str, Any], ast_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for key in self._generate_lookup_keys(program):
            ast = ast_data.get(key)
            if ast:
                return ast
        return None

    def _generate_lookup_keys(self, program: Dict[str, Any]) -> Iterable[str]:
        keys = set()

        def add_key(value: Optional[str]):
            if value:
                keys.add(value)

        add_key(program.get("name"))

        name = program.get("name")
        if name:
            add_key(name.upper())
            add_key(name.lower())

        add_key(program.get("program_id"))
        add_key(program.get("relative_path"))

        relative_path = program.get("relative_path")
        if relative_path:
            path_obj = Path(relative_path)
            add_key(path_obj.name)
            add_key(path_obj.stem)

        absolute_path = program.get("path")
        if absolute_path:
            path_obj = Path(absolute_path)
            add_key(str(path_obj))
            add_key(path_obj.name)
            add_key(path_obj.stem)

        return keys

    def _build_placeholder_ast(self, program_name: str) -> Dict[str, Any]:
        return {
            "program_id": program_name,
            "divisions": [],
            "data_items": [],
            "procedures": [],
            "file_controls": []
        }
    
    def _generate_java_class(self, program_name: str, ast: Dict, target_stack: str) -> str:
        """
        Generate Java class from COBOL AST
        
        This is a simplified template-based generator for MVP.
        In production, use more sophisticated code generation.
        """
        
        # Extract data items
        data_items = ast.get("data_items", [])
        procedures = ast.get("procedures", [])
        
        # Generate class header
        java_code = f"""package com.ford.migration.cobol;

import java.math.BigDecimal;
import java.util.logging.Logger;

/**
 * Migrated from COBOL program: {program_name}
 * Auto-generated by COBOL to Java Migration System
 */
public class {program_name} {{
    
    private static final Logger logger = Logger.getLogger({program_name}.class.getName());
    
"""
        
        # Generate fields from data items
        java_code += "    // Data items from WORKING-STORAGE SECTION\n"
        for item in data_items:
            field_name = self._convert_cobol_name_to_java(item["name"])
            field_type = item["type"]
            field_value = item.get("value")
            
            if field_value:
                # Clean up value
                field_value = field_value.strip().strip("'\"")
                
                if field_type == "String":
                    java_code += f'    private {field_type} {field_name} = "{field_value}";\n'
                elif field_type in ["int", "short", "long"]:
                    # Extract numeric value
                    numeric_value = ''.join(filter(str.isdigit, field_value)) or "0"
                    java_code += f'    private {field_type} {field_name} = {numeric_value};\n'
                elif field_type == "BigDecimal":
                    numeric_value = ''.join(filter(lambda c: c.isdigit() or c == '.', field_value)) or "0"
                    java_code += f'    private {field_type} {field_name} = new BigDecimal("{numeric_value}");\n'
                else:
                    java_code += f'    private {field_type} {field_name};\n'
            else:
                if field_type == "String":
                    java_code += f'    private {field_type} {field_name} = "";\n'
                elif field_type in ["int", "short", "long"]:
                    java_code += f'    private {field_type} {field_name} = 0;\n'
                elif field_type == "BigDecimal":
                    java_code += f'    private {field_type} {field_name} = BigDecimal.ZERO;\n'
                else:
                    java_code += f'    private {field_type} {field_name};\n'
        
        java_code += "\n"
        
        # Generate main method
        java_code += """    /**
     * Main entry point
     */
    public static void main(String[] args) {
        """ + program_name + """ program = new """ + program_name + """();
        program.execute();
    }
    
    /**
     * Execute main logic
     */
    public void execute() {
        logger.info("Starting """ + program_name + """ execution");
        mainLogic();
        logger.info("Completed """ + program_name + """ execution");
    }
    
"""
        
        # Generate main logic method
        java_code += """    /**
     * Main logic (translated from PROCEDURE DIVISION)
     */
    private void mainLogic() {
        // TODO: Implement main logic
        // Original COBOL procedures: """ + ", ".join([p["name"] for p in procedures]) + """
        
        logger.info("Main logic executed");
    }
    
"""
        
        # Generate methods for procedures
        for procedure in procedures:
            method_name = self._convert_cobol_name_to_java(procedure["name"])
            java_code += f"""    /**
     * Procedure: {procedure["name"]}
     */
    private void {method_name}() {{
        // TODO: Implement {procedure["name"]} logic
        logger.info("Executing {method_name}");
    }}
    
"""
        
        # Generate getters and setters
        java_code += "    // Getters and Setters\n"
        for item in data_items:
            field_name = self._convert_cobol_name_to_java(item["name"])
            field_type = item["type"]
            field_name_capitalized = field_name[0].upper() + field_name[1:]
            
            java_code += f"""    public {field_type} get{field_name_capitalized}() {{
        return {field_name};
    }}
    
    public void set{field_name_capitalized}({field_type} {field_name}) {{
        this.{field_name} = {field_name};
    }}
    
"""
        
        # Close class
        java_code += "}\n"
        
        return java_code
    
    def _convert_cobol_name_to_java(self, cobol_name: str) -> str:
        """
        Convert COBOL naming convention to Java camelCase
        
        Example: WS-CUSTOMER-NAME -> wsCustomerName
        """
        # Remove WS- prefix if present
        if cobol_name.startswith("WS-"):
            cobol_name = cobol_name[3:]
        
        # Split by hyphens
        parts = cobol_name.lower().split('-')
        
        # First part lowercase, rest capitalized
        if len(parts) > 0:
            result = parts[0]
            for part in parts[1:]:
                result += part.capitalize()
            return result
        
        return cobol_name.lower()
