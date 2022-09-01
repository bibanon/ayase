FROM ubuntu:22.04
WORKDIR /opt/ayase
COPY requirements.txt /requirements.txt
RUN apt-get update && apt-get -y upgrade && apt-get -y --no-install-recommends install python3 python3-pip && pip3 install -r /requirements.txt && apt-get -y remove python3-pip && rm -rf /var/lib/apt/lists/*
COPY . /opt/ayase
CMD ["uvicorn","start_ayase:app", "--host", "0.0.0.0"]
