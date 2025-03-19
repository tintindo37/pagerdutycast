FROM python:3.12.3


COPY app/ /app

#defualt variables
ENV Time=10


# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# PYTHON dependencies
    RUN pip install -r /app/requirements.txt

CMD ["python", "/app/main.py"]