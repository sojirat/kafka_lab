.PHONY: help start stop restart logs clean check-alerts build status start-burst start-late monitor test verify test-burst test-late verify-burst verify-late monitor-burst monitor-late send-real-alerts clean-alerts capture-all-tasks

# Default target
help:
	@echo "================================================================================"
	@echo "🚀 Real-time Fraud Detection - Available Commands"
	@echo "================================================================================"
	@echo ""
	@echo "Basic Commands:"
	@echo "  make start          - Start all services (steady stream mode)"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-spark     - View Spark Streaming logs only"
	@echo "  make logs-producer  - View Producer logs only"
	@echo "  make status         - Show status of all services"
	@echo "  make check-alerts   - Check fraud alerts in Kafka"
	@echo "  make build          - Build/rebuild all Docker images"
	@echo "  make clean          - Stop and remove all data (⚠️  destructive)"
	@echo ""
	@echo "Real Data Commands:"
	@echo "  make send-real-alerts - Send REAL fraud alerts from creditcard.csv to Kafka"
	@echo "  make clean-alerts     - Clear fraud_alerts topic and send fresh real alerts"
	@echo "  make capture-all-tasks - Capture ALL task screenshots (B, C, D)"
	@echo ""
	@echo "Advanced Streaming Modes:"
	@echo "  make start-burst    - Start with burst mode (high traffic bursts)"
	@echo "  make start-late     - Start with late events mode (out-of-order events)"
	@echo ""
	@echo "Run the windowed streaming job:"
	@echo "  make start-windows    - Start with fraud detection streaming"
	@echo ""
	@echo "Testing & Monitoring (Steady Mode):"
	@echo "  make test           - Run automated tests (check alerts, batches, stats)"
	@echo "  make verify         - Comprehensive verification of all components"
	@echo "  make monitor        - Live monitoring of fraud detection (auto-refresh)"
	@echo ""
	@echo "Testing & Monitoring (Burst Mode):"
	@echo "  make test-burst     - Run automated tests for burst mode"
	@echo "  make verify-burst   - Comprehensive verification for burst mode"
	@echo "  make monitor-burst  - Live monitoring for burst mode (auto-refresh)"
	@echo ""
	@echo "Testing & Monitoring (Late Events Mode):"
	@echo "  make test-late      - Run automated tests for late events mode"
	@echo "  make verify-late    - Comprehensive verification for late events mode"
	@echo "  make monitor-late   - Live monitoring for late events mode (auto-refresh)"
	@echo ""
	@echo "================================================================================"

# Start all services (with screenshot capture)
start:
	@echo "🚀 Starting all services..."
	@./run-all.sh | tee screenshots/startup_with_real_alerts.txt
	@echo ""
	@echo "📸 Screenshot saved to: screenshots/startup_with_real_alerts.txt"

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	@docker compose down
	@echo "✅ All services stopped"

# Restart all services
restart: stop start

# View logs from all services
logs:
	@docker compose logs -f

# View Spark Streaming logs
logs-spark:
	@docker compose logs -f spark-streaming

# View Producer logs
logs-producer:
	@docker compose logs -f producer

# Show service status
status:
	@echo "📊 Service Status:"
	@echo ""
	@docker compose ps
	@echo ""
	@echo "💾 Kafka Topics:"
	@docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
		--bootstrap-server kafka:9092 --list 2>/dev/null || echo "Kafka not running"

# Check fraud alerts
check-alerts:
	@echo "🔍 Checking fraud alerts..."
	@echo ""
	@docker compose exec -T producer python /work/scripts/check_alerts.py

# Send real fraud alerts from creditcard.csv (starts services & cleans first)
send-real-alerts:
	@echo "🚀 Starting services..."
	@docker compose up -d kafka
	@echo "⏳ Waiting for Kafka to be ready..."
	@sleep 10
	@echo ""
	@echo "🧹 Cleaning fraud_alerts topic..."
	@docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic fraud_alerts 2>/dev/null || true
	@sleep 2
	@docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic fraud_alerts --partitions 3 --replication-factor 1 2>/dev/null || true
	@echo ""
	@echo "📊 Sending REAL fraud alerts from creditcard.csv..."
	@docker compose up -d producer
	@sleep 5
	@docker compose exec producer python /work/scripts/send_real_alerts_to_kafka.py
	@echo ""
	@echo "🔍 Verifying alerts..."
	@docker compose exec -T producer python /work/scripts/check_alerts.py

