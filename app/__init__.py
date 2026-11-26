"""API Flask volontairement simple, mais écrite selon les bonnes pratiques de sécurité (OWASP)."""

from __future__ import annotations

import os
import secrets
import uuid

from flask import Flask, abort, jsonify, request

MAX_TITLE = 120
MAX_BODY = 5_000


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        # Jamais de secret en dur : variable d'environnement, sinon valeur aléatoire éphémère.
        SECRET_KEY=os.environ.get("APP_SECRET_KEY", secrets.token_hex(32)),
        MAX_CONTENT_LENGTH=16 * 1024,  # limite la taille des requêtes (anti-DoS basique)
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)

    notes: dict[str, dict] = {}

    @app.after_request
    def security_headers(resp):
        # En-têtes recommandés par l'OWASP Secure Headers Project
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers.pop("Server", None)
        return resp

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    @app.errorhandler(415)
    def json_error(err):
        # Messages d'erreur génériques : pas de stack trace ni de détail interne divulgué.
        return jsonify(error=err.name, message=err.description), err.code

    def validate(payload) -> dict:
        if not isinstance(payload, dict):
            abort(400, "Le corps doit être un objet JSON.")
        title, body = payload.get("title"), payload.get("body", "")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= MAX_TITLE:
            abort(400, f"'title' est requis (1-{MAX_TITLE} caractères).")
        if not isinstance(body, str) or len(body) > MAX_BODY:
            abort(400, f"'body' doit être une chaîne de {MAX_BODY} caractères max.")
        return {"title": title.strip(), "body": body}

    def json_body():
        if not request.is_json:
            abort(415, "Content-Type application/json attendu.")
        return request.get_json(silent=True)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/notes")
    def list_notes():
        return jsonify(list(notes.values()))

    @app.post("/api/notes")
    def create_note():
        data = validate(json_body())
        note = {"id": str(uuid.uuid4()), **data}  # UUID : identifiants non devinables (anti-IDOR)
        notes[note["id"]] = note
        return jsonify(note), 201

    @app.get("/api/notes/<note_id>")
    def get_note(note_id: str):
        return jsonify(notes.get(note_id) or abort(404, "Note introuvable."))

    @app.delete("/api/notes/<note_id>")
    def delete_note(note_id: str):
        if notes.pop(note_id, None) is None:
            abort(404, "Note introuvable.")
        return "", 204

    return app
