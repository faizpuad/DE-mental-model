# Session 4: Local vs AWS Implementation - Complete Comparison

This guide provides a side-by-side comparison of running the same data pipeline locally vs on AWS.

## 📋 Table of Contents

1. [Quick Comparison](#quick-comparison)
2. [Step-by-Step: Local Setup](#step-by-step-local-setup)
3. [Step-by-Step: AWS Setup](#step-by-step-aws-setup)
4. [Architecture Comparison](#architecture-comparison)
5. [Cost Comparison](#cost-comparison)
6. [When to Use Which](#when-to-use-which)

---

## Quick Comparison

| Aspect | Local | AWS |
|--------|-------|-----|
| **Setup Time** | 5-10 minutes | 15-20 minutes |
| **Cost** | $0 (electricity only) | ~$50/month |
| **Database** | PostgreSQL (Docker) | RDS PostgreSQL |
| **Storage** | Local filesystem | S3 |
| **Compute** | Docker containers | Lambda + Local dbt |
| **Orchestration** | Cron + Python | SNS + Manual dbt |
| **Monitoring** | Log files | CloudWatch Logs |
| **Scalability** | Limited by machine | Cloud scalable |
| **Access** | localhost only | Internet accessible |
| **Backup** | Manual snapshots | Automated (RDS) |
| **Best For** | Development, learning | Production, team collaboration |

---

## Step-by-Step: Local Setup

### Prerequisites
- Docker Desktop installed
- 4 GB RAM, 5 GB disk space
- Ports 5432, 8088 available

### Complete Setup (5 Steps)

```bash
# Step 1: Navigate to directory
cd sessions/session4/local

# Step 2: Create configuration
cp .env.example .env

# Step 3: Build containers
docker-compose build

# Step 4: Start services
docker-compose up -d

# Step 5: Run initial pipeline
docker-compose exec pipeline python3 /app/scripts/pipeline.py
```

**Time:** ~5-10 minutes

**Result:**
- ✅ 541,897 rows in bronze layer
- ✅ 3 dimension/fact tables in silver
- ✅ 3 analytics tables in gold
- ✅ Automated cron every 5 minutes

---

## Step-by-Step: AWS Setup

### Prerequisites
- AWS Account with credentials configured
- AWS CLI installed
- PostgreSQL client (psql) installed
- Python with boto3, pandas, psycopg2

### Complete Setup (6 Steps)

```bash
# Step 1: Navigate to directory
cd sessions/session4/aws

# Step 2: Configure AWS
export AWS_REGION="us-east-1"
export DB_PASSWORD="YourSecurePassword123"
export DATA_BUCKET_NAME="retail-pipeline-$(date +%s)"

# Step 3: Deploy infrastructure (10-15 min)
make deploy

# Step 4: Load configuration
source aws_config.env

# Step 5: Upload data to S3
make upload

# Step 6: Ingest data to RDS
make ingest

# Step 7: Run dbt transformations
make dbt-run
```

**Time:** ~15-20 minutes (mostly waiting for RDS)

**Result:**
- ✅ S3 bucket with data
- ✅ RDS PostgreSQL instance
- ✅ Lambda for S3 event detection
- ✅ Same data in cloud database
- ✅ SNS notifications

---

## Architecture Comparison

### Local Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Docker Host (Local Machine)               │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  PostgreSQL  │  │   Pipeline   │  │   Superset   │ │
│  │  Container   │  │   Container  │  │   Container  │ │
│  │              │  │              │  │              │ │
│  │  Port 5432   │◄─┤ cron + dbt   │  │  Port 8088   │ │
│  └──────────────┘  │ + Python     │  └──────────────┘ │
│         ▲          └──────────────┘         │          │
│         │                  │                │          │
│         │                  ▼                │          │
│         │          ┌──────────────┐         │          │
│         └──────────┤  Log Files   │◄────────┘          │
│                    └──────────────┘                    │
│                                                         │
│  Data: /data/online_retail.xlsx (host mount)          │
└─────────────────────────────────────────────────────────┘

Access: localhost only
Cost: $0
Backup: Manual (docker volumes)
```

### AWS Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        AWS Cloud                              │
│                                                               │
│  ┌──────────┐   S3 event   ┌──────────┐   notifies          │
│  │  S3      │─────────────>│  Lambda  │──────────────>       │
│  │  Bucket  │              │  Event   │              SNS     │
│  │          │              │  Handler │              Topic   │
│  └──────────┘              └──────────┘               │      │
│      │                          │                     │      │
│      │                          v                     │      │
│      │                     ┌──────────┐              │      │
│      │                     │   RDS    │              │      │
│      │                     │PostgreSQL│              │      │
│      │                     │ (public) │◄─────┐       │      │
│      │                     └──────────┘      │       │      │
│      │                                       │       │      │
└──────│───────────────────────────────────────│───────│──────┘
       │                                       │       │
       │ download                              │       │ email
       ▼                                       │       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Local Development                         │
│                                                             │
│  ┌──────────┐  ingest   ┌──────────┐  transform           │
│  │S3 → Local│─────────>│   dbt     │──────────────>       │
│  │ Download │          │   Local   │              RDS     │
│  └──────────┘          │Connection │               ▲      │
│                        └───────────┘               │      │
│                             │                      │      │
│                             └──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘

Access: Internet (RDS public endpoint)
Cost: ~$50/month
Backup: Automated (RDS snapshots)
```

---

## Detailed Feature Comparison

### 1. Database

| Feature | Local | AWS |
|---------|-------|-----|
| **Type** | PostgreSQL 15 (Docker) | RDS PostgreSQL 15.4 |
| **Instance** | No limits (uses host resources) | db.t3.micro (1 vCPU, 1 GB RAM) |
| **Storage** | Docker volume (auto-expands) | 20 GB SSD (gp3) |
| **Connection** | localhost:5432 | public-endpoint.rds.amazonaws.com:5432 |
| **High Availability** | No (single container) | Multi-AZ optional |
| **Backup** | Manual volume snapshots | Automated daily snapshots (7 days) |
| **Restore** | Manual volume restore | Point-in-time recovery |
| **Cost** | $0 | ~$15-20/month |

**Connection Examples:**

Local:
```bash
psql -h localhost -p 5432 -U postgres -d retail_db
```

AWS:
```bash
psql -h retail-pipeline-dev.xxx.us-east-1.rds.amazonaws.com -p 5432 -U postgres -d retail_db
```

### 2. Storage

| Feature | Local | AWS |
|---------|-------|-----|
| **Type** | Local filesystem | S3 Standard |
| **Location** | /data/ (host mount) | s3://bucket-name/input/ |
| **Capacity** | Limited by disk | Unlimited |
| **Versioning** | No | Yes (enabled) |
| **Lifecycle** | Manual cleanup | Auto-delete after 90 days |
| **Encryption** | No | AES-256 (server-side) |
| **Cost** | $0 | ~$0.50/month (< 5 GB) |

**Upload Examples:**

Local:
```bash
# Data is already mounted at /data/online_retail.xlsx
```

AWS:
```bash
aws s3 cp online_retail.xlsx s3://bucket-name/input/
```

### 3. Compute

| Feature | Local | AWS |
|---------|-------|-----|
| **Ingestion** | Python script in Docker | Lambda (event detection) + Python script |
| **Transformation** | dbt in Docker | dbt locally connecting to RDS |
| **Memory** | Shared with host | Lambda: 256 MB, Local: unlimited |
| **Timeout** | No limit | Lambda: 60s (event handler only) |
| **Scaling** | No (single container) | Lambda auto-scales |
| **Cost** | $0 | ~$1/month (Lambda) |

**Execution Examples:**

Local:
```bash
docker-compose exec pipeline python3 /app/scripts/pipeline.py
```

AWS:
```bash
# 1. Upload triggers Lambda automatically
# 2. Run ingestion manually
python3 aws/scripts/ingest_from_s3_to_rds.py ...

# 3. Run dbt locally
dbt run --profiles-dir aws/dbt_profile --target aws
```

### 4. Orchestration

| Feature | Local | AWS |
|---------|-------|-----|
| **Method** | Cron + Python | SNS + Manual trigger |
| **Schedule** | Every 5 minutes | On S3 upload or EventBridge |
| **Retries** | No (manual) | Manual retry |
| **Dependencies** | Python script manages | Manual dependency management |
| **Visibility** | Log files | CloudWatch Logs + SNS email |
| **Cost** | $0 | SNS: ~$1/month |

**Configuration Examples:**

Local cron:
```bash
# In .env file
CRON_SCHEDULE=*/5 * * * *
```

AWS EventBridge (optional):
```bash
# Enable daily schedule
aws events enable-rule --name retail-pipeline-schedule
```

### 5. Monitoring

| Feature | Local | AWS |
|---------|-------|-----|
| **Logs** | Local files | CloudWatch Logs |
| **Retention** | Manual cleanup | 7 days |
| **Search** | grep, tail | CloudWatch Insights |
| **Alerts** | No | SNS email notifications |
| **Metrics** | No | CloudWatch Metrics |
| **Cost** | $0 | ~$2.50/month |

**Log Access Examples:**

Local:
```bash
tail -f local/logs/pipeline_20260127.log
docker-compose logs -f pipeline
```

AWS:
```bash
aws logs tail /aws/lambda/retail-pipeline-s3-event-handler --follow
```

---

## Cost Breakdown

### Local (Monthly)

| Item | Cost |
|------|------|
| Electricity (Docker running 24/7) | ~$2-5 |
| **Total** | **$2-5** |

### AWS (Monthly - us-east-1)

| Service | Configuration | Cost |
|---------|--------------|------|
| RDS db.t3.micro | 20 GB storage, 7-day backups | $15-20 |
| S3 Standard | < 5 GB storage | $0.50 |
| Lambda | < 1M invocations | $0 (Free tier) |
| NAT Gateway | 1 instance | $32 |
| Data Transfer | < 10 GB out | $1 |
| CloudWatch Logs | < 5 GB | $2.50 |
| SNS | < 1000 notifications | $1 |
| **Total** | | **$52-57** |

**Cost Optimization Tips:**

AWS:
```bash
# Stop RDS when not in use (saves ~$15/month)
aws rds stop-db-instance --db-instance-identifier retail-pipeline-dev

# Delete NAT Gateway if Lambda doesn't need internet
# (saves $32/month, but Lambda can't download packages)

# Use RDS in public subnet (requires careful security setup)
```

---

## Performance Comparison

### Local Performance

| Operation | Time |
|-----------|------|
| Excel read | ~47 seconds |
| Bronze insert (541K rows) | ~165 seconds |
| dbt transformations | ~11 seconds |
| Data validation | ~5 seconds |
| **Total pipeline** | **~180 seconds** |

### AWS Performance

| Operation | Time |
|-----------|------|
| S3 upload | ~30 seconds (depends on bandwidth) |
| Lambda trigger | < 1 second |
| S3 download | ~20 seconds |
| Bronze insert (541K rows) | ~165 seconds (same) |
| dbt transformations | ~15 seconds (network latency) |
| **Total pipeline** | **~230 seconds** |

**Note:** AWS has additional network latency but can scale better with larger datasets.

---

## When to Use Which?

### Use Local When:

✅ **Development and Learning**
- Testing new transformations
- Learning dbt and SQL
- Rapid iteration and debugging
- No internet required

✅ **Cost Sensitive**
- Budget constraints
- Temporary projects
- Educational purposes

✅ **Data Privacy**
- Sensitive data that cannot leave premises
- Compliance requirements
- Air-gapped environments

✅ **Small Scale**
- Dataset < 1 GB
- Single user
- Infrequent runs

### Use AWS When:

✅ **Production Workloads**
- Production data pipelines
- Business-critical analytics
- 24/7 availability required

✅ **Team Collaboration**
- Multiple users need access
- Shared database for team
- Centralized data platform

✅ **Scalability Needed**
- Growing datasets (> 1 GB)
- Increasing query load
- Future growth expected

✅ **High Availability**
- Cannot afford downtime
- Need automatic failover
- Disaster recovery required

✅ **Integration Requirements**
- Connecting to other AWS services
- Third-party integrations
- External API access needed

---

## Migration Path: Local → AWS

### Step 1: Verify Local Works

```bash
cd sessions/session4/local
make test
# All tests should pass
```

### Step 2: Deploy AWS Infrastructure

```bash
cd ../aws
make deploy
source aws_config.env
```

### Step 3: Upload Data

```bash
make upload
```

### Step 4: Ingest to RDS

```bash
make ingest
```

### Step 5: Run dbt on AWS

```bash
cd ../local
dbt run --profiles-dir ../aws/dbt_profile --target aws
```

### Step 6: Verify Same Results

```bash
# Local row counts
cd local
docker-compose exec postgres psql -U postgres -d retail_db -c "
SELECT COUNT(*) FROM bronze.raw_transactions;
"

# AWS row counts
cd ../aws
PGPASSWORD=$AWS_RDS_PASSWORD psql \
    -h $AWS_RDS_HOST \
    -U postgres \
    -d retail_db \
    -c "SELECT COUNT(*) FROM bronze.raw_transactions;"
```

**Expected:** Identical row counts!

---

## Hybrid Approach (Best of Both)

Use both local and AWS for different purposes:

### Development Workflow

```
1. Develop locally
   ├─ Fast iteration
   ├─ Test transformations
   └─ Debug issues

2. Test on AWS (staging)
   ├─ Verify cloud compatibility
   ├─ Check performance
   └─ Test integrations

3. Deploy to AWS (production)
   ├─ Run on schedule
   ├─ Serve team/business
   └─ Monitor and maintain
```

### Example Schedule

```bash
# Morning: Develop new features locally
cd local
docker-compose up -d
# Edit dbt models...
dbt run --profiles-dir . --target local

# Afternoon: Test on AWS staging
cd ../aws
dbt run --profiles-dir dbt_profile --target aws

# Evening: Deploy to production (if tests pass)
# Production deployment (separate stack)
```

---

## Troubleshooting Comparison

### Issue: Slow Performance

**Local:**
```bash
# Check Docker resources
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Preferences → Resources → Memory: 8 GB
```

**AWS:**
```bash
# Check RDS CPU utilization
aws cloudwatch get-metric-statistics \
    --namespace AWS/RDS \
    --metric-name CPUUtilization \
    --dimensions Name=DBInstanceIdentifier,Value=retail-pipeline-dev \
    --start-time 2026-01-27T00:00:00Z \
    --end-time 2026-01-27T23:59:59Z \
    --period 3600 \
    --statistics Average

# Consider upgrading RDS instance class
# db.t3.micro → db.t3.small (2 vCPU, 2 GB RAM)
```

### Issue: Connection Refused

**Local:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres
```

**AWS:**
```bash
# Check security group rules
aws ec2 describe-security-groups \
    --group-ids sg-xxx

# Verify your IP is allowed
# Update AllowedCIDR in CloudFormation parameters
```

---

## Summary: Quick Decision Matrix

| Your Situation | Recommendation |
|----------------|----------------|
| Learning data engineering | Start with **Local** |
| Building POC/MVP | Start with **Local** |
| Production pipeline | Use **AWS** |
| Team of 2+ people | Use **AWS** |
| Budget: $0 | Use **Local** |
| Need 99.9% uptime | Use **AWS** |
| Dataset > 10 GB | Use **AWS** |
| Dataset < 1 GB | Either (start **Local**) |
| Need to demo quickly | Use **Local** (5 min setup) |
| Long-term project | Use **AWS** |

---

## Conclusion

Both local and AWS implementations:
- ✅ Use same dbt models (100% compatible)
- ✅ Produce identical results
- ✅ Follow medallion architecture
- ✅ Support testing and validation
- ✅ Are production-ready

**Key Difference:**
- Local = Development speed + $0 cost
- AWS = Production reliability + team collaboration

**Best Practice:** Master local first, then graduate to AWS when ready.

---

## Quick Reference Commands

### Local
```bash
make start    # Start pipeline
make pipeline # Run manually
make logs     # View logs
make stop     # Stop pipeline
```

### AWS
```bash
make deploy   # Deploy infrastructure
make upload   # Upload to S3
make ingest   # Load to RDS
make dbt-run  # Transform data
make test     # Verify everything
make cleanup  # Delete all resources
```

---

**Need Help?**
- Local issues: See `local/STEP_BY_STEP_GUIDE.md`
- AWS issues: See `aws/README.md` troubleshooting section
- Both: Review this comparison guide

**Ready to start?**
1. Go to `local/STEP_BY_STEP_GUIDE.md` for detailed local setup
2. Go to `aws/README.md` for detailed AWS setup
3. Use this guide to understand the differences
