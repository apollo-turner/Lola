from fastapi import FastAPI
from pydantic import BaseModel
from agents.lola_agent import run_lola

app = FastAPI()

class Query(BaseModel):
    text: str

@app.post("/query")
def query_llm(q: Query):
    response = run_lola(q.text)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
