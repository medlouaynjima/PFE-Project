"""
SQL Validation Module

This module provides functions to validate SQL queries against security rules
and ensure they adhere to the security constraints and database access policies.
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import logging



def validate_sql_query(query: str, adherent_id: Optional[str] = None, 
                     medecin_id: Optional[str] = None,
                     allowed_columns: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate a SQL query against security rules
    
    Args:
        query: The SQL query to validate
        adherent_id: The adherent_id that should be enforced
        medecin_id: The medecin_id that should be enforced
        
    Returns:
        Tuple with (is_valid, reason) indicating if the query is valid and why
    """
    # Normalize query for easier analysis
    normalized_query = query.strip().lower()
    
    # Check 1: Must be a SELECT statement only
    if not normalized_query.startswith('select '):
        return False, "Only SELECT statements are allowed for data retrieval"
    
    # Check 2: No destructive operations or multiple statements
    forbidden_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate', ';']
    for keyword in forbidden_keywords:
        if keyword in normalized_query.split():
            return False, f"Forbidden keyword '{keyword}' found in query"
    
    
    # Check 4: Must include adherent_id filter if adherent_id is provided and adherent table is used
    if adherent_id and 'adherent' in normalized_query:
        adherent_check = f"adherent_id = '{adherent_id}'"
        adherent_check_alt = f"adherent_id='{adherent_id}'"
        adherent_check_alt2 = f"adherent_id={adherent_id}"
        
        # See if any valid adherent_id pattern is in the query
        adherent_id_found = (
            adherent_check in normalized_query or 
            adherent_check_alt in normalized_query or 
            adherent_check_alt2 in normalized_query
        )
        
        # Also check for a parameterized version where quotes might be placed differently
        if not adherent_id_found:
            pattern = r"adherent_id\s*=\s*['\"]?" + re.escape(adherent_id) + r"['\"]?"
            if not re.search(pattern, normalized_query):
                return False, f"Query must filter by adherent_id = '{adherent_id}'"
    
    # Check 5: Must include medecin_id filter if medecin_id is provided and medecin table is used
    if medecin_id and 'medecin' in normalized_query:
        medecin_check = f"medecin_id = '{medecin_id}'"
        medecin_check_alt = f"medecin_id='{medecin_id}'"
        medecin_check_alt2 = f"medecin_id={medecin_id}"
        
        # See if any valid medecin_id pattern is in the query
        medecin_id_found = (
            medecin_check in normalized_query or 
            medecin_check_alt in normalized_query or 
            medecin_check_alt2 in normalized_query
        )
        
        # Also check for a parameterized version where quotes might be placed differently
        if not medecin_id_found:
            pattern = r"medecin_id\s*=\s*['\"]?" + re.escape(medecin_id) + r"['\"]?"
            if not re.search(pattern, normalized_query):
                return False, f"Query must filter by medecin_id = '{medecin_id}'"
    
    # Check 6: No UNION operations to prevent bypassing filters
    if ' union ' in normalized_query:
        return False, "UNION operations are not allowed"
    
    # Check 7: No OR conditions with adherent_id or medecin_id to prevent filter bypassing
    if (adherent_id or medecin_id) and ' or ' in normalized_query:
        parts = normalized_query.split('where')
        if len(parts) > 1 and ' or ' in parts[1]:
            where_clause = parts[1]
            if (adherent_id and "adherent_id" in where_clause) or (medecin_id and "medecin_id" in where_clause):
                return False, "OR conditions with adherent_id or medecin_id are not allowed to prevent filter bypassing"
            


        if allowed_columns:
            # Extract columns from SELECT clause (simplified approach)
            select_part = normalized_query.split('from')[0].replace('select', '').strip()
        
            # Handle SELECT * case
            if select_part == '*':
                return False, "Wildcard selections are not allowed. Please specify column names explicitly."
        
            # Extract columns (this is a simplified approach)
            columns = [col.strip() for col in select_part.split(',')]
        
            # Handle functions and aliases (simplified)
            extracted_columns = []
            for col in columns:
                # Handle simple aggregate functions like SUM(amount) AS total
                if ' as ' in col:
                    col = col.split(' as ')[0].strip()
            
                # Extract column name from functions like SUM(amount)
                if '(' in col and ')' in col:
                    col_name = col.split('(')[1].split(')')[0].strip()
                    if col_name != '*':  # Ensure no SUM(*) type expressions
                        extracted_columns.append(col_name)
                else:
                    extracted_columns.append(col)
        
            # Check if any column is not in allowed list
            for col in extracted_columns:
                if col.lower() not in [c.lower() for c in allowed_columns] and col != '*':
                    return False, f"Column '{col}' is not allowed. Allowed columns: {', '.join(allowed_columns)}"
    
    return True, "Query is valid"

def extract_tables_from_query(query: str) -> List[str]:
    """
    Extract table names from a SQL query
    
    Args:
        query: The SQL query
        
    Returns:
        List of table names found in the query
    """
    # Normalize query
    normalized_query = query.strip().lower()
    
    # Extract FROM and JOIN tables
    tables = []
    
    # Extract the main table from FROM clause
    from_match = re.search(r'from\s+(\w+)', normalized_query)
    if from_match:
        tables.append(from_match.group(1))
    
    # Extract tables from JOIN clauses
    join_matches = re.finditer(r'join\s+(\w+)', normalized_query)
    for match in join_matches:
        tables.append(match.group(1))
    
    return tables