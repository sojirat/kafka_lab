# Real-time Fraud Detection System
## Executive Report

---

**Project:** Real-time Fraud Detection Pipeline using Kafka + Spark Streaming
**Prepared by:** Sojirat.S
**Student ID:** s6707021857112
**Date:** January 5, 2026
**Status:** ⚠️ Pre-Production (Not Ready for Go-Live)

---

## Executive Summary

This report presents a comprehensive evaluation of our real-time fraud detection system built on Apache Kafka and Spark Structured Streaming. The system successfully processes **283,726 credit card transactions** and detects **492 actual fraud cases** with **93% recall rate**, demonstrating strong technical capabilities.

However, **critical security and compliance gaps** prevent immediate production deployment. The system requires 6-8 weeks of additional work to address authentication, encryption, scalability, and regulatory compliance before go-live.

**Key Findings:**
- ✅ **Strong Detection:** 93% fraud recall (456/492 frauds caught)
- ⚠️ **Precision Gap:** 82% precision (100 false positives) - below 85% target
- ❌ **Security Issues:** No authentication or encryption enabled
- ❌ **Scalability:** Current 1.5K msg/s vs required 10K msg/s
- ❌ **Compliance:** PCI-DSS and GDPR gaps identified

**Recommendation:** **DO NOT DEPLOY** until critical blockers resolved (Est. 6-8 weeks)

---

## 1. System Overview

### Architecture

Our fraud detection pipeline consists of four core components:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Producer   │────▶│    Kafka     │────▶│    Spark     │
│ creditcard   │     │   Broker     │     │  Streaming   │
│   .csv       │     │ 3 partitions │     │  ML Model    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                           ┌──────────────┐
                                           │    Kafka     │
                                           │fraud_alerts  │
                                           └──────────────┘
```

**Components:**
1. **Producer:** Streams 283,726 transactions from creditcard.csv
2. **Kafka:** Distributed message broker (3 partitions, 1 replication)
3. **Spark Streaming:** Real-time ML inference (Logistic Regression model)
4. **Alert Topic:** Outputs fraud alerts for downstream processing

### Dataset

- **Source:** Creditcard.csv (Kaggle dataset)
- **Total Transactions:** 283,726
- **Fraud Cases:** 492 (0.17% fraud rate)
- **Legitimate Cases:** 283,234 (99.83%)
- **Time Period:** 2 days of European cardholder transactions

### Streaming Modes

The system supports three operational modes:

| Mode | Throughput | Use Case |
|------|------------|----------|
| **Steady** | 1,500 msg/s | Normal production load |
| **Burst** | 6,000-7,000 msg/s | Peak traffic (Black Friday) |
| **Late Events** | 1,500 msg/s + 10% late | Out-of-order event handling |

---

## 2. Model Performance Analysis

### Current Metrics

Based on testing with 283,726 transactions:

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Precision** | 82% | ≥85% | ❌ Below target |
| **Recall** | 93% | ≥90% | ✅ Meets target |
| **F1 Score** | 0.87 | ≥0.87 | ✅ Meets target |
| **AUC-ROC** | 0.96 | ≥0.95 | ✅ Exceeds target |
| **False Positive Rate** | 0.035% | ≤2% | ✅ Well below limit |

### Confusion Matrix

```
                    Predicted Fraud    Predicted Legitimate    Total
Actual Fraud              456                 36               492
Actual Legitimate         100              283,134          283,234
Total                     556              283,170          283,726
```

**Analysis:**
- **True Positives (456):** Successfully caught frauds - Good!
- **False Positives (100):** Legitimate transactions flagged - Issue
- **False Negatives (36):** Missed frauds - Acceptable but improvable
- **True Negatives (283,134):** Correctly approved - Excellent

### Business Impact

**Financial Impact per 283,726 Transactions:**

```
False Positives Cost:
- Count: 100 legitimate transactions blocked
- Avg transaction: $50
- Customer recovery rate: 70%
- Lost revenue: 100 × $50 × 30% = $1,500

False Negatives Cost:
- Count: 36 frauds missed
- Avg fraud amount: $200
- Chargeback rate: 100%
- Direct loss: 36 × $200 = $7,200

