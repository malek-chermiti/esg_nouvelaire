from fastapi import FastAPI

app = FastAPI(title="ESG Nouvelair API")

@app.get("/")
def root():
    return {"message": "ESG Nouvelair API fonctionne!"}