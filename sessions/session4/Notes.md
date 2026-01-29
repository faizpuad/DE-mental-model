# Session 4 Notes: AWS Data Engineering Fundamentals

## Theoretical Concepts

### Local vs Cloud Data Engineering

**First Principles**
- Data pipelines can run anywhere: local machines or cloud platforms
- Choice impacts cost, scalability, and complexity
- Same transformation logic should work in both environments
- Understanding trade-offs is essential for data engineers

**Why Learn Both Approaches**
- Local development is fast and free for learning/testing
- Cloud deployment provides production reliability and scalability
- Real-world projects often use both (dev locally, deploy to cloud)
- Different scenarios require different solutions

**Implementation Patterns**
1. **Local Development**: Docker + PostgreSQL + dbt
   - Fast iteration and debugging
   - Zero cost for learning
   - Full control over environment
   - Limited scalability

2. **Cloud Deployment**: S3 + RDS + Lambda + dbt
   - Production reliability
   - Team collaboration
   - Automated backups and monitoring
   - Higher cost but more features

3. **Hybrid Approach**: Develop locally, deploy to cloud
   - Best of both worlds
   - Test transformations locally
   - Deploy validated models to production
   - Gradual migration path

**AWS Core Services for Data Engineering**
- **Amazon S3**: Scalable storage for data lakes
- **Amazon RDS**: Managed relational databases
- **AWS Lambda**: Serverless compute for event processing
- **Amazon CloudWatch**: Monitoring and logging
- **Amazon SNS**: Notification services

### Scheduling and Automation

**First Principles**
- Automation reduces manual errors and saves time
- Scheduling ensures regular data updates
- Choose automation method based on environment and complexity
- Balance between data freshness and operational overhead

**Implementation Approaches**

**Local Scheduling with Cron**
```bash
# Simple cron every 5 minutes
*/5 * * * * /path/to/pipeline.py

# Advantages:
- Simple and reliable
- No additional services needed
- Easy to debug with log files
- Zero cost

# Limitations:
- Only works when machine is running
- No retry logic or error handling
- Manual monitoring required
```

**AWS Scheduling with EventBridge**
```bash
# EventBridge rule for daily execution
aws events put-rule \
  --name "retail-pipeline-daily" \
  --schedule-expression "cron(0 2 * * ? *)"

# Advantages:
- Managed service with high availability
- Can trigger Lambda, Step Functions, etc.
- Built-in retry and error handling
- Cloud monitoring and alerts

# Considerations:
- Additional cost
- More complex setup
- Requires AWS expertise
```

**Event-Driven Processing**
- Local: File system watchers (inotify)
- AWS: S3 event notifications → Lambda
- Best for real-time requirements
- More efficient than polling

**Hybrid Scheduling Strategy**
1. **Development**: Manual execution for rapid iteration
2. **Testing**: Cron for regular validation
3. **Production**: EventBridge + Lambda + manual dbt runs
4. **Monitoring**: CloudWatch logs and metrics

### Monitoring & Observability

**First Principles**
- Observability = Logs + Metrics + Alerting
- Different environments require different monitoring approaches
- Local development needs simple debugging tools
- Production requires comprehensive monitoring and alerting
- Proactive monitoring prevents data pipeline failures

**Local Monitoring Approach**

**1. Log Files**
```bash
# Local log locations
local/logs/pipeline_YYYYMMDD.log    # Pipeline execution logs
local/logs/dbt.log                  # dbt transformation logs
local/logs/cron.log                 # Cron execution logs

# Log monitoring commands
tail -f local/logs/pipeline_20260127.log
docker-compose logs -f pipeline
grep "ERROR" local/logs/*.log
```

**2. Manual Metrics**
- Row counts in database tables
- Pipeline execution time
- File sizes and timestamps
- Memory and CPU usage

**AWS Monitoring Implementation**

**1. CloudWatch Logs**
- Lambda function logs automatically captured
- RDS slow query logs
- Custom application logs
- 7-day retention (configurable)

**2. CloudWatch Metrics**
- RDS CPU, memory, storage utilization
- Lambda invocation counts and errors
- Data transfer metrics
- Custom metrics via PutMetricData API

**3. SNS Notifications**
- Pipeline success/failure alerts
- Email notifications
- Can integrate with Slack, PagerDuty, etc.

**Key Metrics for Data Pipelines**

**Pipeline Health**
- Success Rate: % of runs completing successfully
- Execution Time: Duration of each pipeline stage
- Error Rate: Failed operations per run
- Data Freshness: Time since last successful run