# Clean alerts topic and send fresh real alerts
clean-alerts:
	@echo "🧹 Cleaning fraud_alerts topic..."
	@docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic fraud_alerts 2>/dev/null || true
	@sleep 2
	@docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic fraud_alerts --partitions 3 --replication-factor 1 2>/dev/null || true
	@echo ""
	@echo "📊 Sending fresh REAL fraud alerts..."
	@docker compose up -d producer
	@sleep 5
	@docker compose exec producer python /work/scripts/send_real_alerts_to_kafka.py
	@echo ""
	@echo "🔍 Verifying alerts..."
	@docker compose exec -T producer python /work/scripts/check_alerts.py

# Capture all task screenshots
capture-all-tasks:
	@echo "📸 Capturing all task screenshots..."
	@./scripts/capture_all_tasks.sh

build:
	@echo "🔨 Building Docker images..."
	@docker compose build
	@echo "✅ Build complete"

# Clean everything (including data)
clean:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		echo "✅ All services and data removed"; \
	else \
		echo "❌ Cancelled"; \
	fi

# Start with burst mode (high traffic bursts)
start-burst:
	@echo "🚀 Starting services in BURST MODE..."
	@echo "📊 Mode: Periodic high-throughput bursts"
	@echo "   - Burst duration: 2 seconds"
	@echo "   - Quiet period: 10 seconds"
	@echo "   - Burst size: 2000 messages"
	@echo ""
	@docker compose -f docker-compose.burst.yml down 2>/dev/null || true
	@docker compose -f docker-compose.burst.yml up -d kafka kafka-init
	@echo "⏳ Waiting for Kafka (15 seconds)..."
	@sleep 15
	@docker compose -f docker-compose.burst.yml up -d spark-streaming
	@echo "⏳ Waiting for Spark (20 seconds)..."
	@sleep 20
	@docker compose -f docker-compose.burst.yml up -d producer
	@echo ""
	@echo "✅ Burst mode started!"
	@echo "💡 Use 'docker compose -f docker-compose.burst.yml logs -f' to view logs"

# Start with late events mode (out-of-order events)
start-late:
	@echo "🚀 Starting services in LATE EVENTS MODE..."
	@echo "📊 Mode: Out-of-order event injection"
	@echo "   - Late event rate: 10%"
	@echo "   - Delay range: 30-180 seconds"
	@echo ""
	@docker compose -f docker-compose.late.yml down 2>/dev/null || true
	@docker compose -f docker-compose.late.yml up -d kafka kafka-init
	@echo "⏳ Waiting for Kafka (15 seconds)..."
	@sleep 15
	@docker compose -f docker-compose.late.yml up -d spark-streaming
	@echo "⏳ Waiting for Spark (20 seconds)..."
	@sleep 20
	@docker compose -f docker-compose.late.yml up -d producer
	@echo ""
	@echo "✅ Late events mode started!"
	@echo "💡 Use 'docker compose -f docker-compose.late.yml logs -f' to view logs"

# Start with fraud detection streaming
start-windows:
	@echo "🚀 Starting services in fraud detection streaming..."
	@echo ""
	@docker compose up -d spark-streaming
	@echo ""
	@echo "✅ Fraud detection streaming started!"
	@echo "💡 Use 'docker compose logs -f' to view logs"

