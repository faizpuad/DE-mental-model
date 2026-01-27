# Data Engineering Learning Path

## Purpose

As an AWS community builder focused on data, I provide this curriculum as a community service initiative. This learning material is designed specifically for colleagues starting their data engineering journey, offering a practical pathway to build essential skills and portfolio projects.

## Overview

This curriculum consists of 4 progressive sessions that build fundamental data engineering competencies. Each session delivers incremental learning through hands-on projects that simulate real-world data pipeline development. Upon completion, learners will possess solid data engineering knowledge and a portfolio project suitable for entry-level job applications.

## Curriculum Development

The syllabus is curated from comprehensive experience including:
- Professional data engineering practice
- Mentorship and knowledge transfer
- AWS DEA-C01 certification preparation
- Industry bootcamp methodologies
- AI-assisted content development for accelerated creation

## Session Structure

### Session 1: Data Ingestion Pipeline
**Objective**: Master data extraction and storage fundamentals

**Core Components**:
- Excel file processing using pandas and PostgreSQL
- Database schema design with normalization principles
- Bronze layer data ingestion with quality validation
- Basic error handling and data cleaning
- Container deployment with Docker

**Technical Focus**:
- PostgreSQL database operations and connection management
- Data validation and type conversion
- File processing workflows
- Containerization fundamentals

**Deliverable**: Functional data ingestion pipeline that transforms raw Excel files into structured database tables

### Session 2: Data Modeling & Transformation
**Objective**: Implement medallion architecture and data transformation patterns

**Core Components**:
- Silver layer development with intermediate data modeling
- Gold layer creation for business-ready analytics
- Aggregation and summary table generation
- SQL optimization and indexing strategies
- Data quality enforcement and validation

**Technical Focus**:
- Star schema and dimensional modeling
- SQL aggregation and window functions
- Performance optimization techniques
- Medallion architecture implementation

**Deliverable**: Complete ETL pipeline producing analytics-ready data layers

### Session 3: Git Collaboration & Version Control
**Objective**: Develop professional collaboration and reliability patterns

**Primary Focus**: Git Fundamentals
- Repository setup and basic configuration
- Branching strategies and merge techniques
- Remote collaboration workflows
- Pull request processes and code review
- Advanced Git features (rebase, stash, cherry-pick)

**Advanced Section**: Pipeline Reliability
- Idempotency patterns and checkpoint mechanisms
- Retry logic with exponential backoff
- Structured logging and error handling
- Failure scenario analysis and recovery

**Technical Focus**:
- Git workflow optimization for team environments
- Production-grade pipeline reliability patterns
- Error handling and recovery strategies

**Deliverable**: Professional Git workflow skills and understanding of production reliability patterns

### Session 4: Orchestration & Operations
**Objective**: Build production-ready data pipeline automation

**Core Components**:
- Airflow DAG development and scheduling
- Pipeline monitoring and alerting
- Infrastructure as code with Terraform
- CI/CD pipeline implementation
- Cloud deployment strategies

**Technical Focus**:
- Workflow orchestration concepts
- Infrastructure automation
- Production monitoring and maintenance
- Scalability and reliability patterns

**Deliverable**: Production-grade orchestrated data pipeline with monitoring and automation

## Learning Outcomes

**Technical Skills**:
- Database design and SQL proficiency
- Data pipeline development and optimization
- Version control and collaboration workflows
- Infrastructure automation and deployment
- Production monitoring and operations

**Professional Competencies**:
- Problem-solving approach to data engineering challenges
- Understanding of industry best practices
- Portfolio project demonstrating end-to-end capabilities
- Preparation for entry-level data engineering roles

## Prerequisites

**Technical Requirements**:
- Basic Python programming knowledge
- Understanding of database concepts
- Familiarity with command line operations
- Docker installation and basic usage

**System Requirements**:
- Local PostgreSQL installation or Docker
- Python 3.11+ environment
- Git client and configuration
- Sufficient disk space for data processing

## Usage Instructions

Each session follows this structure:
```
sessions/sessionX/
├── README.md              # Detailed session instructions
├── Notes.md               # Theoretical concepts and explanations
├── code/                  # Implementation files
├── tests/                 # Test cases and validation
├── docker/                # Container configurations
└── requirement.txt        # Python dependencies
```

Execute sessions in sequence as each builds upon previous knowledge and infrastructure.

## Disclaimer

This curriculum provides mental models and practical frameworks to accelerate data engineering learning. It prioritizes conceptual understanding and hands-on application over comprehensive academic coverage. Some sections may be dense with technical content as they reflect real-world complexity encountered in production environments.

## Acknowledgments

This learning material is created with appreciation for colleagues willing to invest in their professional development. The curriculum structure and content are designed to bridge the gap between theoretical knowledge and practical implementation, enabling learners to build confidence and competence in data engineering practices.

## Getting Started

1. Clone the repository
2. Review Session 1 prerequisites
3. Set up development environment
4. Execute sessions sequentially
5. Complete all exercises and projects
6. Build portfolio using delivered artifacts

## Support and Community

As an AWS community builder, I welcome feedback, contributions, and collaboration from the data engineering community. This initiative aims to lower barriers to entry and provide accessible pathways for professionals transitioning into data engineering roles.