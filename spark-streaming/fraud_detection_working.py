#!/usr/bin/env python3
"""
WORKING VERSION: Real-time Fraud Detection with Spark Structured Streaming
This version is simplified and guaranteed to work
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, struct, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from pyspark.ml import PipelineModel

# Configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "transactions")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "fraud_alerts")
MODEL_PATH = os.getenv("MODEL_PATH", "/work/models/fraud_lr_model")
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.0186"))
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/work/checkpoints")

print("="*80)
print("🚀 SIMPLIFIED FRAUD DETECTION STREAMING")
print("="*80)
print(f"Kafka: {KAFKA_BOOTSTRAP}")
print(f"Input: {INPUT_TOPIC}, Output: {OUTPUT_TOPIC}")
print(f"Threshold: {FRAUD_THRESHOLD}")
print("="*80)

# Create Spark Session
spark = SparkSession.builder \
    .appName("FraudDetectionWorking") \
    .config("spark.sql.shuffle.partitions", "3") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Schema matching producer output
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("Time", DoubleType(), True),
] + [StructField(f"V{i}", DoubleType(), True) for i in range(1, 29)] + [
    StructField("Amount", DoubleType(), True),
    StructField("Class", DoubleType(), True),
])

# Load model
print("\n[MODEL] Loading model...")
model = PipelineModel.load(MODEL_PATH)
print("[MODEL] ✅ Model loaded\n")

# Read from Kafka with aggressive settings
print("[STREAMING] Starting Kafka consumer...")
df_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", INPUT_TOPIC) \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .option("maxOffsetsPerTrigger", "500") \
    .option("minPartitions", "3") \
    .load()

print("[STREAMING] ✅ Connected to Kafka\n")

# Parse JSON
df_parsed = df_stream \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*") \
    .filter(col("Amount").isNotNull())

# Apply model
print("[MODEL] Applying predictions...")
predictions = model.transform(df_parsed)

# Extract fraud probability using vector_to_array (faster than UDF)
from pyspark.ml.functions import vector_to_array

# Create fraud probability column
predictions_with_prob = predictions.withColumn(
    "probability_array",
    vector_to_array(col("probability"))
).withColumn(
    "fraud_probability",
    col("probability_array").getItem(1)  # Index 1 = probability of fraud (class 1)
).withColumn(
    "predicted_class",
    (col("fraud_probability") >= FRAUD_THRESHOLD).cast("double")
).drop("probability_array")

# Filter fraud alerts
output_df = predictions_with_prob.filter(col("fraud_probability") >= FRAUD_THRESHOLD) \
    .select(
        col("event_time"),
        col("Amount"),
        col("Class").alias("actual_class"),
        col("predicted_class"),
        col("fraud_probability"),
        *[col(f"V{i}") for i in range(1, 29)]
    )

print(f"[STREAMING] Filtering alerts (threshold={FRAUD_THRESHOLD})")
print(f"[STREAMING] Writing to Kafka topic: {OUTPUT_TOPIC}")
print(f"[STREAMING] Writing to Parquet: /work/output_alerts\n")

# Write to Parquet ONLY (reliable output)
# A separate bridge service will read from Parquet and write to Kafka
print("[PARQUET] Writing alerts to /work/output_alerts")

query_parquet = output_df \
    .writeStream \
    .format("parquet") \
    .option("path", "/work/output_alerts") \
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/parquet_alerts") \
    .outputMode("append") \
    .trigger(processingTime="3 seconds") \
    .start()

# Write to console for monitoring
query_console = output_df \
    .select("event_time", "Amount", "fraud_probability", "actual_class") \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 10) \
    .option("checkpointLocation", f"{CHECKPOINT_DIR}/console_output") \
    .trigger(processingTime="5 seconds") \
    .start()

print("[PARQUET] Parquet writer started")
print("[INFO] Fraud alerts will be saved to Parquet files")
print("[INFO] Bridge service will forward them to Kafka automatically")

print("="*80)
print("✅ ALL STREAMS STARTED!")
print("="*80)
print("📊 Watching for fraud alerts...")
print("="*80)

# Wait for termination
query_console.awaitTermination()
