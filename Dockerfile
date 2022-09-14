FROM python:3.10.7-bullseye
WORKDIR /opt/ayase

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "start_ayase:app", "--host", "0.0.0.0", "--port", "8000"]
