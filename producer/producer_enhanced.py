"""
Enhanced Kafka Producer for Fraud Detection Pipeline
Supports multiple streaming modes:
1. Steady rate mode (constant throughput)
2. Burst mode (periodic high-throughput bursts)
3. Late events injection mode (events with past timestamps)
"""

import os
import json
import time
import math
import random
import pandas as pd
from kafka import KafkaProducer
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration from environment variables
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("TOPIC", "transactions")
CSV_PATH = os.getenv("CSV_PATH", "/data/creditcard.csv")

# Basic parameters
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
SLEEP_MS = int(os.getenv("SLEEP_MS", "250"))
SPEED = float(os.getenv("SPEED", "1.0"))

# Streaming mode configuration
STREAM_MODE = os.getenv("STREAM_MODE", "steady")  # steady, burst, late_events

# Mode 1: Steady rate (default)
# Uses BATCH_SIZE and SLEEP_MS directly

# Mode 2: Burst mode parameters
BURST_ON_MS = int(os.getenv("BURST_ON_MS", "2000"))      # Burst duration (ms)
BURST_OFF_MS = int(os.getenv("BURST_OFF_MS", "10000"))   # Quiet period (ms)
BURST_BATCH_SIZE = int(os.getenv("BURST_BATCH_SIZE", "2000"))  # Records per burst

# Mode 3: Late events injection parameters
LATE_RATE = float(os.getenv("LATE_RATE", "0.05"))        # 5% late events
LATE_DELAY_MIN_SEC = int(os.getenv("LATE_DELAY_MIN_SEC", "30"))   # Min delay
LATE_DELAY_MAX_SEC = int(os.getenv("LATE_DELAY_MAX_SEC", "120"))  # Max delay


