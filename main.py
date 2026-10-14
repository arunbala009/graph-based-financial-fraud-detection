from datetime import datetime, timezone
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from db import run, driver

app = FastAPI(title='Graph-Based Financial Fraud Detection', version='1.0')

class Transfer(BaseModel):
    sender: str = Field(min_length=1)
    receiver: str = Field(min_length=1)
    amount: float = Field(gt=0)

@app.get('/health')
def health():
    try:
        driver.verify_connectivity()
        return {'status': 'connected'}
    except Exception as exc:
        raise HTTPException(503, str(exc))

@app.post('/setup')
def setup():
    run('CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE')
    run('CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE')
    return {'status': 'constraints created'}

@app.post('/seed')
def seed():
    samples = [
        ('T001', 'A', 'B', 5000), ('T002', 'B', 'C', 4800),
        ('T003', 'C', 'A', 4700), ('T004', 'D', 'E', 300),
        ('T005', 'E', 'F', 150), ('T006', 'G', 'H', 900),
    ]
    for tid, sender, receiver, amount in samples:
        run('''
        MERGE (a:Account {id:$sender})
        MERGE (b:Account {id:$receiver})
        MERGE (t:Transaction {id:$tid})
          ON CREATE SET t.amount=$amount, t.created_at=$created_at
        MERGE (a)-[:SENT]->(t)
        MERGE (t)-[:RECEIVED_BY]->(b)
        ''', tid=tid, sender=sender, receiver=receiver, amount=amount,
            created_at=datetime.now(timezone.utc).isoformat())
    return {'status': 'sample data ready', 'transactions_in_seed': len(samples)}

@app.post('/transactions')
def create_transaction(tx: Transfer):
    if tx.sender == tx.receiver:
        raise HTTPException(400, 'Sender and receiver must differ')
    tid = str(uuid4())[:8]
    run('''
    MERGE (a:Account {id:$sender})
    MERGE (b:Account {id:$receiver})
    CREATE (t:Transaction {id:$tid, amount:$amount, created_at:$created_at})
    CREATE (a)-[:SENT]->(t)
    CREATE (t)-[:RECEIVED_BY]->(b)
    ''', sender=tx.sender.strip(), receiver=tx.receiver.strip(), amount=tx.amount,
        tid=tid, created_at=datetime.now(timezone.utc).isoformat())
    return {'id': tid, **tx.model_dump()}

@app.get('/transactions')
def transactions():
    rows, summary = run('''
    MATCH (a:Account)-[:SENT]->(t:Transaction)-[:RECEIVED_BY]->(b:Account)
    RETURN t.id AS id, a.id AS sender, b.id AS receiver,
           t.amount AS amount, t.created_at AS created_at
    ORDER BY created_at DESC LIMIT 200
    ''')
    return {'items': rows, 'query_time_ms': summary.result_available_after}

@app.get('/accounts')
def accounts():
    rows, _ = run('MATCH (a:Account) RETURN a.id AS id ORDER BY id')
    return {'items': rows}

@app.delete('/transactions/{tid}')
def delete_transaction(tid: str):
    rows, _ = run('''
    MATCH (t:Transaction {id:$tid})
    WITH t, t.id AS deleted_id
    DETACH DELETE t
    RETURN deleted_id
    ''', tid=tid)
    if not rows:
        raise HTTPException(404, 'Transaction not found')
    return {'deleted': tid}

@app.get('/alerts')
def alerts():
    # Directed 3-account cycles: A -> B -> C -> A. One result per unique account cycle.
    rows, summary = run('''
    MATCH (a:Account)-[:SENT]->(t1:Transaction)-[:RECEIVED_BY]->(b:Account)
    MATCH (b)-[:SENT]->(t2:Transaction)-[:RECEIVED_BY]->(c:Account)
    MATCH (c)-[:SENT]->(t3:Transaction)-[:RECEIVED_BY]->(a)
    WHERE a <> b AND b <> c AND c <> a
      AND a.id < b.id AND a.id < c.id
    RETURN a.id AS account_1, b.id AS account_2, c.id AS account_3,
           t1.id AS transaction_1, t2.id AS transaction_2,
           t3.id AS transaction_3,
           t1.amount+t2.amount+t3.amount AS total_flow
    LIMIT 100
    ''')
    return {'items': rows, 'count': len(rows),
            'query_time_ms': summary.result_available_after,
            'disclaimer': 'Suspicious circular transfers, not confirmed fraud.'}
