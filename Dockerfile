FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8501
EXPOSE 5000

CMD ["sh", "-c", "streamlit run frontend.py & gunicorn app:app --bind 0.0.0.0:5000"]
