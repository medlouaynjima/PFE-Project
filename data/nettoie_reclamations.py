import pandas as pd

# 1. Charger le CSV
input_path = "data/reclamations_nettoyees.csv"
output_path = "data/reclamations_nettoyees_clean.csv"
df = pd.read_csv(input_path)

# 2. Nettoyage de base
# Supprimer les lignes où la réclamation est vide
df = df.dropna(subset=['reclamation'])

# Supprimer les doublons sur (reclamation, reponse)
df = df.drop_duplicates(subset=['reclamation', 'reponse'])

# Nettoyer les espaces et caractères spéciaux
for col in ['reclamation', 'reponse', 'nature_reclamation', 'objet']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

# Filtrer les réclamations trop courtes
df = df[df['reclamation'].str.len() > 20]

# Supprimer les réclamations dont la réponse est 'Dossier déjà traité' (insensible à la casse et espaces)
df = df[~df['reponse'].str.strip().str.lower().eq('dossier déjà traité')]

# Supprimer les réclamations dont la réponse est 'nan' (valeur manquante ou chaîne 'nan')
df = df[~df['reponse'].isna()]
df = df[~df['reponse'].str.strip().str.lower().eq('nan')]

# Supprimer les réclamations dont la réponse est une phrase générique de traitement
phrases_generiques = [
    'dossier bien traité',
    'la requête est bien traitée',
    'bonjour, la réclamation est bien traité',
    'bonjour, le dossier est bien traité. cordialement.',
    'bonjour, la réclamation est bien traité.',
    'bonjour, le dossier est bien traité. cordialement.'
]
for phrase in phrases_generiques:
    df = df[~df['reponse'].str.strip().str.lower().eq(phrase)]

# 3. Sauvegarder le CSV nettoyé
print(f"Nettoyage terminé. {len(df)} lignes conservées. Fichier: {output_path}")
df.to_csv(output_path, index=False) 