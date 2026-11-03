FROM python:3.12-slim
WORKDIR /opt/assurance-lab
COPY src ./src
COPY common.py ./common.py
COPY RSAP ./RSAP
ENV PYTHONPATH=/opt/assurance-lab/src:/opt/assurance-lab
CMD ["python", "RSAP/run_rsap_v2.py"]
