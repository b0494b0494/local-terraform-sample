.PHONY: help install run test docker-build docker-run docker-compose-up docker-compose-down docker-compose-logs terraform-init terraform-plan terraform-apply terraform-destroy k8s-deploy-manifest k8s-delete-manifest clean

help:
	@echo "?????????:"
	@echo ""
	@echo "?? ???????????:"
	@echo "  make docker-compose-up  - Docker Compose???????"
	@echo "  make docker-compose-down - Docker Compose???????"
	@echo "  make docker-compose-logs - ?????"
	@echo ""
	@echo "?? ????????:"
	@echo "  make install            - Python???????????"
	@echo "  make run                - ????????????Python???"
	@echo "  make test               - ???????"
	@echo "  make docker-build    - Docker????????"
	@echo "  make docker-run      - Docker???????"
	@echo "  make terraform-init  - Terraform????"
	@echo "  make terraform-plan  - Terraform???????"
	@echo "  make terraform-apply - Terraform????????"
	@echo "  make terraform-destroy - Terraform????????"
	@echo "  make clean           - ???????"

install:
	pip install -r requirements.txt

run:
	python app.py

test:
	python test_app.py

test-redis:
	@echo "Testing Redis cache functionality..."
	python test_redis_cache.py

test-k8s:
	@echo "Testing Kubernetes features..."
	./test_k8s_features.sh

test-all: test test-redis
	@echo "All local tests completed"

docker-build:
	docker build -t sample-app:latest .

docker-run:
	docker run -p 8080:8080 sample-app:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f

terraform-init:
	terraform init

terraform-plan:
	terraform plan

terraform-apply:
	terraform apply

terraform-destroy:
	terraform destroy

k8s-deploy-manifest:
	kubectl apply -f k8s-manifests.yaml

k8s-delete-manifest:
	kubectl delete -f k8s-manifests.yaml

clean:
	terraform destroy -auto-approve || true
	kubectl delete namespace sample-app || true
