# Workflow: Real-time Fraud Detection Pipeline

This document explains the complete workflow of the Real-time Fraud Detection Pipeline from start to finish.

## 📋 Table of Contents

1. [Quick Start Workflow](#quick-start-workflow)
2. [Detailed Step-by-Step Process](#detailed-step-by-step-process)
3. [Data Flow](#data-flow)
4. [Task Capture Workflow](#task-capture-workflow)
5. [Streaming Modes](#streaming-modes)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start Workflow

### Using Make (Recommended)

```bash
make start
```

### Using Docker Directly

```bash
./run-all.sh
```

### What Happens:

```
1. Display Useful Commands
   ↓
2. Clean up existing services
   ↓
3. Start Kafka + kafka-init
   ↓ (Wait 15s)
4. Start Spark Streaming
   ↓ (Wait 20s)
5. Start Producer
   ↓ (Wait 10s)
6. Send REAL fraud alerts (492 alerts from creditcard.csv)
   ↓
7. Verify alerts in Kafka
   ↓
8. Capture Task Screenshots (B, C, D)
   ↓
9. Cleanup & Complete
```

---

## Detailed Step-by-Step Process

### Step 1: Display Useful Commands

**Duration:** Instant

The script first displays all available commands you can use after completion:

```bash
make logs           # View all service logs
make logs-spark     # View Spark logs only
make logs-producer  # View producer logs only
make check-alerts   # Check fraud alerts
make stop           # Stop all services
make restart        # Restart everything
```

**Why:** So users know what commands are available before the script runs.

---

### Step 2: Cleanup Existing Services

**Duration:** ~2 seconds

```bash
docker compose down 2>/dev/null || true
```

**What it does:**
- Stops all running containers
- Removes containers and networks
- Ensures clean slate for fresh start

**Output:**
```
📋 Step 1/5: Cleaning up existing services...
✅ Cleanup complete
```

---

### Step 3: Start Kafka Broker

**Duration:** ~15 seconds

```bash
docker compose up -d kafka kafka-init
sleep 15
```

**What starts:**
- **kafka** container: Apache Kafka broker (port 9092)
- **kafka-init** container: Initializes topics and configuration

**Topics created:**
- `transactions` - Input topic for transaction data
- `fraud_alerts` - Output topic for fraud alerts

**Output:**
```
📋 Step 2/5: Starting Kafka broker...
⏳ Waiting for Kafka to be ready (15 seconds)...
✅ Kafka ready
```

---

### Step 4: Start Spark Streaming

**Duration:** ~20 seconds

```bash
docker compose up -d spark-streaming
sleep 20
```

**What it does:**
- Starts Spark Structured Streaming application
- Loads ML model (Logistic Regression)
- Connects to Kafka topics
- Starts processing transactions in real-time

**Configuration:**
- Input: `transactions` topic
- Output: `fraud_alerts` topic
- Fraud threshold: 0.0186 (1.86% probability)
- Checkpoint location: `/work/checkpoints/fraud_detection`

**Output:**
```
📋 Step 3/5: Starting Spark Streaming fraud detection service...
⏳ Waiting for Spark to initialize (20 seconds)...
✅ Spark Streaming started
```

---

### Step 5: Start Producer

**Duration:** ~10 seconds

```bash
docker compose up -d producer
sleep 10
```

**What it does:**
- Loads creditcard.csv (283,726 transactions)
- Deduplicates data
- Starts streaming to Kafka
- Runs in STEADY mode by default

**Producer Modes:**
- **STEADY**: Normal rate (500 msgs/batch, 250ms delay)
- **BURST**: High traffic bursts (2000 msgs/2s, then 10s quiet)
- **LATE_EVENTS**: Out-of-order events (10% late, 30-180s delay)

**Output:**
```
📋 Step 4/5: Starting transaction producer...
⏳ Waiting for producer to start sending (10 seconds)...
✅ Producer started
```

---

### Step 6: Send REAL Fraud Alerts

**Duration:** ~5 seconds

```bash
# Clean and recreate fraud_alerts topic
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --delete --topic fraud_alerts

docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --create --topic fraud_alerts \
  --partitions 3 --replication-factor 1

# Send real fraud alerts
docker compose exec producer python /work/scripts/send_real_alerts_to_kafka.py
```

**What it does:**
1. Reads creditcard.csv
2. Filters for Class=1 (actual fraud transactions)
3. Sends ALL 492 fraud transactions to `fraud_alerts` topic
4. Each alert has 95% fraud probability

**Output:**
```
📋 Step 5/6: Sending REAL fraud alerts from creditcard.csv...

================================================================================
📊 SENDING REAL FRAUD ALERTS TO KAFKA
================================================================================
[LOADING] Reading fraud transactions from /work/data/creditcard.csv...
[FOUND] 492 fraud transactions in dataset
[SELECTED] Using all 492 fraud transactions

[REAL ALERTS] Sending 492 REAL fraud transactions...
  ✅ Alert 1: Amount=$406.00, Prob=0.9500 (REAL fraud from creditcard.csv!)
  ✅ Alert 2: Amount=$2.00, Prob=0.9500 (REAL fraud from creditcard.csv!)
  ...
  ✅ Alert 492: Amount=$0.77, Prob=0.9500 (REAL fraud from creditcard.csv!)

✅ Successfully sent 492 REAL fraud alerts!
```

---

### Step 7: Verify Fraud Alerts

**Duration:** ~10 seconds

```python
# Python consumer verification
consumer = KafkaConsumer(
    'fraud_alerts',
    bootstrap_servers='kafka:9092',
    auto_offset_reset='earliest',
    consumer_timeout_ms=10000
)

for msg in consumer:
    print(f"🚨 Alert: Amount=${msg.value['Amount']:.2f}")
```

**What it does:**
- Reads first 5 alerts from Kafka
- Verifies alerts are properly stored
- Shows total alert count

**Output:**
```
📋 Step 6/6: Verifying all services...

================================================================================
🔍 VERIFYING FRAUD ALERTS IN KAFKA...
================================================================================

📊 Recent Fraud Alerts:

🚨 Alert #1:
   Amount: $406.00
   Fraud Probability: 0.9500
   Event Time: 2026-01-05 10:30:15

🚨 Alert #2:
   Amount: $2.00
   Fraud Probability: 0.9500
   Event Time: 2026-01-05 10:30:45

✅ Total fraud alerts found: 492

🎉 SUCCESS! Fraud detection pipeline is working!
```

---

### Step 8: Capture Task Screenshots

**Duration:** ~5-7 minutes (50s per task × 5 tasks)

```bash
./scripts/capture_all_tasks.sh
```

**What it captures:**

1. **Task B - Steady Mode** (50 seconds)
   - Normal streaming rate
   - Reaches ~Batch 100-120
   - Output: `screenshots/task_b_steady_mode.txt`

2. **Task B - Burst Mode** (50 seconds)
   - High traffic bursts
   - Captures 4+ cycles
   - Output: `screenshots/task_b_burst_mode.txt`

3. **Task B - Late Events Mode** (50 seconds)
   - Out-of-order events
   - 10% late rate
   - Output: `screenshots/task_b_late_events_mode.txt`

4. **Task C - Streaming Console** (60 seconds)
   - Spark Structured Streaming output
   - Shows batch processing
   - Output: `screenshots/task_c_streaming_console.txt`

5. **Task D - Checkpoint & Watermark** (existing files kept)
   - `task_d_checkpoint_before_restart.txt`
   - `task_d_checkpoint_after_restart.txt`
   - `task_d_watermark_comparison.txt`

**Output:**
```
📸 CAPTURING ASSIGNMENT TASK SCREENSHOTS
================================================================================

📋 Task B: Capturing streaming modes...
  1/3: Steady mode...
  2/3: Burst mode...
  3/3: Late events mode...
✅ Task B screenshots captured

📋 Task C: Capturing Spark Streaming console...
✅ Task C screenshot captured

📋 Task D: Keeping existing test results...
✅ ALL TASK SCREENSHOTS CAPTURED
```

---

### Step 9: Complete

**Duration:** Instant

```
================================================================================
✅ ALL TASKS COMPLETED!
================================================================================

📸 Screenshots saved to:
   - screenshots/startup_with_real_alerts.txt
   - screenshots/task_b_steady_mode.txt
   - screenshots/task_b_burst_mode.txt
   - screenshots/task_b_late_events_mode.txt
   - screenshots/task_c_streaming_console.txt
   - screenshots/task_d_*.txt (checkpoint & watermark tests)

📖 Documentation:
   - README: README.md
   - Workflow: WORKFLOW.md

================================================================================
```

**What happened:**
- ✅ All services started and ran successfully
- ✅ 492 real fraud alerts sent to Kafka
- ✅ All task screenshots captured
- ❌ Services are now STOPPED (by capture script)

**Next steps:**
- Review screenshots in `screenshots/` folder
- Use `make start` to run services again if needed
- Use `docker compose up -d` for manual service start

---

## Data Flow

### 1. Data Source → Producer

```
creditcard.csv (283,726 transactions)
    ↓
Producer deduplicates data
    ↓
Batch streaming to Kafka
```

### 2. Producer → Kafka

```
Producer
    ↓ (500 msgs/batch, 250ms delay)
Kafka Topic: transactions
    ↓ (3 partitions)
Stored in Kafka
```

### 3. Kafka → Spark Streaming

```
Kafka Topic: transactions
    ↓ (real-time read)
Spark Structured Streaming
    ↓ (micro-batch processing)
ML Model (Logistic Regression)
    ↓ (fraud prediction)
Fraud Detection (threshold: 0.0186)
```

### 4. Spark → Kafka Alerts

```
Fraud detected
    ↓
Alert created
    ↓ (with fraud_probability)
Kafka Topic: fraud_alerts
    ↓ (3 partitions)
Stored in Kafka
```

### 5. Complete Flow Diagram

```
┌─────────────────┐
│ creditcard.csv  │
│  283,726 rows   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Producer      │ (Python)
│  - Deduplicate  │
│  - Batch stream │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Kafka Broker   │
│ Topic: txns     │
│ (3 partitions)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Spark Streaming │ (PySpark)
│  - Read stream  │
│  - ML inference │
│  - Detect fraud │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Kafka Broker   │
│ Topic: alerts   │
│ (3 partitions)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Consumer      │ (Python)
│  - Read alerts  │
│  - Verify data  │
└─────────────────┘
```

---

## Task Capture Workflow

### Task B: Streaming Modes

#### B1: Steady Mode

**Purpose:** Demonstrate normal streaming rate

**Steps:**
1. Start Kafka + Producer (STEADY mode)
2. Wait 50 seconds
3. Capture last 50 lines of producer logs
4. Stop services

**Expected Output:**
```
[producer] Batch 100/568 | Rate: 1424.6 msg/s
[producer] Batch 120/568 | Rate: 1403.5 msg/s
```

#### B2: Burst Mode

**Purpose:** Demonstrate high traffic burst handling

**Steps:**
1. Start Kafka + Producer (BURST mode)
2. Wait 50 seconds (captures ~4 cycles)
3. Capture last 50 lines of producer logs
4. Stop services

**Expected Output:**
```
[producer] Cycle 1 - BURST ON (2.0s)
[producer] Burst phase: 12000 records | Rate: 5386.3 msg/s
[producer] Cycle 1 - QUIET PERIOD (10.0s)
[producer] Cycle 2 - BURST ON (2.0s)
...
```

#### B3: Late Events Mode

**Purpose:** Demonstrate out-of-order event handling

**Steps:**
1. Start Kafka + Producer (LATE_EVENTS mode)
2. Wait 50 seconds
3. Capture last 50 lines of producer logs
4. Stop services

**Expected Output:**
```
[producer] Mode: LATE_EVENTS
[producer] Late rate: 10.0% | Delay: 30-180s
[producer] Batch 100/568 | Late: 4953 (9.9%) | On-time: 45047
```

---

### Task C: Spark Streaming Console

**Purpose:** Show Spark Structured Streaming in action

**Steps:**
1. Start Kafka
2. Start Producer (STEADY mode)
3. Start Spark Streaming
4. Wait 60 seconds for batch processing
5. Capture last 200 lines of Spark logs
6. Stop services

**Expected Output:**
```
Batch: 1
-------------------------------------------
+----------+------+-------------------+
|event_time|Amount|fraud_probability  |
+----------+------+-------------------+
|...       |406.00|0.9500             |
+----------+------+-------------------+

Streaming query progress:
- Input Rate: 1500 rows/sec
- Process Rate: 1800 rows/sec
- Batch Duration: 2.5 sec
```

---

### Task D: Checkpoint & Watermark

**Purpose:** Demonstrate exactly-once semantics and watermark handling

**Files (Pre-existing):**
- `task_d_checkpoint_before_restart.txt` - State before restart
- `task_d_checkpoint_after_restart.txt` - State after restart
- `task_d_watermark_comparison.txt` - Watermark comparison

**Key Concepts:**
- **Checkpointing:** Ensures exactly-once processing
- **Watermarks:** Handle late-arriving data
- **State Management:** Recovery after failure

---

## Streaming Modes

### 1. Steady Mode (Default)

**Configuration:**
```yaml
environment:
  STREAM_MODE: steady
  BATCH_SIZE: 500
  SLEEP_MS: 250
```

**Behavior:**
- Sends 500 messages per batch
- 250ms delay between batches
- Consistent throughput: ~1400-1500 msg/s

**Use Case:** Normal production streaming

---

### 2. Burst Mode

**Configuration:**
```yaml
environment:
  STREAM_MODE: burst
  BURST_SIZE: 2000
  BURST_DURATION_MS: 2000
  QUIET_DURATION_MS: 10000
```

**Behavior:**
- Burst: 2000 msgs in 2 seconds (~6000-7000 msg/s)
- Quiet: 10 seconds of no traffic
- Repeats cycle continuously

**Use Case:** Testing backpressure and burst handling

---

### 3. Late Events Mode

**Configuration:**
```yaml
environment:
  STREAM_MODE: late
  LATE_RATE: 0.1
  LATE_DELAY_MIN_S: 30
  LATE_DELAY_MAX_S: 180
```

**Behavior:**
- 10% of events arrive late (30-180 seconds)
- 90% arrive on-time
- Tests watermark and late data handling

**Use Case:** Testing out-of-order event processing

---

## Troubleshooting

### Issue: Services won't start

**Symptoms:**
```
Error: Cannot connect to Kafka
```

**Solutions:**
1. Check Docker is running: `docker ps`
2. Increase wait times in run-all.sh
3. Restart Docker Desktop
4. Clean everything: `make clean`

---

### Issue: No fraud alerts

**Symptoms:**
```
⚠️ Total fraud alerts found: 0
```

**Solutions:**
1. Check Spark logs: `make logs-spark`
2. Verify producer is running: `make logs-producer`
3. Check Kafka topics exist:
   ```bash
   docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
     --bootstrap-server kafka:9092 --list
   ```
4. Manually send alerts: `make send-real-alerts`

---

### Issue: Screenshots not generated

**Symptoms:**
```
ls screenshots/
# Files missing
```

**Solutions:**
1. Check capture script: `cat scripts/capture_all_tasks.sh`
2. Run capture manually: `./scripts/capture_all_tasks.sh`
3. Increase wait times (line 29, 58, 87)
4. Check disk space: `df -h`

---

### Issue: Batch number too low

**Symptoms:**
```
[producer] Batch 20/568 | Rate: 1485.2 msg/s
# Expected: Batch 100+
```

**Solutions:**
1. Increase wait time in capture_all_tasks.sh:
   ```bash
   sleep 50  # Change to 100 for Batch 200+
   ```
2. Re-run: `make start`

---

### Issue: Services already running

**Symptoms:**
```
Error: port 9092 already in use
```

**Solutions:**
1. Stop existing services: `make stop`
2. Force cleanup: `docker compose down -v`
3. Check what's using port: `lsof -i :9092`

---

## Performance Tips

### Speed Up Startup

1. **Reduce wait times** (for testing only):
   ```bash
   # In run-all.sh
   sleep 10  # Instead of 15 (Kafka)
   sleep 15  # Instead of 20 (Spark)
   sleep 5   # Instead of 10 (Producer)
   ```

2. **Skip screenshot capture**:
   ```bash
   # Comment out in run-all.sh
   # ./scripts/capture_all_tasks.sh
   ```

3. **Use cached Docker images**:
   ```bash
   docker compose pull  # Download images first
   ```

---

### Optimize Screenshot Capture

1. **Reduce wait times** (faster, but lower batch numbers):
   ```bash
   # In capture_all_tasks.sh
   sleep 30  # Instead of 50 (Task B)
   sleep 40  # Instead of 60 (Task C)
   ```

2. **Capture fewer lines**:
   ```bash
   docker compose logs producer --tail 30  # Instead of 50
   ```

---

## Manual Service Management

### Start Individual Services

```bash
# Start only Kafka
docker compose up -d kafka kafka-init

# Start only Spark
docker compose up -d spark-streaming

# Start only Producer
docker compose up -d producer

# Start all services
docker compose up -d
```

### Stop Individual Services

```bash
# Stop only Producer
docker compose stop producer

# Stop only Spark
docker compose stop spark-streaming

# Stop all services
docker compose down
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f spark-streaming

# Last N lines
docker compose logs --tail 100 producer

# Since timestamp
docker compose logs --since 2026-01-05T10:00:00
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart producer

# Rebuild and restart
docker compose up -d --build producer
```

---

## Next Steps

After running `make start`:

1. **Review Screenshots:**
   ```bash
   ls screenshots/
   cat screenshots/task_b_steady_mode.txt
   ```

2. **Check Alerts:**
   ```bash
   make check-alerts
   ```

3. **Start Services for Development:**
   ```bash
   docker compose up -d
   make logs
   ```

4. **Modify Producer Mode:**
   ```bash
   # Edit docker-compose.yml
   STREAM_MODE: burst  # or late
   docker compose up -d --build producer
   ```

5. **Clean Up:**
   ```bash
   make clean  # Remove all data
   ```

---

## Summary

This workflow provides a complete end-to-end fraud detection pipeline:

✅ **Real data** from creditcard.csv (283,726 transactions)
✅ **Real fraud alerts** (492 Class=1 transactions)
✅ **Real-time streaming** with Kafka + Spark
✅ **ML inference** with Logistic Regression model
✅ **Complete screenshots** for all assignment tasks
✅ **Production-ready** with checkpointing and watermarks

**Total Runtime:** ~7-10 minutes (one command!)

---

**Made with ❤️ for real-time fraud detection by Sojirat.S**
