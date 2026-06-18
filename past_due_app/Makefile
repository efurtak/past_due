.PHONY: dev_up dev_down test_up test_logs test_down prod_up prod_down css

dev_up:
	docker compose -f docker-compose.dev.yaml --env-file .env.dev up --build -d

dev_down:
	docker compose -f docker-compose.dev.yaml --env-file .env.dev down

test_up:
	docker compose -f docker-compose.test.yaml --env-file .env.test up --build -d

test_logs:
	docker compose -f docker-compose.test.yaml --env-file .env.test logs web

test_down:
	docker compose -f docker-compose.test.yaml --env-file .env.test down

prod_up:
	docker compose -f docker-compose.prod.yaml --env-file .env.prod up --build -d 

prod_down:
	docker compose -f docker-compose.prod.yaml --env-file .env.prod down

css:
	./tailwindcss -i ./static/src/input.css -o ./static/output-past_due.css --watch