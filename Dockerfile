FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working dir
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose your app ports
EXPOSE 8501 5000

# Start both frontend and backend.
# If you’re using Streamlit for your frontend and Flask for your backend:
#  - We’ll launch them in the background using & and wait
CMD streamlit run frontend.py --server.port 8501 --server.headless true & \
    python app.py



