import requests
from langchain.tools import tool
import json
from typing import Dict, List, Any
from src.common.db_utils import execute_query as db_execute_query, get_schema as db_get_schema
from src.common.db_utils import COLUMN_MAPPING, AVAILABLE_TABLES, CustomJSONEncoder
import os
import subprocess
from pydantic import BaseModel, Field
from typing import Optional
import re
import datetime
from decimal import Decimal

# Define simple schema classes for the tools
class ExecuteSQLArgs(BaseModel):
    query: str = Field(..., description="The SQL query to execute")

class ExecuteCodeArgs(BaseModel):
    code: str = Field(..., description="The Python code to execute for visualization")

# Define argument schemas for the new security tools
@tool("tables_schema")
def tables_schema(tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema for those tables.
    Example Input: table1, table2, table3
    """
    # Split and validate tables
    table_list = [table.strip() for table in tables.split(',')]
    valid_tables = [table for table in table_list if table in AVAILABLE_TABLES]
    
    if not valid_tables:
        return "No valid tables provided."
    
    # Get schema for each valid table
    schema_responses = {}
    for table in valid_tables:
        try:
            schema = db_get_schema(table)
            schema_responses[table] = schema
        except Exception as e:
            schema_responses[table] = f"Error retrieving schema: {str(e)}"
    
    return json.dumps(schema_responses, indent=2)

# Import the SQL validator
from src.agents.utils.sql_validator import validate_sql_query, extract_tables_from_query

@tool("execute_sql")
def execute_sql(query: str) -> str:
    """Execute a SQL query and return the results."""
    try:
        # Validate the query first
        adherent_id_match = re.search(r"adherent_id\s*=\s*['\"]?(\d+)['\"]?", query)
        medecin_id_match = re.search(r"medecin_id\s*=\s*['\"]?(\d+)['\"]?", query)
        
        adherent_id = adherent_id_match.group(1) if adherent_id_match else None
        medecin_id = medecin_id_match.group(1) if medecin_id_match else None
        
        is_valid, reason = validate_sql_query(query, adherent_id, medecin_id)
        if not is_valid:
            return json.dumps({"error": f"Security Error: {reason}"}, indent=2)
            
        # Execute the query using db_utils
        result = db_execute_query(query)
        return json.dumps(result, indent=2, cls=CustomJSONEncoder)
        
    except Exception as e:
        print(f"Error in execute_sql: {str(e)}")
        return json.dumps({"error": f"Query execution failed: {str(e)}"}, indent=2)

execute_sql.args_schema = ExecuteSQLArgs

@tool("execute_code")
def execute_code(code: str) -> dict:
    """
    Executes Python code dynamically for visualization. This function handles any code
    the agent might generate for visualization, saving the plots in the working directory.

    Args:
    code (str): The Python code to be executed for visualization.

    Returns:
    dict: A dictionary containing the execution result, output, and file path(s) for saved visualizations.
    """
    try:
        # Directory where the notebook is saved
        working_dir = os.getcwd()
        
        # Get list of existing files before execution
        existing_files = set(os.listdir(working_dir))
        
        # Write the code to a temporary file
        temp_file_path = os.path.join(working_dir, "temp_visualization.py")
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Execute the script
        result = subprocess.run(
            ["python", temp_file_path],
            capture_output=True,
            text=True,
            cwd=working_dir
        )

        if result.returncode == 0:
            # Get list of files after execution
            new_files = set(os.listdir(working_dir))
            
            # Find only the newly generated files
            generated_files = [f for f in (new_files - existing_files) 
                            if f.endswith(('.html', '.png', '.jpg', '.svg'))]
            
            # Get the name of the first generated visualization (if any)
            graph_name = generated_files[0] if generated_files else "No visualization generated"
            
            return {
                "result": "Code executed successfully",
                "output": result.stdout.strip(),
                "graph_name": graph_name,
                "file_paths": generated_files
            }
        else:
            return {
                "result": "Execution failed",
                "error": result.stderr.strip(),
                "file_paths": []
            }

    except Exception as e:
        return {
            "result": "Error occurred",
            "error": str(e),
            "file_paths": []
        }

# Add argument schema to the tool
execute_code.args_schema = ExecuteCodeArgs