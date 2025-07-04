.PHONY: all backend frontend run stop

all: run

backend:
	@echo "Starting backend server..."
	@cd backend && uv run -- uvicorn main:app --reload --host 0.0.0.0 --port 8000 & echo $$! > .backend.pid

frontend:
	@echo "Starting frontend server..."
	@cd frontend && uv run -- streamlit run app.py & echo $$! > .frontend.pid

run: backend frontend
	@echo "Backend and Frontend servers are starting in the background."
	@echo "Backend available at http://0.0.0.0:8000"
	@echo "Frontend available at http://localhost:8501"
	@echo "Use 'make stop' to stop the servers."

stop:
	@echo "Stopping servers..."
	@if [ -f .backend.pid ]; then kill `cat .backend.pid`; rm .backend.pid; fi
	@if [ -f .frontend.pid ]; then kill `cat .frontend.pid`; rm .frontend.pid; fi
	@echo "Servers stopped."