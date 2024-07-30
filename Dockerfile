FROM python:3.12

WORKDIR /app

VOLUME /app/data

COPY src /app/src/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["python3", "src/main.py"]