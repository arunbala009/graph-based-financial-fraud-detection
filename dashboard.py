import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv('API_URL', 'http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='Graph Fraud Detection', page_icon='🔎', layout='wide')
st.title('🔎 Graph-Based Financial Fraud Detection')
st.caption('Neo4j + FastAPI + Streamlit | Synthetic data | Academic demonstration')

def call(method, path, **kwargs):
    response = requests.request(method, API + path, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()

with st.sidebar:
    st.header('Project controls')
    if st.button('1. Create constraints'):
        try:
            st.success(call('POST', '/setup'))
        except Exception as e:
            st.error(str(e))
    if st.button('2. Load sample transactions'):
        try:
            st.success(call('POST', '/seed'))
            st.rerun()
        except Exception as e:
            st.error(str(e))

try:
    health = call('GET', '/health')
    transactions = call('GET', '/transactions')
    accounts = call('GET', '/accounts')
    alerts = call('GET', '/alerts')
except Exception as e:
    st.error(f'API or Neo4j is not connected: {e}')
    st.info('Check that uvicorn is running and the .env database credentials are correct.')
    st.stop()

st.success('Neo4j database connected')
a, b, c, d = st.columns(4)
a.metric('Accounts', len(accounts['items']))
b.metric('Transactions', len(transactions['items']))
c.metric('Suspicious cycles', alerts['count'])
d.metric('Alert query time', f"{alerts['query_time_ms']} ms")

st.subheader('Suspicious circular transfers')
st.caption('A → B → C → A. These are rule-based alerts, not proven fraud.')
if alerts['items']:
    st.dataframe(pd.DataFrame(alerts['items']), use_container_width=True, hide_index=True)
else:
    st.info('No 3-account cycles detected. Load the sample data first.')

st.subheader('Transaction history')
if transactions['items']:
    st.dataframe(pd.DataFrame(transactions['items']), use_container_width=True, hide_index=True)
else:
    st.info('No transactions found.')

with st.expander('Add a transaction', expanded=True):
    with st.form('new_transaction'):
        sender = st.text_input('Sender account ID', 'A')
        receiver = st.text_input('Receiver account ID', 'D')
        amount = st.number_input('Amount', min_value=0.01, value=1000.0)
        if st.form_submit_button('Create transaction'):
            try:
                call('POST', '/transactions', json={'sender': sender, 'receiver': receiver, 'amount': amount})
                st.rerun()
            except Exception as e:
                st.error(str(e))

with st.expander('Delete a transaction'):
    ids = [t['id'] for t in transactions['items']]
    if ids:
        selected = st.selectbox('Transaction ID', ids)
        if st.button('Delete selected transaction'):
            try:
                call('DELETE', f'/transactions/{selected}')
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        st.info('Nothing to delete.')

st.caption(f"Transaction query: {transactions['query_time_ms']} ms | Alert query: {alerts['query_time_ms']} ms. Neo4j server-reported result availability times; not end-to-end latency.")
