FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY iot_simulator.py .

COPY startup.sh /startup.sh
RUN chmod +x /startup.sh
CMD ["/startup.sh"]

