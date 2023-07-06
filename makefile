tool:
	python3 create_tools.py

redis:
	kubectl apply -f redis.yaml

manifest:
	kubectl apply -f manifest.yaml

url:
	minikube service my-agent-service --url

delete:
	kubectl delete deployments --all