Total Cost: $8,700 ($0.03 per transaction)
```

**Annual Projection (50M transactions/year):**
```
Expected Annual Cost:
- False Positive Loss: $265,000
- False Negative Loss: $1,270,000
- Total Annual Cost: $1,535,000

Expected Annual Savings:
- Total Fraud Prevented: $9,128,000 (456 frauds × $200 avg)
- Net Benefit: $9,128,000 - $1,535,000 = $7,593,000
```

**ROI: 5.0x** (For every $1 spent, save $5 in fraud)

---

## 3. Critical Risks & Mitigation

We identified **6 critical operational risks** that must be addressed:

### Risk 1: False Positive Cost ⚠️

**Impact:** Customer friction, lost revenue, increased support costs

**Current State:**
- 100 false positives per 283,726 transactions (0.035%)
- Estimated $265K annual customer impact
- No feedback loop for continuous improvement

**Mitigation Plan:**
1. **Multi-tier Alert System:**
   - High risk (>80%): Auto-block
   - Medium risk (30-80%): Delay 30s for review
   - Low risk (2-30%): Monitor only

2. **Feedback Loop:**
   - Collect customer disputes
   - Retrain model monthly with new labels
   - A/B test threshold adjustments

3. **Business Rules:**
   - Whitelist trusted customers (account age >1 year, fraud rate <0.1%)
   - Allow higher threshold for low-risk merchants

**Timeline:** 2 weeks

---

### Risk 2: Fraud Miss (False Negatives) ⚠️

**Impact:** Direct financial losses, regulatory penalties

**Current State:**
- 36 frauds missed (7.3% miss rate)
- Estimated $1.27M annual direct loss
- Static threshold (0.0186) - no adaptation

**Mitigation Plan:**
1. **Ensemble Model:**
   - Combine Logistic Regression + Random Forest + Neural Network
   - Weighted voting system
   - Expected improvement: 5-10% recall increase

2. **Anomaly Detection Layer:**
   - Velocity checks (multiple txns in <5 min)
   - Geolocation (impossible travel time)
   - Device fingerprint changes

3. **Adaptive Threshold:**
   - Dynamic adjustment by context (time, merchant, amount)
   - Night transactions: Lower threshold (more sensitive)
   - High-risk merchants: Lower threshold

**Timeline:** 4 weeks

---

### Risk 3: Data Drift & Concept Drift 🚨

**Impact:** Silent model degradation, increasing fraud miss rate

**Current State:**
- Model trained on 2013 data (13 years old!)
- No drift detection implemented
- No automated retraining pipeline

**Mitigation Plan:**
1. **Statistical Drift Detection:**
   - Daily Kolmogorov-Smirnov tests on feature distributions
   - Alert if p-value < 0.05
   - Track drift metrics in dashboard

2. **Model Performance Monitoring:**
   - Track precision, recall, F1 daily
   - Trigger retraining if F1 drops >10%
   - Automated email alerts

3. **Automated Retraining:**
   - Weekly retraining with last 90 days data
   - A/B test new model vs production (5% traffic)
   - Deploy if new_model.f1 > old_model.f1 + 0.02

**Timeline:** 3 weeks

---

### Risk 4: Security & Access Control 🚨 CRITICAL

**Impact:** Data breaches, regulatory fines, model theft

**Current State:**
- ❌ No authentication on Kafka broker
- ❌ No encryption (data in transit or at rest)
- ❌ Model file stored unencrypted
- ❌ No audit logging
- ❌ JupyterLab exposed without password

**Mitigation Plan:**
1. **Kafka Security:**
   - Enable SASL/SSL authentication
   - Configure topic ACLs (producer: write, spark: read/write)
   - TLS 1.3 encryption for all connections

2. **Model Security:**
   - Encrypt model files at rest (AES-256)
   - Role-based access control (data scientist: read, ML engineer: write)
   - Audit logging (who accessed model, when, what action)

3. **API Security:**
   - JWT authentication for prediction API
   - Rate limiting (1000 requests/min per user)
   - Input validation (prevent adversarial attacks)

**Timeline:** 4 weeks ⚠️ **BLOCKER**

---

### Risk 5: Late-Arriving Events ⚠️

**Impact:** Missed fraud detection windows, incorrect aggregates

**Current State:**
- 10% events arrive 30-180s late
- Watermark: 2 minutes (some events dropped)
- No late event recovery

**Mitigation Plan:**
1. **Increase Watermark:**
   - Change from 2 min to 5 min
   - Accept minor latency increase for better accuracy

2. **Dual-Path Processing:**
   - Real-time path: Low latency (30s)
   - Batch reconciliation: High accuracy (5 min)
   - Merge results to eliminate gaps

3. **Idempotent Processing:**
   - Deduplication by (transaction_id, event_time)
   - RocksDB state store for fault tolerance

**Timeline:** 2 weeks

---

### Risk 6: System Availability 🚨 CRITICAL

**Impact:** Complete system outage, no fraud detection

**Current State:**
- Single Kafka broker (no replication)
- Single Spark executor
- No health checks or auto-recovery
- Manual restart on failures

**Mitigation Plan:**
1. **High Availability:**
   - Kafka cluster: 3 brokers, replication factor = 3
   - Spark cluster: 1 master + 3 workers
   - Load balancer with failover

2. **Health Checks:**
   - Docker health checks every 30s
   - Kubernetes liveness/readiness probes
   - Automatic container restart on failure

3. **Disaster Recovery:**
   - RTO (Recovery Time Objective): 15 minutes
   - RPO (Recovery Point Objective): 5 minutes
   - Daily backups to cloud storage
   - Documented failover procedure

**Timeline:** 3 weeks ⚠️ **BLOCKER**

---

## 4. Go-Live Criteria

The system must meet **ALL** criteria below before production deployment:

### ✅ Criterion 1: Model Performance

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Precision | 82% | ≥85% | ❌ |
| Recall | 93% | ≥90% | ✅ |
| F1 Score | 0.87 | ≥0.87 | ✅ |
| AUC-ROC | 0.96 | ≥0.95 | ✅ |

**Gap:** Precision needs +3% improvement
**Action:** Feature engineering + ensemble model
**Timeline:** 2 weeks

---

### ❌ Criterion 2: System Performance

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Sustained Throughput | 1.5K msg/s | ≥10K msg/s | ❌ |
| Peak Throughput | 7K msg/s | ≥50K msg/s | ❌ |
| P95 Latency | 350ms | ≤500ms | ✅ |
| P99 Latency | Not measured | ≤1000ms | ❌ |

**Gap:** Throughput needs 7-50x increase
**Action:** Horizontal scaling (10 Kafka partitions, 5 Spark workers)
**Timeline:** 3 weeks

---

### ❌ Criterion 3: Security & Compliance

| Control | Status |
|---------|--------|
| Authentication | ❌ Not enabled |
| Encryption | ❌ Not enabled |
| Audit Logging | ❌ Not enabled |
| PCI-DSS Compliance | ❌ Not reviewed |
| GDPR Compliance | ❌ Not reviewed |
| Penetration Testing | ❌ Not conducted |

**Gap:** 0/6 security controls implemented
**Action:** Complete security hardening + compliance review
**Timeline:** 4-6 weeks ⚠️ **BLOCKER**

---

### ❌ Criterion 4: Operational Readiness

| Item | Status |
|------|--------|
| Monitoring Dashboard | ✅ Exists |
| Alerting Rules | ⚠️ Basic only |
| Runbook | ✅ Documented |
| On-call Rotation | ❌ Not established |
| SLA Definition | ❌ Not defined |
| Incident Response Plan | ⚠️ Partial |

**Gap:** On-call rotation, SLA, alerting
**Action:** Complete operational setup
**Timeline:** 2 weeks

---

### ⚠️ Criterion 5: Business Validation

| Item | Status |
|------|--------|
| ROI Analysis | ✅ $7.6M net benefit |
| Stakeholder Sign-off | ⚠️ Pending security |
| User Acceptance Testing | ❌ Not started |
| Shadow Mode | ❌ Not tested |

**Gap:** UAT and shadow mode testing
**Action:** 2-week parallel run with old system
**Timeline:** 2 weeks (after security fixed)

---

## 5. Deployment Roadmap

### Phase 0: Pre-Production (Current) — 6-8 Weeks

**Week 1-4: Security Hardening** 🚨 **CRITICAL**
```
✓ Enable Kafka SASL/SSL authentication
✓ Implement TLS 1.3 encryption
✓ Encrypt model files (AES-256)
✓ Configure audit logging
✓ Set up secrets management (Vault)
✓ Network segmentation (VPC)
✓ Vulnerability scanning (weekly)
```

**Week 3-5: Compliance Review** 🚨 **CRITICAL**
```
✓ PCI-DSS compliance audit
✓ GDPR data retention policy
✓ Privacy impact assessment
✓ Data processing agreements
✓ Penetration testing
```

**Week 2-4: Scalability** ⚠️ **HIGH PRIORITY**
```
✓ Horizontal scaling (10 partitions, 5 workers)
✓ Load testing (2x peak traffic)
✓ Chaos engineering tests
✓ Auto-scaling configuration
```

**Week 3-5: Model Improvement** ⚠️ **HIGH PRIORITY**
```
✓ Feature engineering for precision
✓ Ensemble model development
✓ Anomaly detection layer
✓ A/B testing framework
```

**Week 5-6: Operational Readiness**
```
✓ Complete monitoring setup (Grafana)
✓ Configure alerting (PagerDuty)
✓ Establish on-call rotation
✓ Define SLAs (99.9% uptime)
✓ Document incident response
```

**Week 6-8: User Acceptance Testing**
```
✓ Train business users
✓ 2-week shadow mode (parallel with old system)
✓ Stakeholder sign-off
✓ Go/No-Go decision
```

---

### Phase 1: Canary Deployment — Week 9-10

```
Traffic: 5% production
Duration: 2 weeks
Monitoring: Hourly reviews

