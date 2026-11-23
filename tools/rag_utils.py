from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

def setup_schemes_rag():
    """
    Schemes ki file ko parh kar ChromaDB mein save karta hai.
    """
    file_path = "data/schemes.txt"
    
    # Agar file nahi mili toh error do
    if not os.path.exists(file_path):
        return None

    # 1. Document Load karo
    loader = TextLoader(file_path, encoding="utf-8")
    docs = loader.load()

    # 2. Text ko chhote chunks mein todo
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # 3. Embeddings banao (HuggingFace ka free model)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 4. Vector Store banao
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    
    return vectorstore

def ask_schemes(vectorstore, query):
    """
    User ke sawaal ke mutabiq schemes dhoondta hai.
    """
    if not vectorstore:
        return "Maaf kijiyega, schemes ka data available nahi hai."
        
    # Similar documents dhoondo
    docs = vectorstore.similarity_search(query, k=2)
    
    if not docs:
        return "Is sawaal ka jawab schemes mein nahi mila."
        
    # Jo text mila, usko wapas kar do (AI isko parh kar jawab dega)
    context = "\n\n".join([doc.page_content for doc in docs])
    return context