**Data Quality**
- Row counts in bronze/silver/gold layers
- Null value percentages
- Duplicate detection results
- Validation test results

**Resource Utilization**
- Local: Docker container memory/CPU usage
- AWS: RDS instance performance
- Storage: Disk space or S3 usage
- Network: Data transfer volumes

**Monitoring Setup Examples**

**Local Monitoring Script**
```python
# Simple health check for local pipeline
def check_pipeline_health():
    # Check recent logs for errors
    errors = count_recent_errors('local/logs/')
    
    # Check database connectivity
    db_status = test_postgres_connection()
    
    # Check file timestamps
    data_freshness = get_file_age('data/online_retail.xlsx')
    
    return {
        'errors': errors,
        'database': db_status,
        'data_freshness': data_freshness
    }
```

**AWS Monitoring Setup**
```bash
# Create CloudWatch alarm for RDS CPU
aws cloudwatch put-metric-alarm \
  --alarm-name "retail-pipeline-rds-cpu" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# Create SNS topic for alerts
aws sns create-topic --name retail-pipeline-alerts
```

### Cost Optimization

**First Principles**
- Cloud costs can grow exponentially without oversight
- Cost optimization is ongoing, not one-time
- Balance performance vs. cost
- Monitor and iterate

**Cost Optimization Pillars**

**1. Right-Sizing**
- Use appropriate resource sizes
- Scale down when not needed
- Monitor utilization
- Example: Use Lambda with right memory allocation

**2. Resource Efficiency**
- Use serverless when possible
- Leverage auto-scaling
- Turn off unused resources
- Example: Use Lambda instead of EC2

**3. Pricing Models**
- Choose appropriate pricing tiers
- Use reserved instances for steady workloads
- Use spot instances for fault-tolerant workloads
- Example: RDS reserved instances

**4. Lifecycle Management**
- Delete old data (logs, backups)
- Use cheaper storage tiers (S3 Glacier)
- Implement data retention policies
- Example: Move logs to Glacier after 90 days

**AWS Cost Management Services**
- **AWS Cost Explorer**: Visualize and analyze costs
- **AWS Budgets**: Set spending limits and alerts
- **AWS Trusted Advisor**: Optimization recommendations
- **AWS Cost and Usage Reports**: Detailed cost data

**Cost Monitoring Dashboard**
- Daily spend by service
- Cost by region
- Cost by resource type
- Forecast vs. actual
- Anomaly detection

### AWS Cloud Architecture

**Local to AWS Service Mapping**

| Local Component | AWS Component | Purpose |
|----------------|----------------|----------|
| Docker Compose | Manual + Scripts | Orchestration |
| Python Scripts | AWS Lambda | Event Processing |
| Local Files | Amazon S3 | Data Storage |
| PostgreSQL | Amazon RDS | Database |
| Log Files | CloudWatch Logs | Logging |
| Manual Checks | CloudWatch Metrics | Monitoring |
| Cron Jobs | EventBridge (optional) | Scheduling |
| Email Alerts | SNS Notifications | Alerting |

**Actual Implementation Architecture**