# Automated testing - check all components
test:
	@echo "================================================================================"
	@echo "🧪 AUTOMATED TESTING - Fraud Detection System"
	@echo "================================================================================"
	@echo ""
	@echo "📊 1. Checking Service Status..."
	@echo "----------------------------------------"
	@docker compose ps
	@echo ""
	@echo "📊 2. Checking Spark Batch Processing..."
	@echo "----------------------------------------"
	@docker compose logs spark-streaming 2>&1 | grep "Batch:" | tail -10 || echo "❌ No batches found yet"
	@echo ""
	@echo "📊 3. Checking for Fraud Alerts..."
	@echo "----------------------------------------"
	@docker compose logs spark-streaming --tail 500 2>&1 | grep -B3 -A10 "fraud_probability" | head -50 || echo "⚠️  No fraud alerts in recent logs"
	@echo ""
	@echo "📊 4. Producer Statistics..."
	@echo "----------------------------------------"
	@docker compose logs producer 2>&1 | grep "Batch [0-9]" | tail -5 || echo "❌ Producer not sending data"
	@echo ""
	@echo "📊 5. Kafka Alert Count..."
	@echo "----------------------------------------"
	@docker compose exec -T kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
		--broker-list kafka:9092 --topic fraud_alerts --time -1 2>/dev/null | \
		awk -F: '{sum+=$$3} END {print "Total fraud alerts in Kafka: " sum}' || echo "❌ Cannot connect to Kafka"
	@echo ""
	@echo "================================================================================"
	@echo "✅ Testing Complete!"
	@echo "================================================================================"

# Comprehensive verification
verify:
	@echo "================================================================================"
	@echo "🔍 COMPREHENSIVE SYSTEM VERIFICATION"
	@echo "================================================================================"
	@echo ""
	@echo "1️⃣  Verifying Kafka..."
	@docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list 2>/dev/null && echo "   ✅ Kafka is running" || echo "   ❌ Kafka is down"
	@echo ""
	@echo "2️⃣  Verifying Producer..."
	@docker compose logs producer --tail 20 2>&1 | grep -q "Connected to Kafka" && echo "   ✅ Producer connected" || echo "   ⚠️  Producer may not be connected"
	@echo ""
	@echo "3️⃣  Verifying Spark Streaming..."
	@docker compose logs spark-streaming --tail 50 2>&1 | grep -q "STREAMING STARTED" && echo "   ✅ Spark Streaming running" || echo "   ❌ Spark not started"
	@echo ""
	@echo "4️⃣  Checking Data Flow..."
	@BATCH_COUNT=$$(docker compose logs spark-streaming 2>&1 | grep -c "Batch:"); \
	if [ $$BATCH_COUNT -gt 0 ]; then \
		echo "   ✅ Data flowing: $$BATCH_COUNT batches processed"; \
	else \
		echo "   ❌ No data flow detected"; \
	fi
	@echo ""
	@echo "5️⃣  Checking Model..."
	@docker compose logs spark-streaming 2>&1 | grep -q "Model loaded" && echo "   ✅ ML Model loaded" || echo "   ❌ Model not loaded"
	@echo ""
	@echo "6️⃣  Checking Output Files..."
	@if [ -d "work/output_alerts" ] && [ "$$(ls -A work/output_alerts 2>/dev/null)" ]; then \
		echo "   ✅ Output files exist"; \
		ls -lh work/output_alerts | head -5; \
	else \
		echo "   ⚠️  No output files yet (may need more time)"; \
	fi
	@echo ""
	@echo "================================================================================"
	@echo "📋 SUMMARY"
	@echo "================================================================================"
	@echo "Run 'make test' for detailed fraud alert statistics"
	@echo "Run 'make monitor' for live monitoring"
	@echo "================================================================================"

# Live monitoring with auto-refresh
monitor:
	@echo "================================================================================"
	@echo "📺 LIVE MONITORING - Fraud Detection System"
	@echo "================================================================================"
	@echo "Monitoring fraud alerts in real-time... (Press Ctrl+C to stop)"
	@echo ""
	@while true; do \
		clear; \
		echo "==============================================================================="; \
		echo "🚨 FRAUD DETECTION MONITOR - $$(date)"; \
		echo "==============================================================================="; \
		echo ""; \
		echo "📊 Service Status:"; \
		docker compose ps | grep -E "(producer|spark-streaming)" || true; \
		echo ""; \
		echo "📈 Recent Batches:"; \
		docker compose logs spark-streaming 2>&1 | grep "Batch:" | tail -5 || echo "No batches yet"; \
		echo ""; \
		echo "🚨 Recent Fraud Alerts:"; \
		docker compose logs spark-streaming --tail 100 2>&1 | grep -A5 "fraud_probability" | tail -20 || echo "No fraud alerts yet"; \
		echo ""; \
		echo "📊 Producer Progress:"; \
		docker compose logs producer 2>&1 | grep "Batch [0-9]" | tail -3 || echo "Producer not active"; \
		echo ""; \
		echo "==============================================================================="; \
		echo "Refreshing in 10 seconds... (Ctrl+C to stop)"; \
		sleep 10; \
	done

