#!/usr/bin/env python3
"""
Task D: Fraud Detection with Window KPI + Watermark
- Real-time streaming inference
- Windowed aggregations for KPIs
- Watermark for late event handling
- Checkpoint support
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, when, window, count, avg, sum as _sum,
    current_timestamp, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
)
from pyspark.ml import PipelineModel

# Configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "transactions")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "fraud_alerts")
KPI_TOPIC = os.getenv("KPI_TOPIC", "fraud_kpi")
MODEL_PATH = os.getenv("MODEL_PATH", "/work/models/fraud_lr_model")
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.5"))
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/work/checkpoints")
WATERMARK_DELAY = os.getenv("WATERMARK_DELAY", "2 minutes")  # Can be: "30 seconds", "2 minutes"
WINDOW_DURATION = os.getenv("WINDOW_DURATION", "1 minute")

print("=" * 80)
print("SPARK STRUCTURED STREAMING - FRAUD DETECTION WITH WINDOWS")
print("=" * 80)
print(f"Kafka Bootstrap: {KAFKA_BOOTSTRAP}")
print(f"Input Topic: {INPUT_TOPIC}")
print(f"Output Topic: {OUTPUT_TOPIC}")
print(f"KPI Topic: {KPI_TOPIC}")
print(f"Model Path: {MODEL_PATH}")
print(f"Fraud Threshold: {FRAUD_THRESHOLD}")
print(f"Watermark Delay: {WATERMARK_DELAY}")
print(f"Window Duration: {WINDOW_DURATION}")
print("=" * 80)

# Create Spark Session
spark = SparkSession.builder \
    .appName("FraudDetectionWithWindows") \
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR) \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Schema
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("Time", DoubleType(), True),
] + [StructField(f"V{i}", DoubleType(), True) for i in range(1, 29)] + [
    StructField("Amount", DoubleType(), True),
    StructField("Class", IntegerType(), True),
])

# Load model
print(f"\n[MODEL] Loading model from {MODEL_PATH}...")
try:
    model = PipelineModel.load(MODEL_PATH)
    print("[MODEL] ✅ Model loaded successfully")
except Exception as e:
    print(f"[MODEL] ❌ Error loading model: {e}")
    print("[MODEL] Please run task_a_audit.py first to train the model")
    sys.exit(1)

# Read from Kafka
print("\n[STREAMING] Starting Kafka consumer...")
df_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", INPUT_TOPIC) \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .load()

print("[STREAMING] ✅ Connected to Kafka")

# Parse JSON
df_parsed = df_stream.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# Convert event_time to timestamp
df_with_ts = df_parsed.withColumn(
    "event_timestamp",
    col("event_time").cast(TimestampType())
)

# Apply watermark for late event handling
df_watermarked = df_with_ts.withWatermark("event_timestamp", WATERMARK_DELAY)

print(f"[STREAMING] Watermark set to: {WATERMARK_DELAY}")

# Apply model
print(f"[STREAMING] Applying ML model (threshold={FRAUD_THRESHOLD})...")
predictions = model.transform(df_watermarked)

# Extract fraud probability
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

def extract_prob(probability_vector):
    if probability_vector is not None:
        return float(probability_vector[1])
    return 0.0

extract_prob_udf = udf(extract_prob, DoubleType())

df_with_score = predictions.withColumn(
    "fraud_probability",
    extract_prob_udf(col("probability"))
)

# Add processing timestamp
df_with_score = df_with_score.withColumn("processing_time", current_timestamp())

# ============================================================================
# Stream 1: Fraud Alerts (same as before)
# ============================================================================
fraud_alerts = df_with_score.filter(col("fraud_probability") >= FRAUD_THRESHOLD)

output_df = fraud_alerts.select(
    col("event_time"),
    col("event_timestamp"),
    col("processing_time"),
    col("Time"),
    *[col(f"V{i}") for i in range(1, 29)],
    col("Amount"),
    col("Class").alias("actual_class"),
    col("prediction").alias("predicted_class"),
    col("fraud_probability")
)

# Write fraud alerts to Kafka
print(f"[STREAMING] Writing fraud alerts to Kafka topic: {OUTPUT_TOPIC}")
query_alerts = output_df \
    .select(to_json(struct("*")).alias("value")) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("topic", OUTPUT_TOPIC) \
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/kafka_alerts") \
    .outputMode("append") \
    .start()

# Write to Parquet
query_parquet = output_df \
    .writeStream \
    .format("parquet") \
    .option("path", "/work/output_alerts") \
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/parquet_alerts") \
    .outputMode("append") \
    .trigger(processingTime="10 seconds") \
    .start()

# ============================================================================
# Stream 2: Windowed KPI Aggregations (NEW - Task D)
# ============================================================================
print(f"\n[KPI] Calculating windowed KPIs (window={WINDOW_DURATION})...")

# Calculate True Positives, False Positives, True Negatives, False Negatives
df_with_predictions = df_with_score.withColumn(
    "is_alert", (col("fraud_probability") >= FRAUD_THRESHOLD).cast("int")
).withColumn(
    "tp", when((col("is_alert") == 1) & (col("Class") == 1), 1).otherwise(0)
).withColumn(
    "fp", when((col("is_alert") == 1) & (col("Class") == 0), 1).otherwise(0)
).withColumn(
    "tn", when((col("is_alert") == 0) & (col("Class") == 0), 1).otherwise(0)
).withColumn(
    "fn", when((col("is_alert") == 0) & (col("Class") == 1), 1).otherwise(0)
)

# Windowed aggregations
windowed_kpi = df_with_predictions \
    .groupBy(window(col("event_timestamp"), WINDOW_DURATION)) \
    .agg(
        count("*").alias("n_txn"),
        _sum("is_alert").alias("n_alert"),
        _sum("tp").alias("tp"),
        _sum("fp").alias("fp"),
        _sum("tn").alias("tn"),
        _sum("fn").alias("fn"),
        avg("fraud_probability").alias("avg_fraud_prob"),
        avg("Amount").alias("avg_amount")
    )

# Calculate precision and recall
windowed_kpi_with_metrics = windowed_kpi.withColumn(
    "precision",
    when(col("tp") + col("fp") > 0, col("tp") / (col("tp") + col("fp"))).otherwise(0)
).withColumn(
    "recall",
    when(col("tp") + col("fn") > 0, col("tp") / (col("tp") + col("fn"))).otherwise(0)
).withColumn(
    "f1_score",
    when(
        (col("precision") + col("recall")) > 0,
        2 * col("precision") * col("recall") / (col("precision") + col("recall"))
    ).otherwise(0)
)

# Select output columns
kpi_output = windowed_kpi_with_metrics.select(
    col("window.start").alias("window_start"),
    col("window.end").alias("window_end"),
    col("n_txn"),
    col("n_alert"),
    col("tp"),
    col("fp"),
    col("tn"),
    col("fn"),
    col("precision"),
    col("recall"),
    col("f1_score"),
    col("avg_fraud_prob"),
    col("avg_amount")
)

# Write KPI to Kafka (for real-time monitoring)
print(f"[KPI] Writing KPIs to Kafka topic: {KPI_TOPIC}")
query_kpi_kafka = kpi_output \
    .select(to_json(struct("*")).alias("value")) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("topic", KPI_TOPIC) \
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/kafka_kpi") \
    .outputMode("update") \
    .start()

# Write KPI to Parquet (for batch analysis)
query_kpi_parquet = kpi_output \
    .writeStream \
    .format("parquet") \
    .option("path", "/work/output_kpi") \
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/parquet_kpi") \
    .outputMode("append") \
    .trigger(processingTime="30 seconds") \
    .start()

# Console output for debugging
query_console = kpi_output \
    .writeStream \
    .format("console") \
    .option("truncate", "false") \
    .outputMode("update") \
    .trigger(processingTime="30 seconds") \
    .start()

print("\n" + "=" * 80)
print("🚀 FRAUD DETECTION WITH WINDOWS STARTED")
print("=" * 80)
print(f"📥 Reading from: {INPUT_TOPIC}")
print(f"📤 Writing alerts to: {OUTPUT_TOPIC}")
print(f"📊 Writing KPIs to: {KPI_TOPIC}")
print(f"🎯 Fraud threshold: {FRAUD_THRESHOLD}")
print(f"⏰ Watermark: {WATERMARK_DELAY}")
print(f"🪟  Window: {WINDOW_DURATION}")
print(f"💾 Alerts output: /work/output_alerts")
print(f"📈 KPI output: /work/output_kpi")
print("=" * 80)
print("\nWaiting for transactions... Press Ctrl+C to stop.\n")

# Wait for all queries
try:
    query_alerts.awaitTermination()
except KeyboardInterrupt:
    print("\n\n[SHUTDOWN] Stopping streaming queries...")
    query_alerts.stop()
    query_parquet.stop()
    query_kpi_kafka.stop()
    query_kpi_parquet.stop()
    query_console.stop()
    spark.stop()
    print("[SHUTDOWN] ✅ Graceful shutdown completed")
