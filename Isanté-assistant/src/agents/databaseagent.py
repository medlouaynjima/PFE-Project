from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from src.agents.agentstage import AgentState
from src.agents.utils.tools import tables_schema, execute_sql
from src.common.db_utils import AVAILABLE_TABLES
import json
from dotenv import load_dotenv
import time
from src.agents.utils.llm import llm
from src.agents.utils.token_logs import log_step
from datetime import datetime
import re
import copy
import logging
from src.agents.utils.summarization import get_messages_with_summary, should_summarize, update_state_with_summary
from langchain_core.runnables import RunnableConfig, Runnable
from typing import Any, Optional, Dict, List, Union

# Instructions adaptées pour le domaine santé/assurance

databaseagent_instructions = """
You are an expert database agent that specializes in converting natural language questions into SQL queries for a healthcare/insurance database.

TABLES AND COLUMNS (use only these columns for each table):

adherent: adherent_id, cin, nom_adherent, prenom_adherent, genre, rib, matricule_fiscale, date_de_naissance, gsm
medecin: medecin_id, cin, nom_medecin, prenom_medecin, genre, rib, matricule_fiscale_medecin, date_naissance_medecin, gsm_medecin
agent: agent_id, matricule_agent, gsm_agent, nom_agent, prenom_agent
dossier: dossier_id, ticket_moderateur, reste_a_payer, pharmacie, radio, analyses, autre, malade_id, medecin_id
malade_en_charge: malade_id, malade_nom, malade_prenom, cin, malade_qualite, adherent_id
reclamation: reclamation_id, reclamation_status, reclamation_text, dossier_id, matricule_agent
reclamationresolu: reclamationresolu_id, date_resolution, commentaire_resolution, agent_id, reclamation_id
remboursement: remboursement_id, total_rembourse, est_rembourse, date_decision, total_ordonnance, num_dossier, type, num_transaction,date_demande,delai_prevu,motif_retard

TABLE RELATIONSHIPS (use these paths for joins):
- ADHERENT is linked to MALADE_EN_CHARGE via adherent_id (OneToMany)
- MALADE_EN_CHARGE is linked to DOSSIER via malade_id (OneToMany)
- MEDECIN is linked to DOSSIER via medecin_id (OneToMany)
- DOSSIER is linked to RECLAMATION via dossier_id (OneToMany)
  * IMPORTANT: To join reclamation to dossier, use reclamation.dossier_id = dossier.dossier_id (not dossier_id directly)
- RECLAMATION is linked to RECLAMATIONRESOLU via reclamation_id (OneToOne)
- DOSSIER is linked to REMBOURSEMENT via num_dossier (OneToOne)
- In JOIN clauses, always disambiguate fields like ID by prefixing them with the table name (e.g., dossier.dossier_id, reclamation.reclamation_id)

CONTEXT-AWARE COLUMN SELECTION (POST-PROCESSING ENABLEMENT):
WHEN THE USER ASKS ABOUT:
- Delays / "pourquoi ça prend plus de 15 jours ?" / "délai" / "retard"
  → ALWAYS include: remboursement.date_decision, remboursement.date_demande, remboursement.motif_retard
- Ticket modérateur / reste à payer
  → Include: dossier.reste_a_payer, remboursement.total_ordonnance, remboursement.total_rembourse
- Amount mismatches ("ne correspond pas aux factures")
  → Include: remboursement.total_ordonnance, remboursement.total_rembourse, dossier.reste_a_payer

IMPORTANT:
- Always select these additional columns when relevant, even if the user didn't name them explicitly, to allow post-processing.
- Use the API aliases (NOT DB names): date_decision, date_demande, total_ordonnance, total_rembourse, reste_a_payer.
- For reclamation join, use: reclamation.dossier_id = dossier.dossier_id (NOT reclamation.num_dossier).

To get all claims (réclamations) for an adherent:
1. Start from ADHERENT (adherent_id)
2. Join to MALADE_EN_CHARGE on adherent_id
3. Join to DOSSIER on malade_id
4. Join to RECLAMATION on dossier_id (use reclamation.dossier_id = dossier.dossier_id)
5. (Optionally) Join to RECLAMATIONRESOLU on reclamation_id

Example query for the latest claim and its resolution for an adherent:
SELECT r.reclamation_text, r.reclamation_status, rr.date_resolution, rr.commentaire_resolution
FROM reclamation r
LEFT JOIN reclamationresolu rr ON r.reclamation_id = rr.reclamation_id
JOIN dossier d ON r.dossier_id = d.dossier_id
JOIN malade_en_charge m ON d.malade_id = m.malade_id
WHERE m.adherent_id = 10
ORDER BY r.reclamation_id DESC
LIMIT 1;

If you need to check the resolution of a complaint, use the columns from reclamationresolu (e.g., date_resolution, commentaire_resolution).

CORRESPONDANCE ENTRE LE LANGAGE NATUREL ET LA COLONNE malade_qualite :
- "ma femme", "mon épouse" → malade_qualite = 'épouse'
- "mon fils" → malade_qualite = 'fils'
- "ma fille" → malade_qualite = 'fille'
- "mon enfant" → malade_qualite IN ('fils', 'fille')
- "mes enfants" → malade_qualite IN ('fils', 'fille')
- "mes ayants droit" → pas de filtre sur malade_qualite (tous les ayants droit)
- "mon mari" → malade_qualite = 'époux'
- "conjoint", "conjointe" → malade_qualite = 'époux' ou 'épouse' selon le genre

EXEMPLES DE REQUÊTES :
- Pour le médecin traitant de l'épouse :
SELECT m.nom_medecin, m.prenom_medecin
FROM medecin m
JOIN dossier d ON m.medecin_id = d.medecin_id
JOIN malade_en_charge mc ON d.malade_id = mc.malade_id
WHERE mc.adherent_id = {{adherent_id}} AND mc.malade_qualite = 'épouse';

- Pour le médecin traitant du fils :
... WHERE mc.adherent_id = {{adherent_id}} AND mc.malade_qualite = 'fils';

- Pour tous les ayants droit :
... WHERE mc.adherent_id = {{adherent_id}};

- Pour tous les enfants :
... WHERE mc.adherent_id = {{adherent_id}} AND mc.malade_qualite IN ('fils', 'fille');

CURRENT TIME: {timestamp}


- If the user is a MEDECIN:
   - All data MUST be filtered with `WHERE dossier.medecin_id = {{medecin_id}}`
   - The médecin has access ONLY to the dossiers and remboursements linked to their own patients (i.e., dossiers where they are the prescribing doctor)
   - Within those dossiers, the médecin can see:
     - The patient’s identity (malade_nom, malade_prenom, date_de_naissance, gsm)
     - The associated adherent’s identity (nom_adherent, prenom_adherent, gsm)
     - Dossier details (ticket_moderateur, reste_a_payer)
     - Reimbursement details (total_rembourse, total_ordonnance, date_decision)
   - The médecin CANNOT access dossiers or patients not linked to their `medecin_id`

EXEMPLES DE REQUÊTES POUR MÉDECINS :

1. Voir les patients que j’ai traités :
SELECT DISTINCT 
  mc.malade_nom, 
  mc.malade_prenom, 
FROM dossier d
JOIN malade_en_charge mc ON d.malade_id = mc.malade_id
WHERE d.medecin_id = {{medecin_id}};

2. Voir les remboursements associés à mes dossiers :
SELECT 
  mc.malade_nom, 
  mc.malade_prenom, 
  r.total_rembourse
FROM dossier d
JOIN remboursement r ON r.num_dossier = d.dossier_id
JOIN malade_en_charge mc ON d.malade_id = mc.malade_id
WHERE d.medecin_id = {{medecin_id}};

3. Quels dossiers de mes patients ont été remboursés cette année ? :
SELECT 
  d.dossier_id,
  mc.malade_nom,
  mc.malade_prenom,
  r.total_rembourse,
  r.date_decision
FROM dossier d
JOIN remboursement r ON r.num_dossier = d.dossier_id
JOIN malade_en_charge mc ON d.malade_id = mc.malade_id
WHERE d.medecin_id = {{medecin_id}}
  AND YEAR(r.date_decision) = YEAR(CURDATE());


4. Obtenir les coordonnées de l’adhérent parent d’un patient :
SELECT 
  a.nom_adherent,
  a.prenom_adherent,
  a.gsm AS telephone_adherent
FROM dossier d
JOIN malade_en_charge mc ON d.malade_id = mc.malade_id
JOIN adherent a ON mc.adherent_id = a.adherent_id
WHERE d.medecin_id = {{medecin_id}} AND mc.malade_nom='Mohamed' AND mc.malade_prenom='Zouari';


Your tasks:
1. Analyze the user's question carefully to understand what data they need.
2. Determine which tables from our database contain the necessary information.
3. Examine the schema of those tables using the tables_schema tool.
4. Create a precise SQL query that will answer the user's question.
5. Test your query using the execute_sql tool.
6. Present the results in a clear, user-friendly format.

CRITICAL: FOR DELAY/WAIT TIME QUESTIONS:
- If the user asks about delays, waiting times, or "why does it take longer than X days?"
- ALWAYS include remboursement.motif_retard in your SELECT statement
- This column contains the justification/reason for delays
- Example: SELECT r.date_decision, r.date_demande, r.motif_retard, ... FROM remboursement r ...


HANDLING FOLLOW-UP QUESTIONS AND COMPLEX QUERIES:
- Pay careful attention to the conversation context and previous questions/queries
- When a user asks a short or ambiguous follow-up question (e.g., "What about 2024?" or "How about last month?"), interpret it in the context of previous questions
- If the current question seems to reference a time period, metric, or dimension mentioned in previous questions, assume it's requesting similar data for a different parameter
- Examples of follow-up patterns:
  * "What about [different time period]?" → Apply the same analysis but for the new time period
  * "How about [different dimension]?" → Use the same metrics but slice by the new dimension
  * "And for [different entity]?" → Apply the same query structure but for a different entity

CRITICAL: FOLLOW-UP CONTEXT UNDERSTANDING:
You MUST analyze the conversation context to understand what the user is asking for in follow-up questions.

ANALYZE CONVERSATION CONTEXT:
1. Look at the conversation summary and previous messages to understand what the user was asking about
2. Identify which table was used in the previous question (remboursement, reclamation, dossier, etc.)
3. Identify what type of data was requested (status, amounts, dates, etc.)
4. Apply the SAME query structure but change the family member filter (malade_qualite)

NAME FILTERING RULES (DISABLED):
- Do NOT filter by beneficiary names (mc.malade_nom or mc.malade_prenom). Names are often inconsistent and cause false negatives.
- Rely on strict isolation (mc.adherent_id = {adherent_id}) and role filters (mc.malade_qualite IN ('fille','fils','épouse', ...)).
- If ambiguity remains, order by the most relevant date (e.g., r.date_decision DESC or r.reclamation_id DESC) and use LIMIT 1 when appropriate.

CATEGORY FILTERING RULES (MANDATORY):
- NEVER filter using dossier boolean flags (dossier.pharmacie, dossier.radio, dossier.analyses, dossier.autre). These fields may be unset.
- ALWAYS filter category using remboursement.type IN ('Pharmacie','Analyses','Radio', ...). Example: r.type = 'Analyses'.

FOLLOW-UP PATTERNS TO DETECT:
- "et pour [family member] ?" → Same question but for different family member
- "et [family member] ?" → Same question but for different family member  
- "et mes enfants ?" → Same question but for children (malade_qualite IN ('fils', 'fille'))
- "et mon époux/épouse ?" → Same question but for spouse
- "et mes ayants droit ?" → Same question but for all dependents

CONTEXT ANALYSIS RULES:
1. If previous question was about REMBOURSEMENTS → Use remboursement table with same fields
2. If previous question was about RÉCLAMATIONS/COMPLAINTS → Use reclamation table with same fields  
3. If previous question was about DOSSIERS MÉDICAUX → Use dossier table with same fields
4. If previous question was about MÉDECINS → Use medecin table with same fields

EXAMPLES OF CORRECT FOLLOW-UP HANDLING:

Previous: "Quel est le statut de remboursement de ma femme ?"
Current: "et pour mes fils ?"
→ Use SAME remboursement query but WHERE malade_qualite = 'fils'

Previous: "Montrez-moi mes réclamations"  
Current: "et pour ma fille ?"
→ Use SAME reclamation query but WHERE malade_qualite = 'fille'

Previous: "Quels sont mes dossiers médicaux ?"
Current: "et pour mon époux ?" 
→ Use SAME dossier query but WHERE malade_qualite = 'époux'

Previous: "Combien ai-je été remboursé cette année ?"
Current: "et pour mes enfants ?"
→ Use SAME remboursement query but WHERE malade_qualite IN ('fils', 'fille')

MANDATORY STEPS FOR FOLLOW-UP QUESTIONS:
1. Read the conversation summary to understand the previous question
2. Identify which table and fields were used in the previous query
3. Extract the family member mentioned in the current question
4. Generate the SAME query structure but with the new malade_qualite filter
5. NEVER change the table or main query structure - only change the family member filter

SPECIAL QUERY TYPES FOR HEALTHCARE/INSURANCE:
1. Reimbursement Queries (e.g., "my reimbursements for 2024", "total reimbursed amount")
   - Focus on remboursement table with proper date filtering
   - Use SUM() for total amounts, COUNT() for number of reimbursements
   - Example: SELECT SUM(montant) as total_rembourse FROM remboursement WHERE adherent_id = X AND YEAR(date_remboursement) = 2024
2. Claims/Complaints Queries (e.g., "my complaints status", "reclamation responses")
   - Join reclamation and reclamationresolu tables when needed
   - Check for response status and resolution dates
   - Example: SELECT r.objet, rr.status_resolution FROM reclamation r LEFT JOIN reclamationresolu rr ON r.id = rr.reclamation_id WHERE r.adherent_id = X

3. Personal Information Queries (e.g., "my profile", "my personal details")
   - Return basic information from adherent or medecin table
   - Example: SELECT nom, prenom, gsm, rib FROM adherent WHERE adherent_id = X LIMIT 1

4. Dossier/File Queries (e.g., "my medical files", "dossier status")
   - Query dossier table with proper status filtering
   - Include malade_en_charge information when relevant
   - Example: SELECT dossier_id, ticket_moderateur, reste_a_payer, pharmacie FROM dossier WHERE adherent_id = X

========================
🧠 GENERAL BEHAVIOR RULES:
========================
1. ONLY use the abstract column names (e.g. adherent_id, reclamation_id, etc.) as defined in the COLUMN_MAPPING.
   - NEVER invent or use real database column names (e.g. ID, ID_ADHERENT, ID_MEDECIN).
   - If a required field doesn't exist in the mapping, report it as "not available".
2. NEVER use SELECT * — always select explicit fields like `SELECT dossier_id, ticket_moderateur`.
3. ALWAYS restrict the data to the current user:
   - If adherent: use `WHERE adherent_id = {{adherent_id}}`
   - If medecin: use `WHERE medecin_id = {{medecin_id}}`
4. NEVER use OR, UNION, subqueries that can bypass user filtering.
5. Only SELECT statements are allowed. NEVER use INSERT, UPDATE, DELETE, DROP, etc.

=====================
📊 DATABASE STRUCTURE:
=====================

Tables:
- adherent
- medecin
- agent
- malade_en_charge
- dossier
- reclamation
- reclamationresolu
- remboursement

Key Relationships:
- malade_en_charge.adherent_id → adherent.adherent_id
- dossier.malade_id → malade_en_charge.malade_id
- dossier.medecin_id → medecin.medecin_id
- reclamation.dossier_id → dossier.dossier_id
- reclamation.matricule_agent → agent.agent_id
- reclamationresolu.reclamation_id → reclamation.reclamation_id
- reclamationresolu.agent_id → agent.agent_id
- remboursement.num_dossier → dossier.dossier_id

Date fields (use with YEAR(), BETWEEN, etc.):
- date_de_naissance, date_naissance_medecin, date_resolution, date_decision


RULES FOR SQL GENERATION:
- In JOIN ... ON clauses, always use table prefixes to disambiguate columns (e.g., reclamation.reclamation_id = reclamationresolu.reclamation_id).
- In SELECT and WHERE clauses, use simple column names if there is no ambiguity.
- Never use table aliases (like r., rr., etc.).
- Never use SELECT * — always select explicit fields like SELECT dossier_id, ticket_moderateur.
- Always restrict the data to the current user: If adherent, use WHERE adherent_id = {{adherent_id}}; if medecin, use WHERE medecin_id = {{medecin_id}}.
- Only SELECT statements are allowed. NEVER use INSERT, UPDATE, DELETE, DROP, etc.

=======================
🔁 FOLLOW-UP HANDLING:
=======================
If the user asks:
- "Et pour 2024 ?" → apply the same previous logic for YEAR = 2024.
- "Et pour les médicaments ?" → filter dossier where pharmacie = true.
- "Ont-ils répondu à ma dernière réclamation ?" → use ORDER BY on reclamation_id and LEFT JOIN with reclamationresolu.

When a question is asked:
- Always check relevant table schemas before writing SQL
- Make SQL queries that are efficient, accurate, and focused
- If the query returns errors, carefully review and fix the issues
- Provide clear explanations of your query results

The database contains healthcare and insurance domain data, including tables for patients (adherents and their dependents in malade_en_charge), medical service providers (medecins), medical claim records (dossiers), reimbursement decisions (remboursements), complaints (reclamations) and complaint resolutions (reclamationresolu).

CURRENT USER CONTEXT:
- Adherent ID: {adherent_id} or Medecin ID: {medecin_id} (depending on user role)
- ALWAYS filter queries by this adherent_id or medecin_id to ensure the results are relevant to this specific user
- All data should be limited to this user only

IMPORTANT DATABASE DATE FORMAT:
- Date fields in the database (such as date_naissance, date_resolution, or date_decision) are stored in standard SQL DATE or TIMESTAMP format (e.g., '2024-07-27' for July 27, 2024).
- When filtering by year, use SQL functions like YEAR(date_field) = 2024.
- When filtering by month, use MONTH(date_field) = 7 or DATE_FORMAT(date_field, '%m') = '07' depending on the SQL dialect.
- For queries involving a range of dates, use BETWEEN with 'YYYY-MM-DD' format.
- Example: "WHERE date_resolution BETWEEN '2024-01-01' AND '2024-12-31'"
- Always ensure that every query using dates also includes strict filtering by adherent_id or medecin_id to maintain entity isolation and comply with privacy rules.

SECURITY RULES (CRITICAL - MUST FOLLOW EXACTLY):
- READ-ONLY ACCESS: Use ONLY SELECT statements. NEVER use INSERT, UPDATE, DELETE, CREATE, DROP, ALTER or any other data modification operations.
- STRICT ENTITY ISOLATION: EVERY query MUST include 'WHERE adherent_id = {adherent_id}' or 'WHERE medecin_id = {medecin_id}' in the WHERE clause to enforce data isolation.
- NO EXCEPTIONS: There are NO exceptions to this rule - ALWAYS filter by the appropriate user ID.
- PREVENT BYPASSING: NEVER use OR conditions, UNION queries, or subqueries that could bypass the user ID filter.
- REJECT MULTI-USER QUERIES: If a user requests data across multiple adherents or medecins, REJECT the request and explain the system only provides access to their own data.
- VERIFY ALL JOINS: When joining tables, ensure each joined table is also filtered by the appropriate user ID ({adherent_id} or {medecin_id}) where applicable.
- NO AGGREGATE QUERIES ACROSS USERS: Never perform operations that would aggregate data across different user IDs.
- SQL INJECTION PREVENTION: Sanitize inputs and never directly concatenate user input into SQL strings.

EXAMPLE OF A CORRECT QUERY:
SELECT r.reclamation_text, r.reclamation_status
FROM reclamation r
LEFT JOIN reclamationresolu rr ON r.reclamation_id = rr.reclamation_id
JOIN dossier d ON r.dossier_id = d.dossier_id
JOIN malade_en_charge mc ON d.malade_id = mc.malade_id
WHERE mc.adherent_id = 10
ORDER BY r.reclamation_id DESC
LIMIT 1;

Follow best practices for SQL queries: use proper joins, avoid unnecessary columns, 
limit result sets appropriately, and explain complex parts of your queries.

CONVERSATION CONTEXT:
"{summary}"
"""

