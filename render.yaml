services:
  - type: web
    name: A-eng
    env: python
    plan: free        # free tier is fine; it’ll just spin down when idle
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    autoDeploy: true
    envVars: []
