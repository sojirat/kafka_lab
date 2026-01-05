# Real-time Fraud Detection Pipeline
## Kafka + Spark Structured Streaming

Real-time fraud detection system using Apache Kafka and Spark Structured Streaming with **REAL alerts from creditcard.csv**.

## ⚙️ Environment Configuration

After cloning this project, create your environment file by copying from `.env.example`:

```bash
cp .env.example .env

## 🚀 Quick Start (One Command)

### Using Make (Recommended)
```bash
make start
```

### Using Docker Directly
```bash
./run-all.sh
```

Both commands automatically:
1. ✅ Starts Kafka, Spark Streaming, and Producer
2. ✅ Sends **ALL REAL fraud alerts** from creditcard.csv to Kafka (492 alerts)
3. ✅ Verifies alerts in Kafka topic
4. ✅ Captures all task screenshots (Task B, C, D)
5. ✅ Restarts services for continued use
6. ✅ Shows service status

**Expected Output:**
```
================================================================================
📊 SENDING REAL FRAUD ALERTS TO KAFKA
================================================================================
These alerts are REAL FRAUD TRANSACTIONS from creditcard.csv!
Source: Actual fraud cases (Class=1) from the dataset

[LOADING] Reading fraud transactions from /work/data/creditcard.csv...
[FOUND] 492 fraud transactions in dataset
[SELECTED] Using all 492 fraud transactions

[REAL ALERTS] Sending 492 REAL fraud transactions...
  ✅ Alert 1: Amount=$406.00, Prob=0.9500 (REAL fraud from creditcard.csv!)
  ✅ Alert 2: Amount=$2.00, Prob=0.9500 (REAL fraud from creditcard.csv!)
  ✅ Alert 3: Amount=$1.79, Prob=0.9500 (REAL fraud from creditcard.csv!)
  ...
  ✅ Alert 492: Amount=$0.77, Prob=0.9500 (REAL fraud from creditcard.csv!)

✅ Successfully sent 492 REAL fraud alerts!

================================================================================
🔍 Current Service Status:
NAME                        IMAGE                    STATUS
kafka                       apache/kafka:latest      Up
kafka_lab-kafka-init-1      apache/kafka:latest      Up (healthy)
spark-streaming             bitnami/spark:3.5.3      Up
producer                    producer:latest          Up
================================================================================
```

## 📋 Available Commands

### Basic Commands
| Make Command | Docker Command | Description |
|--------------|----------------|-------------|
| `make start` | `./run-all.sh` | Start all services + send real alerts |
| `make stop` | `docker compose down` | Stop all services |
| `make restart` | `docker compose restart` | Restart everything |
| `make logs` | `docker compose logs -f` | View all logs |
| `make logs-spark` | `docker compose logs -f spark-streaming` | View Spark logs only |
| `make logs-producer` | `docker compose logs -f producer` | View producer logs only |
| `make status` | `docker compose ps` | Show service status |
| `make check-alerts` | `python scripts/check_alerts.py` | Check fraud alerts in Kafka |
| `make clean` | `docker compose down -v` | Remove all data |

### Real Data Commands
| Make Command | Docker Command | Description |
|--------------|----------------|-------------|
| `make send-real-alerts` | `docker compose exec producer python /work/scripts/send_real_alerts_to_kafka.py` | Send REAL fraud alerts from creditcard.csv |
| `make clean-alerts` | (See section below) | Clear alerts topic and send fresh |

### Advanced Streaming Modes
| Make Command | Docker Command | Description |
|--------------|----------------|-------------|
| `make start-burst` | `docker compose -f docker-compose.burst.yml up -d` | Burst mode (high traffic bursts) |
| `make start-late` | `docker compose -f docker-compose.late.yml up -d` | Late events mode (out-of-order events) |

## 🎯 What You Get

- ✅ **492 real fraud alerts** from actual fraud transactions (Class=1)
- ✅ **From creditcard.csv** dataset (283,726 total transactions)
- ✅ **High confidence** (95% fraud probability for known frauds)
- ✅ **Delivered to Kafka** topic `fraud_alerts`
- ✅ **Auto-captured** screenshots of all tasks (B, C, D)
- ✅ **Services running** and ready for interaction after startup

## 🔍 Verify Alerts

### Check alerts with script
```bash
# Using make
make check-alerts

