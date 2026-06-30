import os

# server.py reads config at import time; provide a dummy client id for tests.
os.environ.setdefault("EXCHANGE_AI_CLIENT_ID", "test-client-id")
