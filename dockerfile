FROM alpine:3.14

# Set environment variables
ENV TIME=15

# Copy application files
COPY app/ /app

# Install dependencies
RUN apk update && apk add --no-cache \
    python3 py3-pip ffmpeg libsndfile iputils && \
    rm -rf /var/cache/apk/*  # Clean up cache to reduce image size
# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt 

# Define the command
CMD ["python3", "/app/main.py"]
