from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
from fastapi.middleware.cors import CORSMiddleware
from src.core.workflow import graph, create_initial_state
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langgraph.store.memory import InMemoryStore
import os
from src.common.db_utils import (
    execute_query as db_execute_query,
    get_schema as db_get_schema,
    CustomJSONEncoder
)
from src.agents.utils.sql_validator import validate_sql_query, extract_tables_from_query
from src.common.db_utils import COLUMN_MAPPING

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class SchemaRequest(BaseModel):
    table_name: str

class QueryRequest(BaseModel):
    sql_query: str



class ChatRequest(BaseModel):
    question: str
    adherent_id: str = ""
    adherent_name: str = ""
    medecin_id: str = ""
    medecin_name: str = ""
    role: Optional[str] = ""


# Endpoints
@app.post("/get_schema")
async def get_schema(request: SchemaRequest):
    return db_get_schema(request.table_name)

@app.post("/execute_query")
async def execute_query(request: QueryRequest):
    # Re-validate at the gateway
    sql = request.sql_query
    sql_l = (sql or "").lower()
    # Build strict whitelist of columns from tables referenced in SQL
    tables = extract_tables_from_query(sql)
    allowed_columns = []
    for t in tables:
        mapping = COLUMN_MAPPING.get(t, {})
        allowed_columns.extend(list(mapping.keys()))
    is_valid, reason = validate_sql_query(sql, allowed_columns=allowed_columns or None)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"security_error": reason})
    # Extra guardrails: block UNION/CTE unless isolation present
    if (" union " in sql_l or sql_l.strip().startswith("with ") or " distinct " in sql_l) and ("adherent_id" not in sql_l and "medecin_id" not in sql_l):
        raise HTTPException(status_code=400, detail={"security_error": "Query shape requires adherent/medecin isolation."})
    
    # Execute
    result = db_execute_query(sql)
    # Basic PII/GDPR denylist strip (IDs)
    denylist = {"adherent_id", "medecin_id", "agent_id", "reclamation_id", "reclamationresolu_id", "remboursement_id", "dossier_id", "num_dossier", "num_transaction"}
    if isinstance(result, list):
        for row in result:
            if isinstance(row, dict):
                for k in list(row.keys()):
                    if k in denylist:
                        row.pop(k, None)
    # Observability: lightweight access log
    try:
        row_count = len(result) if isinstance(result, list) else 1
        print(f"[ACCESS] method=POST endpoint=/execute_query tables={tables} rows={row_count}")
    except Exception:
        pass
    return {"data": result}

@app.post("/execute_query_stream")
async def execute_query_stream(request: QueryRequest):
    sql = request.sql_query
    sql_l = (sql or "").lower()
    tables = extract_tables_from_query(sql)
    allowed_columns = []
    for t in tables:
        mapping = COLUMN_MAPPING.get(t, {})
        allowed_columns.extend(list(mapping.keys()))
    is_valid, reason = validate_sql_query(sql, allowed_columns=allowed_columns or None)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"security_error": reason})
    if (" union " in sql_l or sql_l.strip().startswith("with ") or " distinct " in sql_l) and ("adherent_id" not in sql_l and "medecin_id" not in sql_l):
        raise HTTPException(status_code=400, detail={"security_error": "Query shape requires adherent/medecin isolation."})

    # Execute using the existing path, then stream rows as NDJSON
    result = db_execute_query(sql)

    def row_iter():
        denylist = {"adherent_id", "medecin_id", "agent_id", "reclamation_id", "reclamationresolu_id", "remboursement_id", "dossier_id", "num_dossier", "num_transaction"}
        if isinstance(result, list):
            for row in result:
                if isinstance(row, dict):
                    row_filtered = {k: v for k, v in row.items() if k not in denylist}
                    yield json.dumps(row_filtered, cls=CustomJSONEncoder) + "\n"
                else:
                    yield json.dumps(row, cls=CustomJSONEncoder) + "\n"
        else:
            yield json.dumps(result, cls=CustomJSONEncoder) + "\n"

    try:
        row_count = len(result) if isinstance(result, list) else 1
        print(f"[ACCESS] method=POST endpoint=/execute_query_stream tables={tables} rows={row_count}")
    except Exception:
        pass

    return StreamingResponse(row_iter(), media_type="application/x-ndjson")

def get_user_memory(user_id: str):
    """Get user memory for conversation history using Redis or fallback to in-memory."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        return RedisChatMessageHistory(
            url=redis_url,
            session_id=user_id
        )
    except Exception as e:
        print(f"[WARN] Redis unavailable for chat history ({e}), using in-memory storage")
        from langchain.memory import ConversationBufferMemory
        return ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Global store instance for persistence during app lifetime
_profile_store = None

def get_profile_store():
    """Get the profile store for long-term memory.
    Prefer Redis when REDIS_URL is configured; otherwise fallback to in-memory.
    """
    global _profile_store
    if _profile_store is not None:
        return _profile_store
    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url:
        try:
            import redis  # type: ignore
            from langgraph.store.redis import RedisStore  # type: ignore
            client = redis.Redis.from_url(redis_url)
            client.ping()
            _profile_store = RedisStore(client)
            print(f"[INFO] Using RedisStore for profile persistence at {redis_url}")
            return _profile_store
        except Exception as e:
            print(f"[WARN] Redis unavailable ({e}); falling back to InMemoryStore")
    _profile_store = InMemoryStore()
    print("[INFO] Using InMemoryStore for profile persistence")
    return _profile_store

@app.post("/chatbot")
async def run_chat(request: ChatRequest):
    user_id = request.adherent_id or request.medecin_id or "default_user"
    memory = get_user_memory(user_id)
    profile_store = get_profile_store()

    # Utiliser le rôle envoyé si présent
    role = (request.role or "").upper().strip()
    # Déterminer le rôle de l'utilisateur
    if request.medecin_id:
        role = "MEDECIN"
    elif request.adherent_id:
        role = "ADHERENT"
    else:
        role = "ANONYME"

    state = create_initial_state(
        question=request.question,
        adherent_id=request.adherent_id,
        adherent_name=request.adherent_name,
        medecin_id=request.medecin_id,
        medecin_name=request.medecin_name,
        role=role  
    )

    result = await graph.ainvoke(state, config={"configurable": {"store": profile_store, "thread_id": user_id}})
    return {"response": str(result.get("response", ""))}