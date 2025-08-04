import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

def load_and_embed():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = QdrantClient(path="qdrant_data")

    if client.collection_exists("bible"):
        client.delete_collection("bible")
        print("🗑️  Deleted old 'bible' collection.")


    # Only create if it doesn't already exist
    if not client.collection_exists("bible"):
        client.create_collection(
            collection_name="bible",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

        with open("data/bible.json") as f:
            verses = json.load(f)

        points = []
        for i, verse in enumerate(verses):
            embedding = model.encode(verse["text"]).tolist()
            points.append(PointStruct(id=i, vector=embedding, payload=verse))

        client.upsert("bible", points=points)
        print("✅ Bible verses loaded and embedded.")
    else:
        print("⚠️  Bible collection already exists. Skipping reloading.")

if __name__ == "__main__":
    load_and_embed()