**Local Architecture**
```
┌─────────────────────────────────────────────────────────┐
│               Docker Host (Local Machine)               │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  PostgreSQL  │  │   Pipeline   │  │   dbt        │ │
│  │  Container   │  │   Container  │  │   Container  │ │
│  │              │  │              │  │              │ │
│  │  Port 5432   │◄─┤ Python +    │  │  Transform   │ │
│  │              │  │ Cron Jobs   │  │  Models      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ▲                  │                │          │
│         │                  ▼                │          │
│         │          ┌──────────────┐         │          │
│         │          │  Log Files   │◄────────┘          │
│         │          └──────────────┘                    │
│         │                                               │
│         ▼                                               │
│  ┌──────────────┐                                       │
│  │  Data Files  │                                       │
│  │  (mounted)   │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

**AWS Architecture**
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                     AWS CLOUD                                    │
│                                                                                  │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌────────┐   │
│   │ EventBridge  │─────>│    Lambda    │─────>│   S3 Bucket  │─────>│  SNS   │───┐
│   │  (Schedule)  │      │ (Pull/Check) │      │    (Data)    │      │ (Email)│   │
│   └──────────────┘      └──────────────┘      └──────▲───────┘      └────────┘   │
│                                                      │                   ▲       │
│   ┌──────────────┐      ┌──────────────┐             │                   │       │
│   │  S3 Event    │─────>│    Lambda    │─────────────┼───────────────────┘       │
│   │   Trigger    │      │   (Notify)   │             │                           │
│   └──────▲───────┘      └──────────────┘             │                           │
│          │                                           │                           │
└──────────┼───────────────────────────────────────────┼───────────────────────────┘
           │                                           │
    (S3 Notification)                         (Upload / API Call)
           │                                           │
┌──────────┴───────────────────────────────────────────┴───────────────────────────┐
│                              LOCAL DEVELOPMENT                                   │
│                                                                                  │
│  1. Setup:         initialize_rds.py  ────> [ Create Bronze Schema in RDS ]      │
│                                                                                  │
│  2. Ingestion:     ingest_s3_to_rds.py ───> [ Transform & Push to Bronze ]       │
│                                                                                  │
│  3. Transformation: dbt run (Manual)   ───> [ Create Silver & Gold in RDS ]      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions**

**Why This Architecture?**
1. **Simplicity**: Uses core AWS services without complex orchestration
2. **Cost-Effectiveness**: Lambda and S3 are pay-per-use, RDS is minimal instance
3. **Learning Value**: Demonstrates fundamental AWS data engineering patterns
4. **Flexibility**: Can be extended with more services as needed

**Data Flow**
1. **Upload**: Data uploaded to S3 (manually or automated)
2. **Event**: S3 triggers Lambda function
3. **Notification**: Lambda sends SNS notification
4. **Processing**: Local Python scripts download from S3 and load to RDS
5. **Transformation**: dbt runs locally connecting to RDS
6. **Monitoring**: All activities logged to CloudWatch

**Alternative Patterns (Not Implemented)**
- **Step Functions**: For complex orchestration (overkill for this use case)
- **MWAA/Airflow**: For advanced workflow management (higher cost/complexity)
- **Glue**: For serverless ETL (different transformation paradigm)
- **ECS/EKS**: For containerized workloads (more DevOps overhead)

## Implementation Considerations

### Infrastructure Management

**Local Development**
- Docker Compose for service orchestration
- Environment variables for configuration
- Volume mounts for data persistence
- Local logs and monitoring

**AWS Deployment**
- CloudFormation templates for reproducible infrastructure
- Make scripts for common operations
- Environment configuration via .env files
- AWS CLI for automation

### Security Best Practices

**Local Security**
- Use .env files instead of hardcoded credentials
- Limit database connections to localhost
- Regular security updates for Docker images
- Sensitive data encryption when needed

**AWS Security**
- IAM roles with least privilege principle
- RDS security groups with IP restrictions
- S3 bucket policies and encryption
- CloudTrail for API auditing
- Secrets Manager for credential storage

### Cost Optimization

**Local Cost**
- Electricity usage (~$2-5/month if running 24/7)
- No additional software costs
- Free for development and learning

**AWS Cost Management**
- RDS instance sizing (db.t3.micro for development)
- S3 lifecycle policies for old data
- Lambda free tier usage
- CloudWatch log retention policies
- Turn off resources when not in use

**Monthly Cost Breakdown (Development)**
- RDS db.t3.micro: ~$15-20
- S3 storage (<5GB): ~$0.50
- Lambda (within free tier): $0
- NAT Gateway: ~$32 (can be optimized)
- Data transfer: ~$1
- CloudWatch logs: ~$2.50
- **Total: ~$50-55/month**

### High Availability and Scaling

**Current Implementation**
- Single RDS instance (manual failover)
- Lambda auto-scaling (built-in)
- S3 durability (99.999999999%)
- No multi-AZ configuration (cost saving)

**Production Enhancements**
- RDS Multi-AZ for automatic failover
- RDS read replicas for query scaling
- Cross-region S3 replication
- More sophisticated monitoring and alerting

### Monitoring and Maintenance

**Local Maintenance**
- Log file rotation and cleanup
- Docker container health checks
- Database backups and maintenance
- File system monitoring

**AWS Maintenance**
- RDS automated backups and maintenance windows
- CloudWatch log retention policies
- Cost monitoring and alerts
- Security group reviews
- IAM policy audits

### Development vs Production Trade-offs

**Development Environment (Current Focus)**
- Fast iteration and debugging
- Minimal cost overhead
- Simple architecture for learning
- Manual processes are acceptable

**Production Environment (Future Enhancement)**
- Automated deployment and rollback
- Comprehensive monitoring and alerting
- High availability and disaster recovery
- Compliance and audit requirements
- Multi-environment management (dev/staging/prod)
