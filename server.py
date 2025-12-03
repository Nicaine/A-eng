services:
  - type: web
    name: auth-eng-mcp
    env: python
    root: .
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
