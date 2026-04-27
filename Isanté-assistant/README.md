# Insurance Assistant

Un assistant intelligent pour la gestion des assurances, basé sur LangChain et LangGraph.

## Fonctionnalités

- Gestion des conversations avec les utilisateurs (adhérents et médecins)
- Traitement des réclamations
- Accès aux données d'assurance
- Gestion des polices et des couvertures
- Interface API REST avec FastAPI

## Prérequis

- Python 3.11 ou supérieur
- MySQL 8.0 ou supérieur
- Compte OpenAI avec accès à l'API

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-username/insurance-assistant.git
cd insurance-assistant
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :
```bash
poetry install
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
```
Puis modifiez le fichier `.env` avec vos configurations :
```
OPENAI_API_KEY=votre-clé-api
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre-mot-de-passe
DB_NAME=insurance_db
SECRET_KEY=votre-clé-secrète
```

5. Créer la base de données :
```sql
CREATE DATABASE insurance_db;
```

6. Exécuter les migrations :
```bash
python scripts/init_db.py
```

## Utilisation

1. Démarrer le serveur :
```bash
python -m src.app.app
```

2. Accéder à l'API :
- Documentation Swagger : http://localhost:8000/docs
- Documentation ReDoc : http://localhost:8000/redoc

3. Exemple d'utilisation avec curl :
```bash
# Authentification
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=adherent1&password=password123"

# Chat
curl -X POST "http://localhost:8000/api/chat" \
     -H "Authorization: Bearer votre-token" \
     -H "Content-Type: application/json" \
     -d '{"message": "Bonjour, je voudrais savoir le statut de ma réclamation"}'
```

## Structure du Projet

```
insurance-assistant/
├── src/
│   ├── agents/
│   │   ├── conversationalagent.py
│   │   ├── databaseagent.py
│   │   ├── claimsagent.py
│   │   ├── policyagent.py
│   │   ├── agentstage.py
│   │   └── utils/
│   ├── app/
│   │   └── app.py
│   ├── config/
│   │   └── agent_config.py
│   └── server/
│       └── main.py
├── tests/
├── scripts/
├── .env.example
├── pyproject.toml
└── README.md
```

## Agents

1. **ConversationalAgent** :
   - Gère les conversations générales
   - Route les requêtes vers les agents spécialisés
   - Maintient le contexte de la conversation

2. **DatabaseAgent** :
   - Gère les requêtes de données
   - Exécute des requêtes SQL sécurisées
   - Retourne les résultats formatés

3. **ClaimsAgent** :
   - Gère les réclamations
   - Suit le statut des réclamations
   - Guide les utilisateurs dans le processus

4. **PolicyAgent** :
   - Gère les informations sur les polices
   - Calcule les primes
   - Gère les modifications de couverture

## Sécurité

- Authentification JWT
- Validation des requêtes SQL
- Isolation des données utilisateur
- Logs d'activité

## Tests

```bash
pytest
```

## Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

MIT 