# ============================================================================
# BURST MODE - Testing & Monitoring Commands
# ============================================================================

# Automated testing - burst mode
test-burst:
	@echo "================================================================================"
	@echo "🧪 AUTOMATED TESTING - Fraud Detection System (BURST MODE)"
	@echo "================================================================================"
	@echo ""
	@echo "📊 1. Checking Service Status..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.burst.yml ps
	@echo ""
	@echo "📊 2. Checking Spark Batch Processing..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.burst.yml logs spark-streaming 2>&1 | grep "Batch:" | tail -10 || echo "❌ No batches found yet"
	@echo ""
	@echo "📊 3. Checking for Fraud Alerts..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.burst.yml logs spark-streaming --tail 500 2>&1 | grep -B3 -A10 "fraud_probability" | head -50 || echo "⚠️  No fraud alerts in recent logs"
	@echo ""
	@echo "📊 4. Producer Statistics (Burst Pattern)..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.burst.yml logs producer 2>&1 | grep "Batch [0-9]" | tail -5 || echo "❌ Producer not sending data"
	@echo ""
	@echo "📊 5. Kafka Alert Count..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.burst.yml exec -T kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
		--broker-list kafka:9092 --topic fraud_alerts --time -1 2>/dev/null | \
		awk -F: '{sum+=$$3} END {print "Total fraud alerts in Kafka: " sum}' || echo "❌ Cannot connect to Kafka"
	@echo ""
	@echo "================================================================================"
	@echo "✅ Burst Mode Testing Complete!"
	@echo "================================================================================"

# Comprehensive verification - burst mode
verify-burst:
	@echo "================================================================================"
	@echo "🔍 COMPREHENSIVE SYSTEM VERIFICATION (BURST MODE)"
	@echo "================================================================================"
	@echo ""
	@echo "1️⃣  Verifying Kafka..."
	@docker compose -f docker-compose.burst.yml exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list 2>/dev/null && echo "   ✅ Kafka is running" || echo "   ❌ Kafka is down"
	@echo ""
	@echo "2️⃣  Verifying Producer (Burst Pattern)..."
	@docker compose -f docker-compose.burst.yml logs producer --tail 20 2>&1 | grep -q "Connected to Kafka" && echo "   ✅ Producer connected" || echo "   ⚠️  Producer may not be connected"
	@echo ""
	@echo "3️⃣  Verifying Spark Streaming..."
	@docker compose -f docker-compose.burst.yml logs spark-streaming --tail 50 2>&1 | grep -q "STREAMING STARTED" && echo "   ✅ Spark Streaming running" || echo "   ❌ Spark not started"
	@echo ""
	@echo "4️⃣  Checking Data Flow..."
	@BATCH_COUNT=$$(docker compose -f docker-compose.burst.yml logs spark-streaming 2>&1 | grep -c "Batch:"); \
	if [ $$BATCH_COUNT -gt 0 ]; then \
		echo "   ✅ Data flowing: $$BATCH_COUNT batches processed"; \
	else \
		echo "   ❌ No data flow detected"; \
	fi
	@echo ""
	@echo "5️⃣  Checking Model..."
	@docker compose -f docker-compose.burst.yml logs spark-streaming 2>&1 | grep -q "Model loaded" && echo "   ✅ ML Model loaded" || echo "   ❌ Model not loaded"
	@echo ""
	@echo "6️⃣  Checking Output Files..."
	@if [ -d "work/output_alerts" ] && [ "$$(ls -A work/output_alerts 2>/dev/null)" ]; then \
		echo "   ✅ Output files exist"; \
		ls -lh work/output_alerts | head -5; \
	else \
		echo "   ⚠️  No output files yet (may need more time)"; \
	fi
	@echo ""
	@echo "================================================================================"
	@echo "📋 SUMMARY"
	@echo "================================================================================"
	@echo "Run 'make test-burst' for detailed fraud alert statistics"
	@echo "Run 'make monitor-burst' for live monitoring"
	@echo "================================================================================"

