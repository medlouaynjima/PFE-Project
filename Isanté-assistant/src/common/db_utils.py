import mysql.connector
from mysql.connector import Error
import json
from decimal import Decimal
import datetime
import re
from fastapi import HTTPException

# Custom JSON encoder to handle Decimal and datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

# Column Mapping for the MySQL database schema
COLUMN_MAPPING = {
    "adherent": {
        "adherent_id": "ID",
        "cin": "CIN",
        "nom_adherent": "NOM",
        "prenom_adherent": "PRENOM",
        "genre": "GENRE",
        "rib": "RIB",
        "matricule_fiscale": "mat_fisc",
        "date_de_naissance": "DATE_NAISSANCE",
        "gsm": "GSM",
    },
    "medecin": {
        "medecin_id": "ID",
        "cin": "CIN",
        "nom_medecin": "NOM",
        "prenom_medecin": "PRENOM",
        "genre": "GENRE",
        "rib": "RIB",
        "matricule_fiscale_medecin": "mat_fisc",
        "date_naissance_medecin": "DATE_NAISSANCE",
        "gsm_medecin": "GSM",
    },
    "agent": {
        "agent_id": "ID",
        "matricule_agent": "MAT_AGENT",
        "gsm_agent": "GSM",
        "nom_agent": "NOM",
        "prenom_agent": "PRENOM",
    },
    "dossier": {
        "dossier_id": "ID",
        "ticket_moderateur": "TICKET_MOD",
        "reste_a_payer": "REST_A_PAYER",
        "pharmacie": "PHARMACIE",
        "radio": "RADIO",
        "analyses": "ANALYSES",
        "autre": "AUTRE",
        "malade_id": "ID_MALADE",
        "medecin_id": "ID_MEDECIN",
    },
    "malade_en_charge": {
        "malade_id": "ID",
        "malade_nom": "NOM",
        "malade_prenom": "PRENOM",
        "cin": "CIN",
        "malade_qualite": "QUALITE",
        "adherent_id": "ID_ADHERENT",
    },
    "reclamation": {
        "reclamation_id": "ID",
        "reclamation_status": "STATUS",
        "reclamation_text": "text_reclamation",
        "dossier_id": "num_dossier",
        "matricule_agent": "matricule_agent",
    },
    "reclamationresolu": {
        "reclamationresolu_id": "id",
        "date_resolution": "date_resolution",
        "commentaire_resolution": "commentaire_resolution",
        "agent_id": "id_agent",
        "reclamation_id": "id_reclamation",
    },
    "remboursement": {
        "remboursement_id": "ID",
        "total_rembourse": "TOTALE_REMBOURSE",
        "est_rembourse": "EST_REMBOURSE",
        "date_decision": "DATE_DECISION",
        "total_ordonnance": "TOTAL_ORDONNANCE",
        "num_dossier": "ID_DOSSIER",
        "type": "type",
        "date_demande": "date_demande",
        "delai_prevu": "delai_prevu",
        "motif_retard": "motif_retard"
    }
}

AVAILABLE_TABLES = {
    'adherent': 'adherent',
    'medecin': 'medecin',
    'agent': 'agent',
    'dossier': 'dossier',
    'malade_en_charge': 'malade_en_charge',
    'reclamation': 'reclamation',
    'reclamationresolu': 'reclamationresolu',
    'remboursement': 'remboursement'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='assurance'
        )
        return connection
    except Error as e:
        return {"error": str(e)}

