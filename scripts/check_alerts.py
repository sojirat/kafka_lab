#!/usr/bin/env python3
"""
Check fraud alerts from Kafka topic
"""
from kafka import KafkaConsumer
import json
import sys

def main():
    try:
        consumer = KafkaConsumer(
            'fraud_alerts',
            bootstrap_servers='kafka:9092',
            auto_offset_reset='earliest',
            consumer_timeout_ms=10000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        count = 0
        for msg in consumer:
            count += 1
            if count <= 10:
                alert = msg.value
                amount = alert.get('Amount', 0)
                prob = alert.get('fraud_probability', 0)
                time = alert.get('event_time', 'N/A')
                print(f"🚨 Alert {count}: Amount=${amount:.2f}, Prob={prob:.4f}, Time={time}")

        print(f"\n✅ Total alerts: {count}")
        consumer.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
