FROM python:3.11-bookworm

WORKDIR /app

COPY data.csv define.json fine_vector.py model1.3.py model_requirement.txt /app/

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install -r model_requirement.txt

CMD ["python3", "model1.3.py"]
