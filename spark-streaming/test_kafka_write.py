#!/usr/bin/env python3
"""
Simple test to write to Kafka from Spark
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

spark = SparkSession.builder \
    .appName("KafkaWriteTest") \
    .getOrCreate()

# Create a simple DataFrame
data = [{"message": "test from spark", "value": 123}]
df = spark.createDataFrame(data)

# Try to write to Kafka
try:
    df.select(lit('{"test": "from spark"}').alias("value")) \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("topic", "fraud_alerts") \
        .save()
    print("✅ Successfully wrote to Kafka!")
except Exception as e:
    print(f"❌ Error writing to Kafka: {e}")

spark.stop()
