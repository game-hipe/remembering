FROM python:3.14.2-slim-bookworm

WORKDIR /app

RUN mkdir /app/www
RUN mkdir /app/www/img
RUN mkdir /app/www/video

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

VOLUME ["/app/www"]

CMD ["python", "main.py"]