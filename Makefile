.PHONY: run
run:
	docker-compose --profile default up -d --build

.PHONY: poetry
poetry:
	poetry install && poetry shell

.PHONY: lint
lint:
	poetry run python -m pylint .

.PHONY: black
black:
	poetry run python -m black .

.PHONY: locust
locust:
	docker-compose --profile locust up --build locust -d

.PHONY: stop
stop:
	docker-compose --profile default --profile locust down
