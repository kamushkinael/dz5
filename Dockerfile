FROM python:3.9-slim
WORKDIR /app
RUN pip install flask flask-sqlalchemy psycopg2-binary redis gunicorn
COPY app.py .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
