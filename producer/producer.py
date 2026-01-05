import os, json, time, math
import pandas as pd
from kafka import KafkaProducer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC     = os.getenv("TOPIC", "transactions")
CSV_PATH  = os.getenv("CSV_PATH", "/data/creditcard.csv")

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
SLEEP_MS   = int(os.getenv("SLEEP_MS", "250"))
SPEED      = float(os.getenv("SPEED", "1.0"))

def main():
    df = pd.read_csv(CSV_PATH)
    # Drop exact duplicates to reduce leakage in demos (optional)
    df = df.drop_duplicates()

    # Create event_time as ISO string (Spark will parse to timestamp)
    start_ts = pd.Timestamp.now().floor("s")
    df["event_time"] = (start_ts + pd.to_timedelta(df["Time"], unit="s")).astype(str)

    # Ensure stable column order
    cols = ["event_time", "Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
    df = df[cols]

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=10,
        acks=1,
    )

    n = len(df)
    batches = math.ceil(n / BATCH_SIZE)
    print(f"[producer] bootstrap={BOOTSTRAP} topic={TOPIC} rows={n} batch_size={BATCH_SIZE} batches={batches}")

    sleep_sec = (SLEEP_MS / 1000.0) / max(SPEED, 1e-6)

    for b in range(batches):
        part = df.iloc[b*BATCH_SIZE:(b+1)*BATCH_SIZE]
        # Send each row as one message
        for _, row in part.iterrows():
            producer.send(TOPIC, row.to_dict())
        producer.flush()
        if sleep_sec > 0:
            time.sleep(sleep_sec)

        if (b + 1) % 20 == 0:
            print(f"[producer] sent batches: {b+1}/{batches}")

    producer.flush()
    print("[producer] done")

if __name__ == "__main__":
    main()
