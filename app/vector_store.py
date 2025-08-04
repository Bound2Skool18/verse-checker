from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

def get_client():
    client = QdrantClient(path="qdrant_data")  # Persistent Qdrant store

    if not client.collection_exists("bible"):
        client.create_collection(
            collection_name="bible",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    return client

def search_verse(client, model, quote):
    vector = model.encode(quote).tolist()
    search = client.search(
        collection_name="bible",
        query_vector=vector,
        limit=1
    )
    if search:
        m = search[0]
        return {
            "match": m.score > 0.5,
            "score": m.score,
            "reference": f"{m.payload['book']} {m.payload['chapter']}:{m.payload['verse']}",
            "text": m.payload["text"]
        }
    return {"match": False, "message": "No verse found. Possibly a misattributed quote."}