class DatabaseAgent(Runnable):
    """Agent qui convertit les questions en langage naturel en requêtes SQL sécurisées et exécute la requête."""
    
    def __init__(self):
        """Initialize the database agent with LLM and prompt"""
        self.llm = llm  # Using the shared LLM instance
        
        # Create the prompt template with message history and summary
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", databaseagent_instructions),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{question}")
        ])

    async def arun(self, state: AgentState) -> AgentState:
        """Run the agent asynchronously on the given input and state"""
        # Create a deep copy of the state to avoid modifying the original
        new_state = copy.deepcopy(state)


        # Prepare messages for the prompt
        # Get messages with summary prepended as a system message, if available
        messages = get_messages_with_summary(new_state, "database")
        messages_data = {"messages": messages}
        input_data = {**messages_data, "question": new_state.get("question", "")}
        
        
        # Start transaction logging
        start_time = time.time()
        token_start = log_step("DatabaseAgent", "start", 0)
        
        # Extract the question
        question = new_state.get("question", "")
        if not question:
            # Return a proper message using the AIMessage format
            new_state["database"]["response"] = "No question provided to database agent."
            new_state["database"]["messages"].append(AIMessage(content="No question provided to database agent."))
            return new_state
        
        # Initialize variables
        response = ""
        sql_query = ""
        query_result = ""
        error = None
        query_rows = []
        table_schemas = {}
        reasoning = ""
        
        try:
            # First, get the table schemas to help with query generation
            # Use the dynamically configured available tables from app config
            available_tables = ",".join(AVAILABLE_TABLES.keys())
            schema_result = tables_schema(available_tables)
            table_schemas = json.loads(schema_result) if isinstance(schema_result, str) else schema_result
            
            # Add schema information as a function message
            schema_message = FunctionMessage(
                name="tables_schema",
                content=str(table_schemas)
            )
            new_state["database"]["messages"].append(schema_message)
            
            # Get messages with any summary if present for context
            prompt_messages = get_messages_with_summary(new_state, "database")
            
            # Include user context if available
            adherent_id = new_state.get("adherent_id", "")
            medecin_id = new_state.get("medecin_id", "")
            
            # ANALYZE CONVERSATION CONTEXT FOR FOLLOW-UP QUESTIONS
            conversation_summary = new_state.get("summary", "")
            is_follow_up = self._detect_follow_up_context(question, conversation_summary)
            
            # Add user context to the question if available
            enhanced_question = question
            if adherent_id:
                enhanced_question = f"For adherent_id {adherent_id}: {question}"
            elif medecin_id:
                enhanced_question = f"For medecin_id {medecin_id}: {question}"
            
            # If this is a follow-up question, add context analysis
            if is_follow_up:
                context_analysis = self._analyze_previous_context(conversation_summary, question)
                enhanced_question = f"FOLLOW-UP QUESTION: {question}\n\nCONTEXT ANALYSIS: {context_analysis}\n\n{enhanced_question}"
            
            # Get current timestamp for the prompt
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            full_instructions = databaseagent_instructions.format(
                adherent_id=adherent_id,
                medecin_id=medecin_id,
                summary=new_state.get("summary", ""),
                timestamp=current_timestamp
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                ("system", full_instructions),
                MessagesPlaceholder(variable_name="messages"),
                    ("human", "{question}"),
                ]
            )
            
            # Execute the chain to generate SQL
            chain_result = await self.llm.ainvoke(
                prompt.format_messages(
                    messages=prompt_messages,
                    question=enhanced_question,
                    adherent_id=adherent_id,
                    medecin_id=medecin_id,
                    summary=new_state.get("summary", "")
                )
            )
            
            # Get the content of the response
            response = chain_result.content if hasattr(chain_result, 'content') else str(chain_result)
            
            # Extract SQL query from the response
            sql_query = self._extract_sql_query(response)
            
            # If we have a SQL query, execute it
            if sql_query:
                # Enforce automatic WHERE isolation by adherent_id/medecin_id if missing
                adherent_id = new_state.get("adherent_id", "")
                medecin_id = new_state.get("medecin_id", "")
                normalized = (sql_query or "").lower()
                if adherent_id and "adherent_id" not in normalized:
                    # Append safe filter
                    if " where " in normalized:
                        sql_query += f" AND adherent_id = {adherent_id}"
                    else:
                        sql_query += f" WHERE adherent_id = {adherent_id}"
                if medecin_id and "medecin_id" not in normalized and not adherent_id:
                    if " where " in normalized:
                        sql_query += f" AND medecin_id = {medecin_id}"
                    else:
                        sql_query += f" WHERE medecin_id = {medecin_id}"
                # Get the user ID for logging purposes
                adherent_id = new_state.get("adherent_id", "")
                medecin_id = new_state.get("medecin_id", "")
                
                # Make sure the query is properly formatted with the correct user ID
                if adherent_id and 'adherent_id' in sql_query:
                    # Ensure the correct adherent_id is in the query - this is just for logging
                    # The actual validation will happen in the execute_sql function
                    adherent_check = f"adherent_id = '{adherent_id}'"
                    adherent_check_alt = f"adherent_id='{adherent_id}'"
                    if adherent_check not in sql_query and adherent_check_alt not in sql_query:
                        logging.warning(f"Query may not have correct adherent_id: {sql_query}")
                
                elif medecin_id and 'medecin_id' in sql_query:
                    # Ensure the correct medecin_id is in the query - this is just for logging
                    # The actual validation will happen in the execute_sql function
                    medecin_check = f"medecin_id = '{medecin_id}'"
                    medecin_check_alt = f"medecin_id='{medecin_id}'"
                    if medecin_check not in sql_query and medecin_check_alt not in sql_query:
                        logging.warning(f"Query may not have correct medecin_id: {sql_query}")
                
                # Execute SQL - validation will happen inside the execute_sql function
                result_json = execute_sql(sql_query)
                
                # Add the SQL query execution as a function message
                query_message = FunctionMessage(
                    name="execute_sql",
                    content=f"Query executed: {sql_query}"
                )
                new_state["database"]["messages"].append(query_message)
                
                try:
                    # Parse the JSON result
                    parsed_result = json.loads(result_json) if isinstance(result_json, str) else result_json
                    query_rows = parsed_result
                    query_result = json.dumps(parsed_result, indent=2)
                    
                    # Add the result as a function message
                    result_message = FunctionMessage(
                        name="execute_sql_result",
                        content=query_result
                    )
                    new_state["database"]["messages"].append(result_message)
                    
                except json.JSONDecodeError:
                    query_result = result_json
                    error = "Failed to parse query result as JSON"
                    
                    # Add the error as a function message
                    error_message = FunctionMessage(
                        name="execute_sql_error",
                        content=error
                    )
                    new_state["database"]["messages"].append(error_message)
                    
        except Exception as e:
            error = str(e)
            response = f"Error processing your request: {error}"
            
            # Add the error as a function message
            error_message = FunctionMessage(
                name="database_agent_error",
                content=error
            )
            new_state["database"]["messages"].append(error_message)
        
        # Create the assistant response message
        ai_message = AIMessage(content=response)
        new_state["database"]["messages"].append(ai_message)
        
        # Update database agent state with the results
        new_state["database"]["response"] = response
        new_state["database"]["sql_query"] = sql_query
        new_state["database"]["query_result"] = query_result
        new_state["database"]["query_rows"] = query_rows
        new_state["database"]["table_schemas"] = table_schemas
        
        # ALSO copy only the query_rows to the top-level state for access by other agents
        new_state["query_rows"] = query_rows
        
        if error:
            new_state["database"]["error"] = error
        
        if reasoning:
            new_state["database"]["reasoning"] = reasoning
        
        # Add the SQL query to the history if it exists
        if sql_query and not error:
            if "_query_history" not in new_state["database"]:
                new_state["database"]["_query_history"] = []
            new_state["database"]["_query_history"].append(sql_query)
        
        # Complete token logging
        log_step("DatabaseAgent", "end", token_start, time.time() - start_time)
        
        return new_state

    def _detect_follow_up_context(self, question: str, summary: str) -> bool:
        """Detect if this is a follow-up question based on patterns and context"""
        if not summary or summary.strip() == "NO SUMMARY..." or summary.strip() == "EMPTY...":
            return False
            
        # Comprehensive follow-up patterns
        follow_up_patterns = [
            # Family member follow-ups
            r"et\s+pour\s+(mon|ma|mes|le|la|les)",  # "et pour mes fils"
            r"et\s+(mon|ma|mes|le|la|les)",  # "et mes enfants"
            r"et\s+mon\s+(fils|fille|époux|épouse|enfant|enfants)",  # "et mon fils"
            r"et\s+mes\s+(enfants|fils|filles)",  # "et mes enfants"
            r"et\s+mes\s+ayants\s+droit",  # "et mes ayants droit"
            
            # Time-based follow-ups
            r"et\s+pour\s+\d{4}",  # "et pour 2024"
            r"et\s+en\s+\d{4}",  # "et en 2024"
            r"et\s+le\s+(mois|année|trimestre|semaine|jour)",  # "et le mois dernier"
            r"et\s+(l'année|le mois|la semaine|le jour)",  # "et l'année dernière"
            r"et\s+(dernier|dernière|précédent|précédente)",  # "et le dernier"
            r"et\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)",  # "et janvier"
            
            # Status/details follow-ups
            r"et\s+le\s+(statut|status)",  # "et le statut"
            r"et\s+les\s+(détails|details)",  # "et les détails"
            r"et\s+les\s+(dates|montants|montant)",  # "et les dates"
            r"et\s+combien",  # "et combien"
            r"et\s+le\s+total",  # "et le total"
            r"et\s+la\s+(somme|valeur)",  # "et la somme"
            
            # Category follow-ups
            r"et\s+pour\s+les\s+(médicaments|medicaments|pharmacie)",  # "et pour les médicaments"
            r"et\s+les\s+(analyses|radio|radiologie)",  # "et les analyses"
            r"et\s+la\s+(pharmacie|radiologie|analyses)",  # "et la pharmacie"
            r"et\s+(médicaments|analyses|radio)",  # "et médicaments"
            
            # Short follow-ups
            r"^\s*et\s*\?*\s*$",  # "et ?" or "et"
            r"et\s+alors",  # "et alors"
            r"et\s+sinon",  # "et sinon"
            r"et\s+aussi",  # "et aussi"
            r"et\s+ça",  # "et ça"
            
            # Number/date follow-ups
            r"^\s*\d{4}\s*\?*\s*$",  # "2024?" or "2024"
            r"^\s*\d{1,2}\s*\?*\s*$",  # "12?" or "12" (month)
            r"^\s*(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s*\?*\s*$",  # "janvier?"
            
            # Question word follow-ups
            r"^\s*(quoi|comment|où|quand|pourquoi|qui)\s*\?*\s*$",  # "quoi?", "comment?"
            r"^\s*(statut|montant|total|détails|dates)\s*\?*\s*$",  # "statut?", "montant?"
        ]
        
        question_lower = question.lower().strip()
        for pattern in follow_up_patterns:
            if re.search(pattern, question_lower):
                return True
                
        return False
    
    def _analyze_previous_context(self, summary: str, current_question: str) -> str:
        """Analyze the previous conversation context to understand what table/query to use"""
        if not summary or summary.strip() in ["NO SUMMARY...", "EMPTY..."]:
            return "No previous context available"
        
        # Analyze what the previous question was about
        summary_lower = summary.lower()
        question_lower = current_question.lower()
        
        # Determine the base table and context from previous conversation
        base_table = None
        base_context = ""
        
        # Check for reimbursement context
        if any(word in summary_lower for word in ["remboursement", "remboursé", "reimbursement", "paid", "money", "montant", "total"]):
            base_table = "remboursement"
            base_context = "REIMBURSEMENTS"
        # Check for claims/reclamations context
        elif any(word in summary_lower for word in ["réclamation", "reclamation", "complaint", "claim", "status", "statut"]):
            base_table = "reclamation"
            base_context = "CLAIMS/RECLAMATIONS"
        # Check for medical files/dossiers context
        elif any(word in summary_lower for word in ["dossier", "medical", "médical", "file", "ticket", "modérateur", "pharmacie", "radio", "analyses"]):
            base_table = "dossier"
            base_context = "MEDICAL FILES/DOSSIERS"
        # Check for doctor context
        elif any(word in summary_lower for word in ["médecin", "medecin", "doctor", "traitant"]):
            base_table = "medecin"
            base_context = "DOCTORS"
        
        if not base_table:
            return f"Previous context: {summary[:200]}... Current follow-up: {current_question}. Analyze the previous question type and apply the same query structure."
        
        # Analyze the current follow-up question type
        follow_up_type = self._analyze_follow_up_type(question_lower)
        
        # Generate context analysis based on follow-up type
        if follow_up_type == "family_member":
            family_member = self._extract_family_member(question_lower)
            return f"Previous question was about {base_context}. Current follow-up asks about {family_member}. Use {base_table} table with malade_qualite filter for {family_member}."
        
        elif follow_up_type == "time_period":
            time_info = self._extract_time_info(question_lower)
            return f"Previous question was about {base_context}. Current follow-up asks about {time_info}. Use {base_table} table with date/time filter for {time_info}."
        
        elif follow_up_type == "status_details":
            detail_type = self._extract_detail_type(question_lower)
            return f"Previous question was about {base_context}. Current follow-up asks about {detail_type}. Use {base_table} table with additional fields for {detail_type}."
        
        elif follow_up_type == "category":
            category = self._extract_category(question_lower)
            return f"Previous question was about {base_context}. Current follow-up asks about {category}. Use {base_table} table with category filter for {category}."
        
        elif follow_up_type == "amount":
            return f"Previous question was about {base_context}. Current follow-up asks about AMOUNTS/TOTALS. Use {base_table} table with SUM/COUNT functions for amounts."
        
        else:  # generic follow-up
            return f"Previous question was about {base_context}. Current follow-up: '{current_question}'. Use {base_table} table with same structure but adapt filters based on the follow-up question."
    
    def _analyze_follow_up_type(self, question_lower: str) -> str:
        """Determine the type of follow-up question"""
        # Family member follow-ups
        if any(word in question_lower for word in ["fils", "fille", "enfant", "enfants", "époux", "épouse", "ayants droit"]):
            return "family_member"
        
        # Time period follow-ups
        if any(word in question_lower for word in ["2024", "2023", "2025", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre", "mois", "année", "dernier", "dernière"]):
            return "time_period"
        
        # Status/details follow-ups
        if any(word in question_lower for word in ["statut", "status", "détails", "details", "dates", "montant", "montant"]):
            return "status_details"
        
        # Category follow-ups
        if any(word in question_lower for word in ["médicaments", "medicaments", "pharmacie", "analyses", "radio", "radiologie"]):
            return "category"
        
        # Amount follow-ups
        if any(word in question_lower for word in ["combien", "total", "somme", "valeur", "montant"]):
            return "amount"
        
        return "generic"
    
    def _extract_family_member(self, question_lower: str) -> str:
        """Extract family member from follow-up question"""
        if "fils" in question_lower:
            return "SONS"
        elif "fille" in question_lower:
            return "DAUGHTER"
        elif "enfants" in question_lower:
            return "CHILDREN"
        elif "époux" in question_lower:
            return "HUSBAND"
        elif "épouse" in question_lower:
            return "WIFE"
        elif "ayants droit" in question_lower:
            return "ALL DEPENDENTS"
        else:
            return "FAMILY MEMBER"
    
    def _extract_time_info(self, question_lower: str) -> str:
        """Extract time information from follow-up question"""
        if any(year in question_lower for year in ["2024", "2023", "2025"]):
            return "SPECIFIC YEAR"
        elif any(month in question_lower for month in ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]):
            return "SPECIFIC MONTH"
        elif "dernier" in question_lower or "dernière" in question_lower:
            return "LAST PERIOD"
        else:
            return "TIME PERIOD"
    
    def _extract_detail_type(self, question_lower: str) -> str:
        """Extract detail type from follow-up question"""
        if "statut" in question_lower:
            return "STATUS"
        elif "détails" in question_lower:
            return "DETAILS"
        elif "dates" in question_lower:
            return "DATES"
        else:
            return "ADDITIONAL INFORMATION"
    
    def _extract_category(self, question_lower: str) -> str:
        """Extract category from follow-up question"""
        if "médicaments" in question_lower or "pharmacie" in question_lower:
            return "MEDICATIONS/PHARMACY"
        elif "analyses" in question_lower:
            return "ANALYSES"
        elif "radio" in question_lower or "radiologie" in question_lower:
            return "RADIOLOGY"
        else:
            return "SPECIFIC CATEGORY"

    def _extract_sql_query(self, text: str) -> str:
        """Extract SQL query from text"""
        # Look for SQL queries inside ``` blocks
        sql_pattern = r"```sql\s*([\s\S]*?)\s*```"
        match = re.search(sql_pattern, text)
        
        if match:
            return match.group(1).strip()
        
        # Try without sql tag
        code_pattern = r"```\s*([\s\S]*?)\s*```"
        match = re.search(code_pattern, text)
        
        if match:
            return match.group(1).strip()
        
        return ""

    def run(self, state: AgentState) -> AgentState:
        """Synchronous version of arun"""
        import asyncio
        try:
            # Try to get the existing event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there is no event loop in this thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        try:
            return loop.run_until_complete(self.arun(state))
        except Exception as e:
            # Log the error and re-raise
            print(f"Error in DatabaseAgent.run: {str(e)}")
            raise

    def __call__(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Make the agent compatible with LangGraph by implementing __call__"""
        return self.run(state)

    def invoke(self, input: Union[Dict[str, Any], AgentState], config: Optional[RunnableConfig] = None) -> AgentState:
        """Required implementation for the Runnable interface"""
        # Start time tracking
        start_time = time.time()
        
        # If input is a dictionary, convert it to an AgentState
        if isinstance(input, dict):
            state = AgentState(**input)
        else:
            state = input

        # Debugging log
        token_start = log_step("DatabaseAgent", "invoke_start", 0)

        # Check if state needs summarization
        if should_summarize(state):
            state = update_state_with_summary(state, "database")

        # Create a modified copy of the state for processing
        new_state = copy.deepcopy(state)
        
        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format instructions with user context, timestamp, and summary
        adherent_id = new_state.get("adherent_id", "")
        medecin_id = new_state.get("medecin_id", "")
        
        full_instructions = databaseagent_instructions.format(
            adherent_id=adherent_id,
            medecin_id=medecin_id,
            timestamp=current_time,
            summary=new_state.get("summary", "")
        )
        
        # Create a new prompt with the updated instructions
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", full_instructions),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{question}")
        ])
        
        # Run the agent with the updated prompt
        result = self.run(new_state)
        
        # Complete token logging
        log_step("DatabaseAgent", "invoke_end", token_start, time.time() - start_time)
        
        return result

