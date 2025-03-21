FROM python:3.13.2-bookworm


COPY app/ /app

#defualt variables
ENV Time=15


# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# PYTHON dependencies
    RUN pip install -r /app/requirements.txt

CMD ["python", "/app/main.py"]