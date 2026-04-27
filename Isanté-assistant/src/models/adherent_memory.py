from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class ReclamationSummary(BaseModel):
    """Résumé d’une réclamation passée"""
    date: str = Field(description="Date de la réclamation ou de la résolution")
    description: str = Field(description="Objet ou résumé de la réclamation")
    status: Optional[str] = Field(default=None, description="Statut de la réclamation (résolue, en attente, etc.)")
    resolution_comment: Optional[str] = Field(default=None, description="Commentaire de résolution s’il existe")


class AdherentFAQ(BaseModel):
    """Question fréquemment posée par l’adhérent"""
    question: str = Field(description="La question posée")
    answer: Optional[str] = Field(default=None, description="La réponse donnée (si connue)")
    frequency: Optional[int] = Field(default=1, description="Nombre de fois posée")


class AdherentProfile(BaseModel):
    """
    Profil mémoire de l’adhérent (utilisé par le chatbot)
    """
    adherent_name: Optional[str] = Field(description="Nom complet de l’adhérent")
    adherent_id: str = Field(description="Identifiant unique de l’adhérent", exclude=True)


    malades_en_charge: List[Dict[str, Any]] = Field(default_factory=list, description="Liste des membres de famille/malades associés")
    dossiers_actifs: List[Dict[str, Any]] = Field(default_factory=list, description="Dossiers médicaux récents")
    past_reclamations: List[Union[ReclamationSummary, Dict[str, Any]]] = Field(default_factory=list, description="Historique des réclamations")
    frequent_asked_questions: List[Union[AdherentFAQ, Dict[str, Any]]] = Field(default_factory=list, description="Questions fréquentes")
    preferences: List[str] = Field(default_factory=list, description="Préférences ou besoins particuliers")
    
    historique_questions: List[str] = Field(default_factory=list, description="Historique des questions posées")
    derniere_interaction: Optional[str] = Field(default=None, description="Date de dernière conversation")

    last_updated: Optional[str] = Field(default=None, description="Date de dernière mise à jour")

    @field_validator('adherent_id')
    def validate_adherent_id(cls, v):
        """Ensure adherent_id is stored as a string even when excluded from serialization"""
        if v is not None:
            return str(v)
        return v
    
    def model_post_init(self, __context):
        """Set last_updated time on initialization"""
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
