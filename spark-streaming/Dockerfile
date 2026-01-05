FROM jupyter/pyspark-notebook:latest

USER root

# Install additional Python packages
RUN pip install --no-cache-dir \
    kafka-python==2.0.2 \
    pandas==2.1.4

# Copy fraud detection scripts
COPY fraud_detection.py /home/jovyan/fraud_detection.py
COPY fraud_detection_working.py /home/jovyan/fraud_detection_working.py
COPY fraud_detection_batch.py /home/jovyan/fraud_detection_batch.py

# Set working directory
WORKDIR /home/jovyan

# Make scripts executable
RUN chmod +x *.py && \
    chown -R ${NB_UID}:${NB_GID} /home/jovyan

USER ${NB_UID}

# Default command
CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "--master", "local[*]", \
     "--driver-memory", "2g", \
     "--executor-memory", "2g", \
     "/home/jovyan/fraud_detection.py"]
