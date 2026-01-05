#!/bin/bash

# Capture all task outputs for screenshots
SCREENSHOT_DIR="screenshots"

echo "================================================================================"
echo "📸 CAPTURING ALL TASK SCREENSHOTS"
echo "================================================================================"
echo ""

# Task B: Streaming Modes
echo "📋 Task B: Capturing streaming modes..."
echo ""

# Task B - Steady Mode
echo "  1/3: Steady mode..."
docker compose down 2>/dev/null
{
    START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "================================================================================"
    echo "TASK B: STEADY MODE (Normal streaming rate)"
    echo "Started: $START_TIME"
    echo "================================================================================"
    echo ""
    docker compose up -d kafka kafka-init
    echo "⏳ Waiting for Kafka to be ready (20 seconds)..."
    sleep 20
    docker compose up -d producer
    echo "⏳ Waiting for producer to stream (50 seconds to reach ~Batch 100)..."
    sleep 50
    echo ""
    echo "================================================================================"
    echo "📊 PRODUCER OUTPUT (Last 50 lines)"
    echo "================================================================================"
    docker compose logs producer --tail 50
    docker compose down
    echo ""
    echo "================================================================================"
    END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "Completed: $END_TIME"
    echo "Started:   $START_TIME"
    echo "================================================================================"
} > "$SCREENSHOT_DIR/task_b_steady_mode.txt" 2>&1

# Task B - Burst Mode
echo "  2/3: Burst mode..."
{
    START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "================================================================================"
    echo "TASK B: BURST MODE (High traffic bursts)"
    echo "Started: $START_TIME"
    echo "================================================================================"
    echo ""
    docker compose -f docker-compose.burst.yml up -d kafka kafka-init
    echo "⏳ Waiting for Kafka to be ready (20 seconds)..."
    sleep 20
    docker compose -f docker-compose.burst.yml up -d producer
    echo "⏳ Waiting for producer to stream (50 seconds to capture multiple cycles)..."
    sleep 50
    echo ""
    echo "================================================================================"
    echo "📊 PRODUCER OUTPUT (Last 50 lines)"
    echo "================================================================================"
    docker compose -f docker-compose.burst.yml logs producer --tail 50
    docker compose -f docker-compose.burst.yml down
    echo ""
    echo "================================================================================"
    END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "Completed: $END_TIME"
    echo "Started:   $START_TIME"
    echo "================================================================================"
} > "$SCREENSHOT_DIR/task_b_burst_mode.txt" 2>&1

# Task B - Late Events Mode
echo "  3/3: Late events mode..."
{
    START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "================================================================================"
    echo "TASK B: LATE EVENTS MODE (Out-of-order events)"
    echo "Started: $START_TIME"
    echo "================================================================================"
    echo ""
    docker compose -f docker-compose.late.yml up -d kafka kafka-init
    echo "⏳ Waiting for Kafka to be ready (20 seconds)..."
    sleep 20
    docker compose -f docker-compose.late.yml up -d producer
    echo "⏳ Waiting for producer to stream (50 seconds to reach ~Batch 100)..."
    sleep 50
    echo ""
    echo "================================================================================"
    echo "📊 PRODUCER OUTPUT (Last 50 lines)"
    echo "================================================================================"
    docker compose -f docker-compose.late.yml logs producer --tail 50
    docker compose -f docker-compose.late.yml down
    echo ""
    echo "================================================================================"
    END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "Completed: $END_TIME"
    echo "Started:   $START_TIME"
    echo "================================================================================"
} > "$SCREENSHOT_DIR/task_b_late_events_mode.txt" 2>&1

echo "✅ Task B screenshots captured"
echo ""

# Task C: Streaming Console
echo "📋 Task C: Capturing Spark Streaming console..."
{
    START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "================================================================================"
    echo "TASK C: SPARK STRUCTURED STREAMING (Fraud Detection)"
    echo "Started: $START_TIME"
    echo "================================================================================"
    echo ""
    docker compose up -d kafka kafka-init
    echo "⏳ Waiting for Kafka to be ready (20 seconds)..."
    sleep 20
    docker compose up -d producer
    echo "⏳ Waiting for producer to start (15 seconds)..."
    sleep 15
    docker compose up -d spark-streaming
    echo "⏳ Waiting for Spark to initialize and process batches (60 seconds)..."
    sleep 60
    echo ""
    echo "================================================================================"
    echo "📊 SPARK STREAMING OUTPUT (Last 200 lines)"
    echo "================================================================================"
    docker compose logs spark-streaming --tail 200
    echo ""
    echo "================================================================================"
    echo "🔍 PRODUCER STATUS"
    echo "================================================================================"
    docker compose logs producer --tail 20
    docker compose down
    echo ""
    echo "================================================================================"
    END_TIME=$(date +"%Y-%m-%d %H:%M:%S")
    echo "Completed: $END_TIME"
    echo "Started:   $START_TIME"
    echo "================================================================================"
} > "$SCREENSHOT_DIR/task_c_streaming_console.txt" 2>&1

echo "✅ Task C screenshot captured"
echo ""

# Task D: Restore existing screenshots message
echo "📋 Task D: Keeping existing test results..."
echo "  (task_d_checkpoint_*.txt and task_d_watermark_comparison.txt exist)"
echo ""

echo "================================================================================"
echo "✅ ALL TASK SCREENSHOTS CAPTURED"
echo "================================================================================"
echo ""
echo "Screenshots saved to: $SCREENSHOT_DIR/"
echo "  - task_b_steady_mode.txt"
echo "  - task_b_burst_mode.txt"
echo "  - task_b_late_events_mode.txt"
echo "  - task_c_streaming_console.txt"
echo "  - task_d_* (manual test scripts if needed)"
echo ""
