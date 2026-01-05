#!/usr/bin/env python3
"""
Real-time Fraud Detection with Spark Structured Streaming

This script:
1. Trains a Logistic Regression model (if not exists)
2. Reads transactions from Kafka topic "transactions"
3. Applies ML model for fraud detection
4. Writes fraud alerts to Kafka topic "fraud_alerts"
5. Saves results to Parquet files
"""

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, when, window, count, avg, sum as _sum
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline, PipelineModel

# Configuration from environment variables
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "transactions")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "fraud_alerts")
MODEL_PATH = os.getenv("MODEL_PATH", "/work/models/fraud_lr_model")
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.5"))
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/work/checkpoints")
CSV_PATH = os.getenv("CSV_PATH", "/work/data/creditcard.csv")

print("=" * 80)
print("SPARK STRUCTURED STREAMING - FRAUD DETECTION")
print("=" * 80)
print(f"Kafka Bootstrap: {KAFKA_BOOTSTRAP}")
print(f"Input Topic: {INPUT_TOPIC}")
print(f"Output Topic: {OUTPUT_TOPIC}")
print(f"Model Path: {MODEL_PATH}")
print(f"Fraud Threshold: {FRAUD_THRESHOLD}")
print(f"CSV Path: {CSV_PATH}")
print("=" * 80)

# Create Spark Session
spark = SparkSession.builder \
    .appName("FraudDetectionStreaming") \
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR) \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Define schema for incoming Kafka messages
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("Time", DoubleType(), True),
    StructField("V1", DoubleType(), True),
    StructField("V2", DoubleType(), True),
    StructField("V3", DoubleType(), True),
    StructField("V4", DoubleType(), True),
    StructField("V5", DoubleType(), True),
    StructField("V6", DoubleType(), True),
    StructField("V7", DoubleType(), True),
    StructField("V8", DoubleType(), True),
    StructField("V9", DoubleType(), True),
    StructField("V10", DoubleType(), True),
    StructField("V11", DoubleType(), True),
    StructField("V12", DoubleType(), True),
    StructField("V13", DoubleType(), True),
    StructField("V14", DoubleType(), True),
    StructField("V15", DoubleType(), True),
    StructField("V16", DoubleType(), True),
    StructField("V17", DoubleType(), True),
    StructField("V18", DoubleType(), True),
    StructField("V19", DoubleType(), True),
    StructField("V20", DoubleType(), True),
    StructField("V21", DoubleType(), True),
    StructField("V22", DoubleType(), True),
    StructField("V23", DoubleType(), True),
    StructField("V24", DoubleType(), True),
    StructField("V25", DoubleType(), True),
    StructField("V26", DoubleType(), True),
    StructField("V27", DoubleType(), True),
    StructField("V28", DoubleType(), True),
    StructField("Amount", DoubleType(), True),
    StructField("Class", DoubleType(), True),  # Changed to DoubleType to match pandas
])


def train_model():
    """Train Logistic Regression model on historical data"""
    print("\n[TRAINING] Starting model training...")

    # Load historical data
    print(f"[TRAINING] Loading CSV from {CSV_PATH}")
    df = spark.read.csv(CSV_PATH, header=True, inferSchema=True)
    print(f"[TRAINING] Loaded {df.count()} records")

    # Prepare features
    feature_cols = [f"V{i}" for i in range(1, 29)] + ["Amount"]
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )

    # Create Logistic Regression model
    lr = LogisticRegression(
        featuresCol="features",
        labelCol="Class",
        maxIter=10,
        regParam=0.01,
        elasticNetParam=0.5
    )

    # Create pipeline
    pipeline = Pipeline(stages=[assembler, lr])

    # Train model
    print("[TRAINING] Training Logistic Regression model...")
    model = pipeline.fit(df)

    # Save model
    print(f"[TRAINING] Saving model to {MODEL_PATH}")
    model.write().overwrite().save(MODEL_PATH)

    print("[TRAINING] ✅ Model training completed successfully!")
    return model