class StreamProducer:
    def __init__(self):
        print(f"[producer] Connecting to Kafka at {BOOTSTRAP}...")
        self.producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            linger_ms=10,
            acks=1,
            retries=3,
            max_block_ms=10000
        )
        print(f"[producer] ✅ Connected to Kafka")
        self.df = None
        self.mode = STREAM_MODE

    def load_data(self):
        """Load and prepare creditcard data"""
        self.df = pd.read_csv(CSV_PATH)
        # Drop exact duplicates
        self.df = self.df.drop_duplicates()

        # Create event_time as ISO string
        start_ts = pd.Timestamp.now().floor("s")
        self.df["event_time"] = (start_ts + pd.to_timedelta(self.df["Time"], unit="s")).astype(str)

        # Ensure stable column order
        cols = ["event_time", "Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
        self.df = self.df[cols]

        print(f"[producer] Loaded {len(self.df):,} records after deduplication")
        return len(self.df)

    def send_record(self, row: pd.Series, inject_late: bool = False):
        """Send a single record to Kafka"""
        record = row.to_dict()

        # Inject late event if requested
        if inject_late:
            delay_sec = random.randint(LATE_DELAY_MIN_SEC, LATE_DELAY_MAX_SEC)
            original_time = pd.Timestamp(record["event_time"])
            late_time = original_time - pd.Timedelta(seconds=delay_sec)
            record["event_time"] = str(late_time)
            record["_late_injected"] = True
            record["_late_delay_sec"] = delay_sec

        try:
            future = self.producer.send(TOPIC, record)
            # Don't wait for each message, but catch errors
            future.add_errback(lambda e: print(f"[ERROR] Failed to send: {e}"))
        except Exception as e:
            print(f"[ERROR] Exception sending record: {e}")

    def run_steady_mode(self):
        """Mode 1: Steady rate streaming"""
        print(f"[producer] Mode: STEADY")
        print(f"[producer] Batch size: {BATCH_SIZE}, Sleep: {SLEEP_MS}ms, Speed: {SPEED}x")

        n = len(self.df)
        batches = math.ceil(n / BATCH_SIZE)
        sleep_sec = (SLEEP_MS / 1000.0) / max(SPEED, 1e-6)

        sent_count = 0

        for b in range(batches):
            batch_start = time.time()
            part = self.df.iloc[b*BATCH_SIZE:(b+1)*BATCH_SIZE]

            for _, row in part.iterrows():
                self.send_record(row)
                sent_count += 1

            self.producer.flush()

            # Debug: show first batch details
            if b == 0:
                print(f"[producer] DEBUG: First batch sent {len(part)} records, total sent: {sent_count}")

            if sleep_sec > 0:
                time.sleep(sleep_sec)

            if (b + 1) % 20 == 0:
                elapsed = time.time() - batch_start
                rate = len(part) / elapsed if elapsed > 0 else 0
                print(f"[producer] Batch {b+1}/{batches} | Sent: {sent_count}/{n} | Rate: {rate:.1f} msg/s")

        self.producer.flush()
        print(f"[producer] Steady mode complete: {sent_count:,} records sent")

    def run_burst_mode(self):
        """Mode 2: Burst streaming (periodic high-throughput bursts)"""
        print(f"[producer] Mode: BURST")
        print(f"[producer] Burst ON: {BURST_ON_MS}ms, OFF: {BURST_OFF_MS}ms")
        print(f"[producer] Burst batch size: {BURST_BATCH_SIZE}")

        n = len(self.df)
        idx = 0
        cycle = 0

        burst_on_sec = BURST_ON_MS / 1000.0
        burst_off_sec = BURST_OFF_MS / 1000.0

        while idx < n:
            cycle += 1

            # BURST PHASE
            print(f"[producer] Cycle {cycle} - BURST ON ({burst_on_sec:.1f}s)")
            burst_start = time.time()
            burst_count = 0

            while (time.time() - burst_start) < burst_on_sec and idx < n:
                # Send up to BURST_BATCH_SIZE records
                batch_end = min(idx + BURST_BATCH_SIZE, n)
                part = self.df.iloc[idx:batch_end]

                for _, row in part.iterrows():
                    self.send_record(row)
                    burst_count += 1

                self.producer.flush()
                idx = batch_end

                # Small sleep to control burst rate
                time.sleep(0.01)

            burst_elapsed = time.time() - burst_start
            burst_rate = burst_count / burst_elapsed if burst_elapsed > 0 else 0
            print(f"[producer] Burst phase: {burst_count} records | Rate: {burst_rate:.1f} msg/s")

            if idx >= n:
                break

            # QUIET PHASE
            print(f"[producer] Cycle {cycle} - QUIET PERIOD ({burst_off_sec:.1f}s)")
            time.sleep(burst_off_sec)

        self.producer.flush()
        print(f"[producer] Burst mode complete: {n:,} records sent in {cycle} cycles")

    def run_late_events_mode(self):
        """Mode 3: Steady rate with late event injection"""
        print(f"[producer] Mode: LATE_EVENTS")
        print(f"[producer] Late rate: {LATE_RATE*100:.1f}% | Delay: {LATE_DELAY_MIN_SEC}-{LATE_DELAY_MAX_SEC}s")
        print(f"[producer] Batch size: {BATCH_SIZE}, Sleep: {SLEEP_MS}ms")

        n = len(self.df)
        batches = math.ceil(n / BATCH_SIZE)
        sleep_sec = (SLEEP_MS / 1000.0) / max(SPEED, 1e-6)

        late_count = 0
        on_time_count = 0

        for b in range(batches):
            part = self.df.iloc[b*BATCH_SIZE:(b+1)*BATCH_SIZE]

            for _, row in part.iterrows():
                # Randomly inject late events
                inject_late = random.random() < LATE_RATE
                self.send_record(row, inject_late=inject_late)

                if inject_late:
                    late_count += 1
                else:
                    on_time_count += 1

            self.producer.flush()

            if sleep_sec > 0:
                time.sleep(sleep_sec)

            if (b + 1) % 20 == 0:
                late_pct = (late_count / (late_count + on_time_count)) * 100 if (late_count + on_time_count) > 0 else 0
                print(f"[producer] Batch {b+1}/{batches} | Late: {late_count} ({late_pct:.1f}%) | On-time: {on_time_count}")

        self.producer.flush()
        total = late_count + on_time_count
        late_pct = (late_count / total) * 100 if total > 0 else 0
        print(f"[producer] Late events mode complete: {total:,} records | Late: {late_count} ({late_pct:.1f}%)")

    def run(self):
        """Run producer in configured mode"""
        print("="*80)
        print("ENHANCED KAFKA PRODUCER")
        print("="*80)
        print(f"Bootstrap: {BOOTSTRAP}")
        print(f"Topic: {TOPIC}")
        print(f"CSV: {CSV_PATH}")
        print(f"Mode: {self.mode.upper()}")
        print("="*80)

        n = self.load_data()

        if self.mode == "steady":
            self.run_steady_mode()
        elif self.mode == "burst":
            self.run_burst_mode()
        elif self.mode == "late_events":
            self.run_late_events_mode()
        else:
            print(f"[producer] ERROR: Unknown mode '{self.mode}'")
            print(f"[producer] Valid modes: steady, burst, late_events")
            return

        print("="*80)
        print("[producer] DONE")
        print("="*80)


def main():
    producer = StreamProducer()
    producer.run()


if __name__ == "__main__":
    main()