Success Metrics:
✓ Zero production incidents
✓ Precision ≥ 85%
✓ Latency P95 ≤ 500ms
✓ Uptime ≥ 99.9%

Go/No-Go Decision: End of Week 10
```

---

### Phase 2: Gradual Rollout — Week 11-14

```
Week 11: 10% traffic
Week 12: 25% traffic
Week 13: 50% traffic
Week 14: 100% traffic

Rollback Plan:
- Automated rollback if error rate > 1%
- Manual rollback if FP rate > 3%
- Runbook: 5-minute rollback procedure
```

---

### Phase 3: Full Production — Week 15+

```
✓ Decommission old system
✓ Full monitoring & alerting
✓ Weekly model retraining
✓ Monthly performance review
✓ Quarterly business review
```

---

## 6. Financial Analysis

### Investment Required

**Development & Infrastructure:**
```
Security Implementation:        $150,000
Scalability (HW/Cloud):         $200,000
Compliance Review:              $100,000
Staff Training:                 $50,000
Monitoring Tools (annual):      $30,000
─────────────────────────────────────
Total Year 1 Investment:        $530,000
```

**Ongoing Annual Costs:**
```
Cloud Infrastructure:           $240,000
Model Retraining (compute):     $60,000
Monitoring & Tools:             $30,000
Incident Response (on-call):    $80,000
Compliance (annual audit):      $40,000
─────────────────────────────────────
Total Annual Operating Cost:    $450,000
```

---

### Expected Returns

**Annual Fraud Prevention (50M transactions/year):**
```
Fraud Prevented:                $9,128,000
False Positive Cost:            -$265,000
False Negative Cost:            -$1,270,000
Operating Cost:                 -$450,000
─────────────────────────────────────
Net Annual Benefit:             $7,143,000
```

**5-Year Projection:**
```
Year 1: -$530,000 (investment) + $7,143,000 = $6,613,000
Year 2-5: $7,143,000/year × 4 = $28,572,000
─────────────────────────────────────
Total 5-Year Net Benefit:       $35,185,000
```

**ROI Metrics:**
```
Payback Period:       1.1 months
5-Year ROI:           6,639% (66x return)
Internal Rate of Return: 1,248%/year
```

**Conclusion:** Excellent financial justification despite 6-8 week delay.

---

## 7. Recommendations

### Immediate Actions (This Week)

1. **Form Security Task Force**
   - Assign dedicated security engineer
   - Engage external penetration tester
   - Schedule PCI-DSS compliance audit

2. **Freeze Feature Development**
   - Focus 100% on go-live blockers
   - No new features until security complete

3. **Stakeholder Communication**
   - Inform executives of 6-8 week delay
   - Explain critical security gaps
   - Present financial justification

---

### Go/No-Go Decision

**Current Recommendation: 🚫 DO NOT GO LIVE**

**Rationale:**
- ❌ 3 critical blockers (security, scalability, compliance)
- ❌ 0/8 security controls implemented
- ❌ No PCI-DSS/GDPR compliance review
- ⚠️ Model precision below target (82% vs 85%)

**Next Decision Point:** End of Week 6
- Expected: All security controls implemented
- Expected: Compliance review complete
- Expected: Scalability validated
- Expected: Model precision ≥ 85%

**Approval Required:**
- ☐ Chief Information Security Officer (CISO)
- ☐ Chief Risk Officer (CRO)
- ☐ VP Engineering
- ☐ Compliance Officer
- ☐ CFO (budget approval)

---

## 8. Conclusion

The Real-time Fraud Detection System demonstrates **strong technical capabilities** with 93% fraud detection recall and excellent financial projections ($7.1M annual benefit). However, **critical security and compliance gaps** prevent immediate deployment.

**Key Takeaways:**
1. ✅ **Technology Works:** System successfully processes transactions and detects fraud
2. ✅ **Strong ROI:** $35M net benefit over 5 years (66x return)
3. ❌ **Security Gaps:** No authentication, encryption, or audit logging
4. ❌ **Not Production Ready:** 6-8 weeks additional work required
5. ⚠️ **Go-Live Date:** Target March 2026 (after all blockers resolved)

**Management Decision Required:**
- Accept 6-8 week delay for proper security implementation?
- Approve $530K Year 1 investment?
- Commit resources to security task force?

**Risk of Rushing:**
- Regulatory fines ($100K-$1M per GDPR/PCI-DSS violation)
- Data breach costs (average $4.45M per incident)
- Reputation damage (priceless)

**Recommendation:** **Invest the 6-8 weeks** to do this right. The financial upside justifies the wait, and the security risks of rushing are too high.

---

**Prepared by:** Sojirat.S, ML Engineer
**Email:** s6707021857112@email.kmutnb.ac.th
**Date:** January 5, 2026
**Version:** 1.0

---

## Appendix: Technical Specifications

### Model Details
```
Algorithm:             Logistic Regression
Training Data:         creditcard.csv (2013)
Features:              28 PCA components + Amount + Time
Training Set:          80% (226,980 transactions)
Test Set:              20% (56,746 transactions)
Hyperparameters:       Default scikit-learn
Fraud Threshold:       0.0186 (1.86% probability)
```

### Infrastructure Specs
```
Kafka Version:         3.7.0 (Apache)
Spark Version:         3.5.3 (Bitnami)
Python Version:        3.11
Producer Framework:    kafka-python 2.0.2
Consumer Framework:    kafka-python 2.0.2
ML Framework:          scikit-learn 1.3.2
Data Processing:       pandas 2.1.4
Container Platform:    Docker 24.0.7
Orchestration:         docker-compose 2.23.0
```

### Performance Benchmarks
```
Steady Mode:
- Throughput: 1,500 msg/s
- Batch size: 500
- Batch interval: 250ms
- Total batches: 568
- Total time: ~3 minutes

Burst Mode:
- Throughput: 6,000-7,000 msg/s peak
- Burst size: 2,000 msgs
- Burst duration: 2 seconds
- Quiet period: 10 seconds
- Cycle count: 8+ cycles

Late Events Mode:
- Throughput: 1,500 msg/s
- Late rate: 10%
- Delay range: 30-180 seconds
- Watermark: 2 minutes (120s)
```

---

**END OF REPORT**
