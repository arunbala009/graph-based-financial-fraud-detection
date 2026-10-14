# Graph-Based Financial Fraud Detection — MVP

## Prerequisites
- Windows laptop with Python 3.10+ and VS Code
- Free Neo4j AuraDB instance

## Setup in VS Code terminal (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` with your AuraDB URI and password. Never share or commit `.env`.

## Run
Terminal 1:
```powershell
uvicorn main:app --reload
```
Visit http://127.0.0.1:8000/docs and use GET /health, POST /setup, POST /seed.

Terminal 2 (activate the environment again):
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run dashboard.py
```
Visit http://localhost:8501 . Click 'Create constraints', then 'Load sample transactions'.

## Neo4j Browser visualization
Run this query in Neo4j's query interface:
```cypher
MATCH (a:Account)-[s:SENT]->(t:Transaction)-[r:RECEIVED_BY]->(b:Account)
RETURN a,s,t,r,b LIMIT 50;
```

## Demo sequence
1. Show architecture and schema (Review 1).
2. Show graph nodes and relationships in Neo4j, FastAPI /docs, add/delete a transaction (Review 2).
3. Show cycle alerts A→B→C→A and actual query timings; take screenshots (Review 3).

## Limitations
- Data is synthetic, not real bank data.
- Cycles are heuristic suspicious patterns, not confirmed fraud.
- This detects directed 3-account cycles only, not all types of fraud.
- Timing is Neo4j driver summary `result_available_after` in milliseconds, not a controlled scalability benchmark.
