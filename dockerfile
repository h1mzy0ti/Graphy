FROM python:3.12.3
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
cmd ["python","graphycore/manage.py","runserver","0.0.0.0:8000"]