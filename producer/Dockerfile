FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir pandas kafka-python

WORKDIR /app
COPY producer.py /app/producer.py
COPY producer_enhanced.py /app/producer_enhanced.py

CMD ["python","producer.py"]
