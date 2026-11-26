// Même pipeline DevSecOps que .github/workflows/devsecops.yml, version Jenkins.
// Prérequis sur l'agent : Docker. Les outils tournent dans des conteneurs => rien à installer.
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE = "devsecops-api:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Lint & tests') {
            agent { docker { image 'python:3.13-slim'; reuseNode true } }
            steps {
                sh '''
                    python -m venv .venv && . .venv/bin/activate
                    pip install -q -r requirements-dev.txt
                    ruff check .
                    pytest --junitxml=reports/junit.xml --cov=app --cov-fail-under=90
                '''
            }
            post { always { junit 'reports/junit.xml' } }
        }

        stage('Security scans') {
            parallel {
                stage('SAST - Bandit') {
                    agent { docker { image 'python:3.13-slim'; reuseNode true } }
                    steps { sh 'pip install -q bandit==1.9.4 && bandit -r app wsgi.py -c pyproject.toml --severity-level medium' }
                }
                stage('SCA - pip-audit') {
                    agent { docker { image 'python:3.13-slim'; reuseNode true } }
                    steps { sh 'pip install -q pip-audit==2.10.1 && pip-audit -r requirements.txt --strict' }
                }
                stage('Secrets - Gitleaks') {
                    steps { sh 'docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect --source /repo --no-banner' }
                }
                stage('Dockerfile - Hadolint') {
                    steps { sh 'docker run --rm -i hadolint/hadolint < Dockerfile' }
                }
            }
        }

        stage('Build image') {
            steps { sh 'docker build -t "$IMAGE" .' }
        }

        stage('Image scan - Grype') {
            steps {
                sh '''
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                        anchore/grype:latest "$IMAGE" --only-fixed --fail-on critical
                '''
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    docker rm -f api-smoke || true
                    docker run -d --name api-smoke "$IMAGE"
                    sleep 5
                    docker exec api-smoke python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
                    test "$(docker exec api-smoke id -u)" = "10001"
                '''
            }
            post { always { sh 'docker rm -f api-smoke || true' } }
        }
    }

    post {
        success { echo "Image ${IMAGE} validée : prête à déployer." }
        failure { echo 'Pipeline bloqué par un contrôle qualité ou sécurité.' }
    }
}
