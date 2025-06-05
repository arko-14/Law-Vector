FROM python:3.10-slim

# Prevents Python from writing .pyc files to disc and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Copy all project files
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install supervisor

# Expose Streamlit and Flask ports
EXPOSE 8501
EXPOSE 5000

# Copy the supervisord config
COPY supervisord.conf /etc/supervisord.conf

# Run both the frontend and backend
CMD ["supervisord", "-c", "/etc/supervisord.conf"]

