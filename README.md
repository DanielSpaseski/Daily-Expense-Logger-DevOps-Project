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
