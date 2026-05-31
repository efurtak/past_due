.PHONY: up down prod_up prod_down

up:
	docker compose up --build -d

down:
	docker compose down

prod_up:
	docker compose -f docker-compose.prod.yaml up --build -d 

prod_down:
	docker compose -f docker-compose.prod.yaml down