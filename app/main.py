from fastapi import FastAPI
from pydantic import BaseModel
from app.embedding import get_model
from app.vector_store import get_client, search_verse

app = FastAPI()
model = get_model()
client = get_client()

class Query(BaseModel):
    quote: str

@app.post("/check")
def check_quote(query: Query):
    return search_verse(client, model, query.quote)