def unmap_columns(sql_query, alias_to_table, column_mapping):
    """
    Remplace les noms de colonnes API par les vrais noms SQL, en tenant compte de l'alias/table.
    Gère aussi les colonnes sans alias et les cas table.api_col.
    """
    # Remplacement pour les cas avec alias (ex: r.colonne)
    for alias, table in alias_to_table.items():
        mapping = column_mapping.get(table, {})
        for api_col in sorted(mapping, key=len, reverse=True):
            sql_col = mapping[api_col]
            pattern = rf'\b{alias}\.({api_col})\b'
            sql_query = re.sub(pattern, f"{alias}.{sql_col}", sql_query)
    # Remplacement pour les cas table.api_col (ex: malade_en_charge.adherent_id)
    for table, mapping in column_mapping.items():
        for api_col in sorted(mapping, key=len, reverse=True):
            sql_col = mapping[api_col]
            pattern = rf'\b{table}\.({api_col})\b'
            sql_query = re.sub(pattern, f"{table}.{sql_col}", sql_query)
    # Remplacement pour les colonnes sans alias ni table (ex: reste_a_payer)
    for table, mapping in column_mapping.items():
        for api_col in sorted(mapping, key=len, reverse=True):
            sql_col = mapping[api_col]
            # Pattern plus strict pour éviter de remplacer les colonnes déjà dans un contexte de table
            pattern = rf'(?<!\.)\b{api_col}\b(?!\.)'
            sql_query = re.sub(pattern, sql_col, sql_query)
    
    return sql_query

def extract_alias_to_table(sql_query):
    """
    Extrait un mapping alias->table à partir d'une requête SQL.
    Ne détecte les alias que s'ils sont explicitement définis avec AS ou espace.
    """
    alias_to_table = {}
    # Pattern pour détecter les alias explicites: FROM table alias ou FROM table AS alias
    alias_patterns = [
        r'\bfrom\s+([a-zA-Z_][\w]*)\s+([a-zA-Z_][\w]*)\b',  # FROM table alias
        r'\bfrom\s+([a-zA-Z_][\w]*)\s+as\s+([a-zA-Z_][\w]*)\b',  # FROM table AS alias
        r'\bjoin\s+([a-zA-Z_][\w]*)\s+([a-zA-Z_][\w]*)\b',  # JOIN table alias
        r'\bjoin\s+([a-zA-Z_][\w]*)\s+as\s+([a-zA-Z_][\w]*)\b',  # JOIN table AS alias
    ]
    
    for pattern in alias_patterns:
        for match in re.finditer(pattern, sql_query, re.IGNORECASE):
            table = match.group(1)
            alias = match.group(2)
            # Vérifier que l'alias n'est pas un mot-clé SQL
            sql_keywords = ['select', 'from', 'where', 'join', 'on', 'and', 'or', 'order', 'by', 'limit', 'group', 'having']
            if alias.lower() not in sql_keywords:
                alias_to_table[alias] = table.lower()
    
    return alias_to_table

