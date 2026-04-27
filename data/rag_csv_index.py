import pandas as pd
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# 1. Charger le CSV minimal
csv_path = "data/reclamations_rag_minimal.csv"
df = pd.read_csv(csv_path)

# 2. Préparer les passages à indexer
passages = [f"Réclamation : {q}\nRéponse : {r}" for q, r in zip(df['reclamation'], df['reponse'])]

# 3. Vectoriser et indexer avec ChromaDB
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma.from_texts(passages, embedding=embeddings, persist_directory="rag_reclamations_db")

print(f"Indexation terminée. {len(passages)} passages indexés dans rag_reclamations_db.")

# 4. Exemple de recherche sémantique
def retrieve_reclamations(question, k=3):
    docs = vectorstore.similarity_search(question, k=k)
    print("\n--- Passages les plus pertinents ---")
    for i, doc in enumerate(docs, 1):
        print(f"\n[{i}]\n{doc.page_content}\n")
    return docs

if __name__ == "__main__":
    # Exemple d'utilisation
    question = input("Pose une question pour tester le RAG : ")
    retrieve_reclamations(question) 