def load_or_train_model():
    """Load existing model or train new one"""
    try:
        print(f"\n[MODEL] Checking if model exists at {MODEL_PATH}...")
        model = PipelineModel.load(MODEL_PATH)
        print("[MODEL] ✅ Model loaded from disk")
        return model
    except Exception as e:
        print(f"[MODEL] Model not found: {e}")
        return train_model()


def main():
    # Load or train model
    model = load_or_train_model()

    print("\n[STREAMING] Starting Kafka consumer...")

    # Read from Kafka
    df_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", INPUT_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .option("maxOffsetsPerTrigger", "1000") \
        .load()

    print("[STREAMING] ✅ Connected to Kafka")

    # Debug: print raw Kafka data
    print("[DEBUG] Setting up raw data monitoring...")

    # Parse JSON messages
    df_parsed = df_stream.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # Drop nulls from parsing errors
    df_parsed = df_parsed.filter(col("Amount").isNotNull())

    # Apply model for predictions
    print(f"[STREAMING] Applying ML model (threshold={FRAUD_THRESHOLD})...")
    predictions = model.transform(df_parsed)

    # Define UDF to extract probability from DenseVector
    from pyspark.ml.linalg import VectorUDT, Vectors
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType

    def extract_prob(probability_vector):
        """Extract fraud probability (class 1) from probability vector"""
        if probability_vector is not None:
            return float(probability_vector[1])
        return 0.0

    extract_prob_udf = udf(extract_prob, DoubleType())

    # Extract fraud probability (probability of class 1)
    df_with_score = predictions.withColumn(
        "fraud_probability",
        extract_prob_udf(col("probability"))
    )

    # Filter fraud alerts based on threshold
    fraud_alerts = df_with_score.filter(col("fraud_probability") >= FRAUD_THRESHOLD)

    # Prepare output: select relevant columns
    output_df = fraud_alerts.select(
        col("event_time"),
        col("Time"),
        col("V1"), col("V2"), col("V3"), col("V4"), col("V5"),
        col("V6"), col("V7"), col("V8"), col("V9"), col("V10"),
        col("V11"), col("V12"), col("V13"), col("V14"), col("V15"),
        col("V16"), col("V17"), col("V18"), col("V19"), col("V20"),
        col("V21"), col("V22"), col("V23"), col("V24"), col("V25"),
        col("V26"), col("V27"), col("V28"),
        col("Amount"),
        col("Class").alias("actual_class"),
        col("prediction").alias("predicted_class"),
        col("fraud_probability")
    )

    # Write to Kafka topic "fraud_alerts"
    print(f"[STREAMING] Writing fraud alerts to Kafka topic: {OUTPUT_TOPIC}")
    query_kafka = output_df \
        .select(to_json(struct("*")).alias("value")) \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("topic", OUTPUT_TOPIC) \
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/kafka_alerts") \
        .outputMode("append") \
        .trigger(processingTime="5 seconds") \
        .start()

    # Also write to Parquet files for batch analysis
    print("[STREAMING] Writing fraud alerts to Parquet files: /work/output_alerts")
    query_parquet = output_df \
        .writeStream \
        .format("parquet") \
        .option("path", "/work/output_alerts") \
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/parquet_alerts") \
        .outputMode("append") \
        .trigger(processingTime="10 seconds") \
        .start()

    # Console output for debugging
    query_console = output_df \
        .writeStream \
        .format("console") \
        .option("truncate", "false") \
        .option("numRows", "10") \
        .outputMode("append") \
        .trigger(processingTime="5 seconds") \
        .start()

    print("\n" + "=" * 80)
    print("🚀 FRAUD DETECTION STREAMING STARTED")
    print("=" * 80)
    print(f"📥 Reading from: {INPUT_TOPIC}")
    print(f"📤 Writing to: {OUTPUT_TOPIC}")
    print(f"🎯 Fraud threshold: {FRAUD_THRESHOLD}")
    print(f"💾 Parquet output: /work/output_alerts")
    print("=" * 80)
    print("\nWaiting for transactions... Press Ctrl+C to stop.\n")

    # Wait for all queries
    try:
        query_kafka.awaitTermination()
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping streaming queries...")
        query_kafka.stop()
        query_parquet.stop()
        query_console.stop()
        spark.stop()
        print("[SHUTDOWN] ✅ Graceful shutdown completed")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