# Live monitoring - burst mode
monitor-burst:
	@echo "================================================================================"
	@echo "📺 LIVE MONITORING - Fraud Detection System (BURST MODE)"
	@echo "================================================================================"
	@echo "Monitoring fraud alerts in real-time... (Press Ctrl+C to stop)"
	@echo ""
	@while true; do \
		clear; \
		echo "==============================================================================="; \
		echo "🚨 FRAUD DETECTION MONITOR (BURST MODE) - $$(date)"; \
		echo "==============================================================================="; \
		echo ""; \
		echo "📊 Service Status:"; \
		docker compose -f docker-compose.burst.yml ps | grep -E "(producer|spark-streaming)" || true; \
		echo ""; \
		echo "📈 Recent Batches:"; \
		docker compose -f docker-compose.burst.yml logs spark-streaming 2>&1 | grep "Batch:" | tail -5 || echo "No batches yet"; \
		echo ""; \
		echo "🚨 Recent Fraud Alerts:"; \
		docker compose -f docker-compose.burst.yml logs spark-streaming --tail 100 2>&1 | grep -A5 "fraud_probability" | tail -20 || echo "No fraud alerts yet"; \
		echo ""; \
		echo "📊 Producer Progress (Burst Pattern):"; \
		docker compose -f docker-compose.burst.yml logs producer 2>&1 | grep "Batch [0-9]" | tail -3 || echo "Producer not active"; \
		echo ""; \
		echo "==============================================================================="; \
		echo "Refreshing in 10 seconds... (Ctrl+C to stop)"; \
		sleep 10; \
	done

# ============================================================================
# LATE EVENTS MODE - Testing & Monitoring Commands
# ============================================================================

# Automated testing - late events mode
test-late:
	@echo "================================================================================"
	@echo "🧪 AUTOMATED TESTING - Fraud Detection System (LATE EVENTS MODE)"
	@echo "================================================================================"
	@echo ""
	@echo "📊 1. Checking Service Status..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.late.yml ps
	@echo ""
	@echo "📊 2. Checking Spark Batch Processing..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.late.yml logs spark-streaming 2>&1 | grep "Batch:" | tail -10 || echo "❌ No batches found yet"
	@echo ""
	@echo "📊 3. Checking for Fraud Alerts..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.late.yml logs spark-streaming --tail 500 2>&1 | grep -B3 -A10 "fraud_probability" | head -50 || echo "⚠️  No fraud alerts in recent logs"
	@echo ""
	@echo "📊 4. Producer Statistics (Late Events Pattern)..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.late.yml logs producer 2>&1 | grep "Batch [0-9]" | tail -5 || echo "❌ Producer not sending data"
	@docker compose -f docker-compose.late.yml logs producer 2>&1 | grep "LATE EVENT" | tail -5 || echo "No late events detected yet"
	@echo ""
	@echo "📊 5. Kafka Alert Count..."
	@echo "----------------------------------------"
	@docker compose -f docker-compose.late.yml exec -T kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
		--broker-list kafka:9092 --topic fraud_alerts --time -1 2>/dev/null | \
		awk -F: '{sum+=$$3} END {print "Total fraud alerts in Kafka: " sum}' || echo "❌ Cannot connect to Kafka"
	@echo ""
	@echo "================================================================================"
	@echo "✅ Late Events Mode Testing Complete!"
	@echo "================================================================================"

