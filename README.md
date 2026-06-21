# Daily Expense Logger

A minimal full-stack app for logging daily expenses and viewing a category summary. Built as a DevOps project — the app itself is intentionally small so the focus stays on containerization, CI/CD, and Kubernetes.

**Stack:** FastAPI (Python) · React (Vite) · PostgreSQL 16 · Docker · GitHub Actions · Kubernetes

---

## Repository layout

```
expense-logger/
├── backend/                  FastAPI app
│   ├── app/
│   │   ├── main.py           CRUD + summary endpoints
│   │   ├── models.py         SQLAlchemy Expense model
│   │   ├── schemas.py        Pydantic schemas
│   │   └── database.py       DB connection (config from env)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 React + Vite app
│   ├── src/{App.jsx,main.jsx,index.css}
│   ├── nginx.conf            serves /api → backend, / → SPA
│   └── Dockerfile            multi-stage (node build → nginx)
├── k8s/                      Kubernetes manifests
│   ├── 00-namespace.yaml
│   ├── 01-postgres-configmap.yaml
│   ├── 02-postgres-secret.yaml
│   ├── 03-postgres-service.yaml         headless service
│   ├── 04-postgres-statefulset.yaml
│   ├── 05-backend-configmap.yaml
│   ├── 06-backend-secret.yaml
│   ├── 07-backend-deployment.yaml
│   ├── 08-backend-service.yaml
│   ├── 09-frontend-deployment.yaml
│   ├── 10-frontend-service.yaml
│   └── 11-ingress.yaml
├── .github/workflows/ci-cd.yml
├── docker-compose.yml
└── .env.example
```

---

## API

| Method | Path                        | Description                          |
|-------:|-----------------------------|--------------------------------------|
| GET    | `/api/health`               | Health check                         |
| GET    | `/api/expenses`             | List recent expenses (limit param)   |
| POST   | `/api/expenses`             | Create an expense                    |
| DELETE | `/api/expenses/{id}`        | Delete an expense                    |
| GET    | `/api/summary?days=30`      | Totals grouped by category           |

---

## 1. Run locally with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend (Swagger UI): http://localhost:8000/docs

Tear down:
```bash
docker compose down -v
```

---

## 2. CI/CD with GitHub Actions

The pipeline (`.github/workflows/ci-cd.yml`) does the following on push to `main`:

1. **test-backend** — checks out the code, installs Python deps, runs a smoke import to catch broken modules.
2. **build-and-push** — builds both Docker images with Buildx and pushes to Docker Hub with two tags each:
   - `latest`
   - the short commit SHA (e.g. `a1b2c3d`) — useful for rollbacks and pinning manifests.
3. **deploy** *(optional, commented out)* — applies the k8s manifests to a cluster and rolls the new images.

### Required GitHub Secrets

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | your Docker Hub username |
| `DOCKERHUB_TOKEN` | a Docker Hub access token (Account Settings → Security) |

If you enable the CD step, also add:

| Secret | Value |
|---|---|
| `KUBECONFIG` | base64-encoded kubeconfig file: `base64 -w0 ~/.kube/config` |

---

## 3. Kubernetes deployment

Tested on **k3d** / **minikube** / **kind**. Any cluster with an nginx ingress controller will work.

### Prerequisites

```bash
# k3d example
k3d cluster create expense --port "8081:80@loadbalancer"

# minikube example
minikube start
minikube addons enable ingress
```

### Update image references

Before applying, replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username in:
- `k8s/07-backend-deployment.yaml`
- `k8s/09-frontend-deployment.yaml`

Quick one-liner:
```bash
sed -i 's/YOUR_DOCKERHUB_USERNAME/yourusername/g' k8s/07-backend-deployment.yaml k8s/09-frontend-deployment.yaml
```

### Apply manifests

```bash
kubectl apply -f k8s/
```

### Verify everything is running

```bash
kubectl get all -n expense-logger
kubectl get pvc,configmap,secret,ingress -n expense-logger
```

Expected output:
```
NAME                            READY   STATUS    RESTARTS   AGE
pod/postgres-0                  1/1     Running   0          1m
pod/backend-xxxxxxxxxx-xxxxx    1/1     Running   0          1m
pod/backend-xxxxxxxxxx-yyyyy    1/1     Running   0          1m
pod/frontend-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
pod/frontend-xxxxxxxxxx-yyyyy   1/1     Running   0          1m
```

### Access the app

Add a hosts entry pointing `expense.local` to your cluster's ingress IP:

```bash
# minikube
echo "$(minikube ip) expense.local" | sudo tee -a /etc/hosts

# k3d (mapped to localhost above)
echo "127.0.0.1 expense.local" | sudo tee -a /etc/hosts
```

Then open: <http://expense.local> (or with k3d port mapping: <http://expense.local:8081>)

### Demo commands for the presentation

```bash
# show namespace isolation
kubectl get ns
kubectl get all -n expense-logger

# show config & secrets are wired in
kubectl describe deployment backend -n expense-logger | grep -A 10 "Environment"

# show statefulset persistence
kubectl get pvc -n expense-logger
kubectl exec -n expense-logger postgres-0 -- psql -U expense_user -d expenses -c "\dt"

# show pod logs
kubectl logs -n expense-logger deployment/backend
kubectl logs -n expense-logger postgres-0

# kill a backend pod and watch it self-heal
kubectl delete pod -n expense-logger -l app=backend
kubectl get pods -n expense-logger -w

# scale backend up
kubectl scale deployment/backend -n expense-logger --replicas=3
```

### Clean up

```bash
kubectl delete namespace expense-logger
```

---

## Grading checklist

| % | Requirement | Where |
|---|---|---|
| 10 | Public Git repo | (push this folder to GitHub) |
| 10 | Dockerized | `backend/Dockerfile`, `frontend/Dockerfile` |
| 10 | Docker Compose orchestration | `docker-compose.yml` |
| 20 | CI/CD pipeline → DockerHub | `.github/workflows/ci-cd.yml` |
| 10 | Deployment + ConfigMaps/Secrets | `07-backend-deployment.yaml` + `05`, `06` |
| 10 | Service for the app | `08-backend-service.yaml`, `10-frontend-service.yaml` |
| 10 | Ingress | `11-ingress.yaml` |
| 10 | StatefulSet for DB + ConfigMaps/Secrets | `04-postgres-statefulset.yaml` + `01`, `02` |
| 10 | Manifests in a separate namespace | `00-namespace.yaml` (all resources scoped to it) |

---

## Security notes

The secrets in `k8s/02-postgres-secret.yaml` and `k8s/06-backend-secret.yaml` are committed only because this is a course project. For anything real, use one of:

- `kubectl create secret generic ... --from-literal=...` and don't commit
- [SealedSecrets](https://github.com/bitnami-labs/sealed-secrets)
- [SOPS](https://github.com/getsops/sops) with age/GPG
- External Secrets Operator backed by Vault / AWS SM / etc.
