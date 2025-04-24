FROM python:3.12.10-slim

WORKDIR /app

COPY ./app /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

RUN python -m nltk.downloader punkt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
