FROM python:3.8-slim

WORKDIR /opt/apps/mstc_ping

COPY mstc_ping.py mstc_ping.py

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt


CMD ["python","-u","mstc_ping.py"]