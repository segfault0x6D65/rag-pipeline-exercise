import chromadb

def setup_chromadb():
    client = chromadb.PersistentClient(path="./chromadb-rag")
    collection = client.get_or_create_collection(name="files")
    return collection