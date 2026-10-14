import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
URI = os.getenv('NEO4J_URI', '')
PASSWORD = os.getenv('NEO4J_PASSWORD', '')
DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')
if not URI or not PASSWORD or PASSWORD == 'YOUR_PASSWORD':
    raise RuntimeError('Fill in NEO4J_URI and NEO4J_PASSWORD in .env first')
driver = GraphDatabase.driver(URI, auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), PASSWORD))

def run(query, **params):
    records, summary, _ = driver.execute_query(query, parameters_=params, database_=DATABASE)
    return [r.data() for r in records], summary
