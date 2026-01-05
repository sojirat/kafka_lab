#!/usr/bin/env python3
"""
BATCH VERSION: Read all data from Kafka and process in batch mode
This is guaranteed to work and show results immediately
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from pyspark.ml import PipelineModel

# Configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "transactions")
MODEL_PATH = os.getenv("MODEL_PATH", "/work/models/fraud_lr_model")
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.0186"))

print("="*80)
print("📊 BATCH FRAUD DETECTION (Reading from Kafka)")
print("="*80)

# Create Spark Session
spark = SparkSession.builder \
    .appName("FraudDetectionBatch") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Schema
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("Time", DoubleType(), True),
] + [StructField(f"V{i}", DoubleType(), True) for i in range(1, 29)] + [
    StructField("Amount", DoubleType(), True),
    StructField("Class", DoubleType(), True),
])

print("\n[BATCH] Reading ALL data from Kafka...")
df_kafka = spark.read \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", INPUT_TOPIC) \
    .option("startingOffsets", "earliest") \
    .option("endingOffsets", "latest") \
    .load()

total_messages = df_kafka.count()
print(f"[BATCH] ✅ Read {total_messages:,} messages from Kafka")

if total_messages == 0:
    print("[BATCH] ❌ No data in Kafka! Producer may not be running.")
    spark.stop()
    exit(1)

# Parse JSON
print("[BATCH] Parsing JSON messages...")
df_parsed = df_kafka \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*")

valid_count = df_parsed.filter(col("Amount").isNotNull()).count()
print(f"[BATCH] ✅ Parsed {valid_count:,} valid transactions")

# Load model
print("\n[MODEL] Loading model...")
model = PipelineModel.load(MODEL_PATH)
print("[MODEL] ✅ Model loaded")

# Apply model
print("[MODEL] Applying predictions...")
predictions = model.transform(df_parsed.filter(col("Amount").isNotNull()))

# Extract fraud probability
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

def extract_prob(prob_vector):
    if prob_vector is not None:
        return float(prob_vector[1])
    return 0.0

extract_prob_udf = udf(extract_prob, DoubleType())

predictions_with_prob = predictions.withColumn(
    "fraud_probability",
    extract_prob_udf(col("probability"))
)

# Filter frauds
frauds = predictions_with_prob.filter(col("fraud_probability") >= FRAUD_THRESHOLD)
fraud_count = frauds.count()

print(f"\n{'='*80}")
print(f"🚨 FRAUD DETECTION RESULTS")
print(f"{'='*80}")
print(f"Total transactions processed: {valid_count:,}")
print(f"Fraud alerts (prob >= {FRAUD_THRESHOLD}): {fraud_count:,}")
print(f"Fraud rate: {fraud_count/valid_count*100:.2f}%")
print(f"{'='*80}\n")

# Show sample alerts
print("📋 Sample Fraud Alerts:")
print("="*80)
frauds.select(
    "event_time",
    "Amount",
    "Class",
    "fraud_probability"
).orderBy(col("fraud_probability").desc()).show(20, truncate=False)

# Save results
print("\n[SAVE] Writing fraud alerts to Parquet...")
frauds.select(
    col("event_time"),
    col("Amount"),
    col("Class").alias("actual_class"),
    col("fraud_probability"),
    *[col(f"V{i}") for i in range(1, 29)]
).write.mode("overwrite").parquet("/work/output_alerts_batch")

print(f"[SAVE] ✅ Saved {fraud_count:,} fraud alerts to /work/output_alerts_batch")

print("\n" + "="*80)
print("✅ BATCH PROCESSING COMPLETE!")
print("="*80)

spark.stop()
