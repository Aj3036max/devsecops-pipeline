from app import create_app

app = create_app()

if __name__ == "__main__":
    # Dev uniquement. En prod : gunicorn (voir Dockerfile). debug=False toujours.
    app.run(host="127.0.0.1", port=8000, debug=False)
