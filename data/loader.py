from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Loading all PDFs from the data folder and splitting them into pages

folder_path = Path(__file__).parent
vectorstore_path = folder_path / "movements"

all_pages = []
for file_path in sorted(folder_path.rglob("*.pdf")):
    print(f"Loading: {file_path.name}")
    loader = PyPDFLoader(str(file_path))
    pages = loader.load_and_split()
    all_pages.extend(pages)

print(f"Total pages loaded: {len(all_pages)}")

# Creating indexed vector embeddings from all documents

embeddings = HuggingFaceEmbeddings()
vectorstore = FAISS.from_documents(all_pages, embeddings)

# Persisting the vectorstore to disk

vectorstore.save_local(str(vectorstore_path))
print(f"Vectorstore saved to: {vectorstore_path}")

# Example: searching for similar vectors
docs = vectorstore.similarity_search("What was the most popular spending?", k=2)
for doc in docs:
    print(doc.page_content[:200])