# Comprehensive verification - late events mode
verify-late:
	@echo "================================================================================"
	@echo "🔍 COMPREHENSIVE SYSTEM VERIFICATION (LATE EVENTS MODE)"
	@echo "================================================================================"
	@echo ""
	@echo "1️⃣  Verifying Kafka..."
	@docker compose -f docker-compose.late.yml exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list 2>/dev/null && echo "   ✅ Kafka is running" || echo "   ❌ Kafka is down"
	@echo ""
	@echo "2️⃣  Verifying Producer (Late Events Pattern)..."
	@docker compose -f docker-compose.late.yml logs producer --tail 20 2>&1 | grep -q "Connected to Kafka" && echo "   ✅ Producer connected" || echo "   ⚠️  Producer may not be connected"
	@echo ""
	@echo "3️⃣  Verifying Spark Streaming..."
	@docker compose -f docker-compose.late.yml logs spark-streaming --tail 50 2>&1 | grep -q "STREAMING STARTED" && echo "   ✅ Spark Streaming running" || echo "   ❌ Spark not started"
	@echo ""
	@echo "4️⃣  Checking Data Flow..."
	@BATCH_COUNT=$$(docker compose -f docker-compose.late.yml logs spark-streaming 2>&1 | grep -c "Batch:"); \
	if [ $$BATCH_COUNT -gt 0 ]; then \
		echo "   ✅ Data flowing: $$BATCH_COUNT batches processed"; \
	else \
		echo "   ❌ No data flow detected"; \
	fi
	@echo ""
	@echo "5️⃣  Checking Model..."
	@docker compose -f docker-compose.late.yml logs spark-streaming 2>&1 | grep -q "Model loaded" && echo "   ✅ ML Model loaded" || echo "   ❌ Model not loaded"
	@echo ""
	@echo "6️⃣  Checking Output Files..."
	@if [ -d "work/output_alerts" ] && [ "$$(ls -A work/output_alerts 2>/dev/null)" ]; then \
		echo "   ✅ Output files exist"; \
		ls -lh work/output_alerts | head -5; \
	else \
		echo "   ⚠️  No output files yet (may need more time)"; \
	fi
	@echo ""
	@echo "================================================================================"
	@echo "📋 SUMMARY"
	@echo "================================================================================"
	@echo "Run 'make test-late' for detailed fraud alert statistics"
	@echo "Run 'make monitor-late' for live monitoring"
	@echo "================================================================================"

# Live monitoring - late events mode
monitor-late:
	@echo "================================================================================"
	@echo "📺 LIVE MONITORING - Fraud Detection System (LATE EVENTS MODE)"
	@echo "================================================================================"
	@echo "Monitoring fraud alerts in real-time... (Press Ctrl+C to stop)"
	@echo ""
	@while true; do \
		clear; \
		echo "==============================================================================="; \
		echo "🚨 FRAUD DETECTION MONITOR (LATE EVENTS MODE) - $$(date)"; \
		echo "==============================================================================="; \
		echo ""; \
		echo "📊 Service Status:"; \
		docker compose -f docker-compose.late.yml ps | grep -E "(producer|spark-streaming)" || true; \
		echo ""; \
		echo "📈 Recent Batches:"; \
		docker compose -f docker-compose.late.yml logs spark-streaming 2>&1 | grep "Batch:" | tail -5 || echo "No batches yet"; \
		echo ""; \
		echo "🚨 Recent Fraud Alerts:"; \
		docker compose -f docker-compose.late.yml logs spark-streaming --tail 100 2>&1 | grep -A5 "fraud_probability" | tail -20 || echo "No fraud alerts yet"; \
		echo ""; \
		echo "📊 Producer Progress (Late Events Pattern):"; \
		docker compose -f docker-compose.late.yml logs producer 2>&1 | grep "Batch [0-9]" | tail -3 || echo "Producer not active"; \
		echo ""; \
		echo "⏰ Recent Late Events:"; \
		docker compose -f docker-compose.late.yml logs producer 2>&1 | grep "LATE EVENT" | tail -3 || echo "No late events yet"; \
		echo ""; \
		echo "==============================================================================="; \
		echo "Refreshing in 10 seconds... (Ctrl+C to stop)"; \
		sleep 10; \
	done