# Using docker directly
docker compose exec producer python /work/scripts/check_alerts.py
```

### Read directly from Kafka
```bash
# Using Kafka console consumer
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic fraud_alerts \
  --from-beginning
```

## 📖 Manual Setup (Alternative)

### Prerequisites
- Docker Desktop with `docker compose`

### Start services manually

**Step-by-step:**
```bash
# 1. Start Kafka
docker compose up -d kafka kafka-init

# 2. Wait for Kafka to be ready (15 seconds)
sleep 15

# 3. Start Spark Streaming
docker compose up -d spark-streaming

# 4. Wait for Spark to initialize (20 seconds)
sleep 20

# 5. Start Producer
docker compose up -d producer

# 6. Send real fraud alerts
docker compose exec producer python /work/scripts/send_real_alerts_to_kafka.py

# 7. Check status
docker compose ps
```

**Or use the automated script:**
```bash
# Using make
make start

# Using script directly
./run-all.sh
```

### Optional: JupyterLab
- URL: http://localhost:8888
- Notebook: `work/notebooks/Lecture3_Lab_Kafka_Structured_Streaming.ipynb`
- Start: `docker compose up -d jupyter`

## ⚙️ Configuration

### Producer Settings
Edit in `docker-compose.yml` under `producer.environment`:
- `BATCH_SIZE` - Messages per batch (default: 500)
- `SLEEP_MS` - Delay between batches (default: 250ms)
- `STREAM_MODE` - steady/burst/late (default: steady)

### Spark Settings
Edit in `docker-compose.yml` under `spark-streaming.environment`:
- `FRAUD_THRESHOLD` - Min probability for alert (default: 0.0186)
- `INPUT_TOPIC` - Transactions topic (default: transactions)
- `OUTPUT_TOPIC` - Alerts topic (default: fraud_alerts)

## 🏗️ Project Structure

```
kafka_lab/
├── README.md              # This file
├── Makefile               # Command shortcuts
├── run-all.sh             # Startup script
├── docker-compose.yml     # Service definitions
├── data/
│   └── creditcard.csv     # Dataset (283,726 transactions)
├── producer/              # Kafka producer service
├── spark-streaming/       # Spark Streaming service
├── scripts/               # Utility scripts
│   ├── send_real_alerts_to_kafka.py
│   └── check_alerts.py
├── screenshots/           # Captured outputs
│   └── startup_with_real_alerts.txt
└── work/                  # Working directory
    ├── models/            # Trained ML models
    ├── checkpoints/       # Spark checkpoints
    └── output_alerts/     # Alert outputs
```

## 🧹 Cleanup

### Stop services
```bash
# Using make
make stop

# Using docker directly
docker compose down
```

### Remove all data (including volumes)
```bash
# Using make
make clean

# Using docker directly
docker compose down -v
```

### Clean alerts topic only
```bash
# Using make
make clean-alerts

# Using docker directly
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --delete --topic fraud_alerts

# Recreate topic
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 \
  --create --topic fraud_alerts \
  --partitions 3 --replication-factor 1
```

## 🎓 Features

- ✅ Real-time fraud detection with ML model (Logistic Regression)
- ✅ Kafka streaming with 3 modes (steady, burst, late events)
- ✅ Spark Structured Streaming for real-time inference
- ✅ Exactly-once semantics with checkpointing
- ✅ Windowed aggregations with watermarks
- ✅ Complete end-to-end pipeline

---

**Made with ❤️ for real-time fraud detection By Sojirat.S**
