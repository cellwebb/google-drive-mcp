.PHONY: all setup run update-deps start-docker clean

all: setup run

setup:
	# Setup virtual environment and install dependencies
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r requirements.txt

run:
	# Run the application
	source .venv/bin/activate && python gdrive_server.py

update-deps:
	# Update dependencies
	source .venv/bin/activate && pip install --upgrade -r requirements.txt

start-docker:
	# Start Docker containers
	docker-compose up --build

clean:
	# Clean up temporary files and containers
	docker-compose down
	rm -rf .venv
	rm -rf __pycache__
