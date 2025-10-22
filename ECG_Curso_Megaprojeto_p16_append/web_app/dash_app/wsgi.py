from app import app

# Gunicorn expects a WSGI callable named 'application'
application = app.server
