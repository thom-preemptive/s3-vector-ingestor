#!/bin/bash
cd /Users/thomkozik/dev/agent2_ingestor/backend
export PYTHONPATH=/Users/thomkozik/dev/agent2_ingestor/backend
/Users/thomkozik/dev/agent2_ingestor/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload