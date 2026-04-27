from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class ReclamationMedecinSummary(BaseModel):
    """Résumé d'une réclamation du médecin"""
    date: str = Field(description="Date de réclamation ou de résolution")
    description: str = Field(description="Objet de la réclamation")
    status: Optional[str] = Field(default=None, description="Statut de la réclamation")
    resolution_comment: Optional[str] = Field(default=None, description="Commentaire de résolution")


class MedecinFAQ(BaseModel):
    """Question fréquente posée par le médecin"""
    question: str = Field(description="Question posée")
    answer: Optional[str] = Field(default=None, description="Réponse fournie (si connue)")
    frequency: Optional[int] = Field(default=1, description="Nombre de fois posée")


class MedecinProfile(BaseModel):
    """
    Profil mémoire du médecin (utilisé par le chatbot)
    """
    medecin_name: Optional[str] = Field(description="Nom complet du médecin")
    medecin_id: str = Field(description="Identifiant unique du médecin", exclude=True)


    patients: List[Dict[str, Any]] = Field(default_factory=list, description="Liste des patients suivis")
    dossiers_actifs: List[Dict[str, Any]] = Field(default_factory=list, description="Dossiers récents traités")
    past_reclamations: List[Union[ReclamationMedecinSummary, Dict[str, Any]]] = Field(default_factory=list, description="Historique des réclamations")
    frequent_asked_questions: List[Union[MedecinFAQ, Dict[str, Any]]] = Field(default_factory=list, description="Questions fréquentes")
    preferences: List[str] = Field(default_factory=list, description="Préférences de traitement ou de contact")

    historique_questions: List[str] = Field(default_factory=list, description="Historique des questions posées")
    derniere_interaction: Optional[str] = Field(default=None, description="Date de dernière conversation")

    last_updated: Optional[str] = Field(default=None, description="Horodatage de dernière mise à jour")

    @field_validator('medecin_id')
    def validate_medecin_id(cls, v):
        """Ensure medecin_id is stored as a string even when excluded from serialization"""
        if v is not None:
            return str(v)
        return v
    
    def model_post_init(self, __context):
        """Set last_updated time on initialization"""
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
