.PHONY: run
run:
	docker-compose up -d --build

.PHONY: poetry
poetry:  # start poetry shell for backend
	poetry install && poetry shell

.PHONY: lint
lint:
	poetry run python -m pylint app
