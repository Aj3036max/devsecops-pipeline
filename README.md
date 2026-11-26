# 🔐 DevSecOps Pipeline

![DevSecOps](https://github.com/Aj3036max/devsecops-pipeline/actions/workflows/devsecops.yml/badge.svg)
![Docker](https://img.shields.io/badge/docker-non--root-2496ED?logo=docker&logoColor=white)
![Jenkins](https://img.shields.io/badge/jenkins-pipeline-D24939?logo=jenkins&logoColor=white)

Pipeline **CI/CD sécurisée "shift-left"** autour d'une API Flask durcie.
Chaque push passe par **6 contrôles de sécurité automatiques** avant que l'image Docker soit publiée.
Le même pipeline existe en **GitHub Actions** et en **Jenkins**.

## 🔄 Le pipeline

```
 push / PR
    │
    ├── Lint & tests (ruff, pytest, couverture ≥ 90 %)
    ├── SAST ............ Bandit       → failles dans le code Python
    ├── SCA ............. pip-audit    → CVE dans les dépendances
    ├── Secrets ......... Gitleaks     → clés / mots de passe commités
    └── Dockerfile ...... Hadolint     → bonnes pratiques Docker
            │  (tout doit être vert)
            ▼
    Build image ─► Smoke test (non-root + /health) ─► Scan Grype ─► SBOM SPDX ─► Push GHCR (main)
```

> 💡 Pendant la création du projet, **pip-audit a bloqué Flask 3.1.2** (vulnérabilité PYSEC-2026-2151) :
> la dépendance a été mise à jour en 3.1.3. C'est exactement le rôle d'un pipeline DevSecOps.

## 🛡️ Mesures de sécurité appliquées

**Application (OWASP)**
- Validation stricte des entrées (type, longueur), `Content-Type` imposé
- Taille de requête limitée (16 Ko) → anti-DoS basique
- En-têtes de sécurité : CSP, HSTS, X-Frame-Options, nosniff, no-referrer
- Identifiants UUID (anti-IDOR), erreurs génériques sans stack trace
- Aucun secret en dur (`APP_SECRET_KEY` via variable d'environnement)

**Conteneur (CIS Docker Benchmark)**
- Build multi-stage, image `slim`, utilisateur **non-root (UID 10001)**
- `HEALTHCHECK`, `.dockerignore` (pas de `.git`, tests, `.env` dans l'image)
- docker-compose : `read_only`, `cap_drop: ALL`, `no-new-privileges`, limites CPU/RAM, port lié à 127.0.0.1

**Supply chain**
- Versions des dépendances épinglées, **Dependabot** (pip, Docker, Actions)
- **SBOM** SPDX généré à chaque build
- Token GitHub en lecture seule par défaut, `packages: write` seulement sur le job de publication

## 🚀 Lancer en local

```bash
# Python
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
python wsgi.py                                       # http://127.0.0.1:8000/health

# Docker
docker compose up --build
curl -X POST http://127.0.0.1:8000/api/notes -H "Content-Type: application/json" -d '{"title":"test"}'
```

## 📁 Structure

```
app/__init__.py              API Flask (factory create_app)
tests/                       tests pytest (fonctionnels + sécurité)
Dockerfile                   image durcie multi-stage
docker-compose.yml           exécution locale durcie
Jenkinsfile                  pipeline Jenkins équivalent
.github/workflows/           pipeline GitHub Actions
.github/dependabot.yml       mises à jour automatiques
```

## 🔭 Améliorations possibles

- Épingler les GitHub Actions par SHA de commit
- Signer l'image avec **cosign** (Sigstore) et vérifier la signature au déploiement
- DAST avec **OWASP ZAP** contre le conteneur lancé
- Déploiement sur Kubernetes (voir mon projet [k8s-security-lab](https://github.com/Aj3036max/k8s-security-lab))
