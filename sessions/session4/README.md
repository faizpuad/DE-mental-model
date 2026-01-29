# Session 4: AWS Data Engineering Fundamentals

Learn AWS data engineering by building the same retail pipeline twice: **locally** (Docker + dbt + PostgreSQL) and on **AWS** (S3 + RDS + Lambda + dbt).

## 🎯 Learning Objectives

By completing this session, you will:
1. ✅ Build a production-ready local data pipeline with medallion architecture
2. ✅ Deploy the same pipeline to AWS using cloud services
3. ✅ Understand local vs cloud trade-offs (cost, scalability, complexity)
4. ✅ Master dbt transformations that work in both environments
5. ✅ Learn AWS fundamentals: S3, RDS, Lambda, CloudWatch, SNS

---

## 📚 Documentation Index

### Getting Started
- **[LOCAL_VS_AWS_COMPARISON.md](LOCAL_VS_AWS_COMPARISON.md)** - Side-by-side comparison, when to use which

### Local Setup (Start Here!)
- **[local/STEP_BY_STEP_GUIDE.md](local/STEP_BY_STEP_GUIDE.md)** - Complete walkthrough (10 steps)
- **[local/README.md](local/README.md)** - Quick reference and troubleshooting
- **[local/TEST_RESULTS.md](local/TEST_RESULTS.md)** - Testing documentation

### AWS Setup (After Local)
- **[aws/README.md](aws/README.md)** - Complete AWS deployment guide
- **[aws/Makefile](aws/Makefile)** - Quick commands reference

### Reference
- **[thoughts/shared/plans/004_session4_aws_fundamentals_refinement.md](../../thoughts/shared/plans/004_session4_aws_fundamentals_refinement.md)** - Implementation plan and progress

---

## 🚀 Quick Start

### Option 1: Local Setup (5 minutes)

```bash
cd local
docker-compose up -d
docker-compose exec pipeline python3 /app/scripts/pipeline.py
```

**Result:** Complete data pipeline running on your machine at zero cost.

### Option 2: AWS Setup (15 minutes + AWS account required)

```bash
cd aws
make deploy
source aws_config.env
make upload && make ingest && make dbt-run
make test
```

**Result:** Production-ready pipeline on AWS with automated backups and monitoring.

---

## 📊 What You'll Build

### Medallion Architecture (Same for Both Local & AWS)

```
1. Bronze Layer (Raw Data)
   └─ raw_transactions (541,897 rows)

2. Silver Layer (Dimensional Model)
   ├─ dim_date (305 days)
   ├─ dim_product (4,069 products)
   └─ fact_sales_daily (305,476 facts)

3. Gold Layer (Analytics)
   ├─ monthly_sales_summary (13 months)
   ├─ top_products_by_revenue (top 100)
   └─ country_performance (38 countries)
```

---

## 💰 Cost Comparison

| Setup | Monthly Cost | Setup Time | Best For |
|-------|--------------|------------|----------|
| **Local** | $0 | 5 minutes | Development, learning |
| **AWS** | ~$50-55 | 15 minutes | Production, teams |

---

## 📖 Learning Path

### Step 1: Master Local (1-2 hours)
Follow [local/STEP_BY_STEP_GUIDE](local/README.md)

### Step 2: Deploy to AWS (1-2 hours)
Follow [aws/README.md](aws/README.md)

---

## ✅ Completion Checklist

- [ ] Local pipeline running successfully
- [ ] All 29 dbt tests passing
- [ ] AWS infrastructure deployed
- [ ] Same data in both environments
- [ ] Understand when to use local vs AWS
- [ ] Can troubleshoot common issues

---

**Ready to start?** Go to [local/STEP_BY_STEP_GUIDE.md](local/README.md) 🚀
