FROM alpine:latest

# Set environment variables
ENV TIME=15

# Copy application files
COPY app/ /app

# Install dependencies
RUN apk add --no-cache python3 py3-pip ffmpeg libsndfile iputils

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt --break-system-packages

# Define the command
CMD ["python3", "/app/main.py"]