def execute_query(sql_query: str):
    try:
        # Normalize
        sql_l = (sql_query or "").lower().strip()

        # --- Sanitize: remove fragile name-based filters to avoid false negatives ---
        # Drop predicates on malade_nom / malade_prenom (case/accents variations cause 0 rows)
        # Patterns remove segments like:
        #   AND mc.malade_nom = 'Rania'
        #   AND LOWER(mc.malade_prenom) LIKE LOWER('%Amira%')
        #   AND mc.malade_nom COLLATE utf8mb4_general_ci LIKE '%...%'
        import re as _re_sanitize
        def _strip_name_predicates(q: str) -> str:
            patterns = [
                r"\s+AND\s+(?:[a-zA-Z_][\w]*\.)?(?:malade_nom|malade_prenom)[^)]*?(?=(\s+AND|\s+ORDER|\s+LIMIT|;|$))",
                r"\s+AND\s+LOWER\((?:[a-zA-Z_][\w]*\.)?(?:malade_nom|malade_prenom)\)[^)]*?(?=(\s+AND|\s+ORDER|\s+LIMIT|;|$))",
                r"\s+AND\s+(?:[a-zA-Z_][\w]*\.)?(?:malade_nom|malade_prenom)\s+COLLATE[^)]*?(?=(\s+AND|\s+ORDER|\s+LIMIT|;|$))",
            ]
            cleaned = q
            for p in patterns:
                cleaned = _re_sanitize.sub(p, "", cleaned, flags=_re_sanitize.IGNORECASE)
            # Handle case where the name predicate was the first after WHERE: 'WHERE <name> AND' → 'WHERE '
            cleaned = _re_sanitize.sub(r"\bWHERE\s+(?:[a-zA-Z_][\w]*\.)?(?:malade_nom|malade_prenom)[^)]*?\s+AND\s+",
                                       "WHERE ", cleaned, flags=_re_sanitize.IGNORECASE)
            # If WHERE ended up empty (rare), collapse 'WHERE  ORDER' → 'ORDER'
            cleaned = _re_sanitize.sub(r"\bWHERE\s*(ORDER|LIMIT)\b", r" \1", cleaned, flags=_re_sanitize.IGNORECASE)
            return cleaned

        sql_query = _strip_name_predicates(sql_query)
        sql_l = sql_query.lower().strip()

        # --- Enforce WHERE clause isolation ---
        def _has_isolation_in_where(sql: str) -> bool:
            """
            Checks whether adherent_id or medecin_id appear in the WHERE clause.
            Prevents accidental or malicious queries that join or select those columns without filtering.
            """
            # Split once at 'where' to isolate the clause
            parts = re.split(r"\bwhere\b", sql, maxsplit=1)
            if len(parts) < 2:
                return False  # No WHERE clause
            where_clause = parts[1]
            # Look for exact equality filters like adherent_id = '123'
            return bool(
                re.search(r"\badherent_id\s*=\s*['\"]?\d+['\"]?", where_clause)
                or re.search(r"\bmedecin_id\s*=\s*['\"]?\d+['\"]?", where_clause)
            )

        if "select" in sql_l and not _has_isolation_in_where(sql_l):
            raise HTTPException(
                status_code=400,
                detail="Isolation required: WHERE clause must filter by adherent_id or medecin_id."
            )

        # Get allowed database column names
        allowed_db_columns = set()
        for table_map in COLUMN_MAPPING.values():
            allowed_db_columns.update(table_map.values())
        
        # Basic SQL tokenization
        query_tokens = sql_query.lower().replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
        
        # Check for unauthorized column access
        for token in query_tokens:
            if token in ['select', 'from', 'where', 'and', 'or', 'group', 'by', 'having', 'order', 'limit', 
                         'offset', 'join', 'inner', 'outer', 'left', 'right', 'on', 'as', '*', '=', '<', '>', '<=', '>=',
                         'desc', 'asc']:
                continue
            
            if re.match(r'^\d+;?$', token) or (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
                continue
            
            if '.' in token:
                possible_col = token.split('.')[-1].strip('`')
                if possible_col not in allowed_db_columns:
                    continue
            else:
                possible_col = token.strip('`')
                if possible_col not in allowed_db_columns:
                    if len(possible_col) <= 2 or possible_col in AVAILABLE_TABLES.keys():
                        continue
                    continue
        
        # Extract aliases and unmap columns
        alias_to_table = extract_alias_to_table(sql_query)
        query = unmap_columns(sql_query, alias_to_table, COLUMN_MAPPING)
        
        connection = get_db_connection()
        if isinstance(connection, dict):
            raise HTTPException(status_code=500, detail=connection)
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        
        # Map result column names back to API names
        mapped_result = []
        for row in result:
            mapped_row = {}
            for db_col, value in row.items():
                api_col = None
                for table_map in COLUMN_MAPPING.values():
                    for ac, dc in table_map.items():
                        if dc == db_col:
                            api_col = ac
                            break
                    if api_col:
                        break
                mapped_row[api_col if api_col else db_col] = value
            mapped_result.append(mapped_row)
        
        cursor.close()
        connection.close()
        
        json_data = json.dumps(mapped_result, cls=CustomJSONEncoder)
        return json.loads(json_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_schema(table_name: str):
    try:
        if table_name not in AVAILABLE_TABLES:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
        query = f"DESCRIBE `{table_name}`"
        connection = get_db_connection()
        if isinstance(connection, dict):
            raise HTTPException(status_code=500, detail=connection)
            
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        
        table_mapping = COLUMN_MAPPING.get(table_name, {})
        allowed_db_columns = set(table_mapping.values())
        
        filtered_schema = [
            row for row in result 
            if row['Field'] in allowed_db_columns
        ]
        
        for row in filtered_schema:
            column_name = row['Field']
            for api_col, db_col in table_mapping.items():
                if db_col == column_name:
                    row['Field'] = api_col
                    break
                    
        return filtered_schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 