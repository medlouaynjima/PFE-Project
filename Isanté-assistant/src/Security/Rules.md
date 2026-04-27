# Règles de Sécurité SQL – Assistant Santé/Assurance

---

**Règle : Utiliser uniquement des requêtes SELECT**  
**Description :**  
Seules les requêtes SELECT sont autorisées pour la récupération de données.  
Aucune requête INSERT, UPDATE, DELETE, DROP, etc. n'est permise.

**Exemple :**
```sql
SELECT * FROM dossier WHERE adherent_id = '{adherent_id}'
```

---

**Règle : Filtrer par identifiant utilisateur**  
**Description :**  
Toutes les requêtes doivent inclure un filtre sur l'identifiant de l'utilisateur connecté :  
- `adherent_id = '{adherent_id}'` pour un adhérent  
- `medecin_id = '{medecin_id}'` pour un médecin

**Exemple :**
```sql
SELECT * FROM remboursement WHERE adherent_id = '{adherent_id}'
SELECT * FROM dossier WHERE medecin_id = '{medecin_id}'
```

---

**Règle : Interdiction des patterns d'injection SQL**  
**Description :**  
Aucun pattern pouvant mener à une injection SQL n'est autorisé (pas de `--`, de `;`, de concaténation dynamique non sécurisée).

**Exemple interdit :**
```sql
SELECT * FROM dossier WHERE adherent_id = '{adherent_id}'; DROP TABLE user
```

---

**Règle : Interdiction des opérations UNION**  
**Description :**  
Aucune opération UNION n'est autorisée pour éviter le contournement des filtres de sécurité.

**Exemple interdit :**
```sql
SELECT * FROM dossier WHERE adherent_id = '{adherent_id}' UNION SELECT * FROM dossier
```

---

**Règle : Respect du RGPD et de la confidentialité**  
**Description :**  
Ne jamais exposer ou requêter des données personnelles sensibles (CIN, RIB, nom complet d'un tiers, etc.) sauf si strictement nécessaire et autorisé.

**Exemple :**
- Préférer l'identifiant ou un champ anonymisé à la place du nom complet.

---

**Règle : Isolation stricte des données**  
**Description :**  
Un utilisateur (adhérent ou médecin) ne peut accéder qu'à ses propres données ou à celles de ses patients/malades en charge.  
Aucune requête ne doit permettre d'accéder aux données d'un autre utilisateur.

**Exemple interdit :**
```sql
SELECT * FROM dossier WHERE adherent_id != '{adherent_id}'
```

---

**Règle : Pas d'accès direct aux identifiants techniques**  
**Description :**  
Ne jamais exposer d'identifiants techniques internes (ID de base, clés primaires non anonymisées) dans les réponses utilisateur.

---

**Règle : Anonymisation des données sensibles**  
**Description :**  
Si une information sensible doit être affichée, elle doit être anonymisée (ex : masquer une partie du RIB, du CIN, etc.).

**Exemple :**
Afficher : `CIN: XXXXXX123` au lieu du CIN complet.

---

**Règle : Accès restreint aux dossiers des malades en charge**  
**Description :**  
Un adhérent ne peut voir que les dossiers de ses propres malades en charge.  
Un médecin ne peut voir que les dossiers des patients qu'il a traités.

---

**Règle : Pas de jointures non filtrées**  
**Description :**  
Toute jointure entre tables doit respecter les règles de filtrage par identifiant utilisateur.

---

## Résumé
- **Sécurité, confidentialité, et filtrage strict** sont obligatoires dans toutes les requêtes générées ou validées par l'assistant.
- **Aucune opération destructive ou risquée** n'est permise.
- **Toujours filtrer par l'identifiant de l'utilisateur connecté**. 