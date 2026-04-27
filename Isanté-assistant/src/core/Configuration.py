from typing import ClassVar, Optional, Any
from pydantic import BaseModel, Field

class Configuration(BaseModel):
    """Configuration for the claims management workflow."""
    user_id: str = Field(default="default_user", description="The unique identifier for the user")
    adherent_id: Optional[str] = Field(default=None, description="The adherent ID in the system")
    medecin_id: Optional[str] = Field(default=None, description="The doctor ID in the system")
    store: Any = Field(default=None, description="The memory store for the workflow")
    
    TYPE_KEY: ClassVar[str] = "configuration"
    
    @classmethod
    def from_runnable_config(cls, config):
        """Extract the configuration from a runnable config.
        Supports both:
          - config["configurable"]["configuration"]  (schema'd blob)
          - config["configurable"]["store"]          (top-level convenience)
        """
        if config is None or not isinstance(config, dict):
            return cls(user_id="unknown")
        
        configurable = config.get("configurable", {}) or {}
        conf_blob = configurable.get(cls.TYPE_KEY, {}) or {}

        # Prefer explicit 'store' inside the config blob; fall back to top-level
        store = conf_blob.get("store", None)
        if store is None:
            store = configurable.get("store", None)

        return cls(
            user_id=conf_blob.get("user_id", "unknown"),
            adherent_id=conf_blob.get("adherent_id"),
            medecin_id=conf_blob.get("medecin_id"),
            store=store,
        )

    @classmethod
    def get_store(cls, config):
        """Small helper to consistently pull the store from config."""
        cfg = cls.from_runnable_config(config)
        return cfg.store