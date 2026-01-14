# Session 2 Notes: Data Modeling & Analytics

## Theoretical Concepts

### OLTP vs OLAP

**OLTP (Online Transaction Processing)**
- Purpose: Day-to-day operations and transaction management
- Characteristics:
  - Fast query processing for small transactions
  - Data integrity and consistency
  - Normalized schema (3NF) to reduce redundancy
  - High volume of read/write operations
  - Real-time data processing
- Example: E-commerce order entry system, banking transaction system
- refs: https://leapcell.io/blog/blueprint-for-digital-commerce-a-relational-database-design

**OLAP (Online Analytical Processing)**
- Purpose: Data analysis, reporting, and decision making
- Characteristics:
  - Complex queries with aggregations
  - Historical data analysis
  - Denormalized schema (Star/Snowflake) for query performance
  - High volume of read operations, low write volume
  - Batch processing
- Example: Sales reporting, trend analysis, BI dashboards

### Entity Relationship (ER) Model

![ER Diagram example](./images/ER-diagram.png)

**First Principles**
- ER model conceptualizes data as entities and relationships
- Entities represent real-world objects (Customer, Product, Transaction)
- Attributes describe entities (Customer Name, Product Price)
- Relationships define how entities interact (Customer makes Transaction)
- refs: 
  - https://www.red-gate.com/blog/how-to-use-er-diagram
  - https://medium.com/@Samietex/how-to-design-a-database-in-3-easy-steps-conceptual-logical-and-physical-modeling-3bd2a789de04

**Key Components**
- Entity: Distinct object/concept
- Attribute: Property of an entity
- Primary Key: Unique identifier for entity
- Foreign Key: References primary key of related entity
- Cardinality: Number of relationships (1:1, 1:N, N:N)
- refs: https://www.youtube.com/watch?v=8fF7Rcfcy2A

**3NF (Third Normal Form)**
- Ensures data integrity and reduces redundancy
- Rules:
  1. 1NF: All values atomic, no repeating groups
  2. 2NF: No partial dependencies (all non-key attributes depend on entire primary key)
  3. 3NF: No transitive dependencies (non-key attributes don't depend on other non-key attributes)
- refs: 
  - https://medium.com/@ajadiololade/understanding-database-normalization-a-practical-guide-with-e-commerce-examples-02c87b234a49
  - https://www.freecodecamp.org/news/database-normalization-1nf-2nf-3nf-table-examples/

### Star Schema

![star schema example](./images/star_schema.png)

**First Principles**
- Star schema optimizes query performance for analytical workloads
- Denormalized design reduces join operations
- Simpler to understand and maintain for business users
- refs:
  - https://medium.com/@manojt2501/a-step-by-step-approach-to-convert-er-models-to-effective-dimensional-models-3a21ec02e8e
  - https://medium.com/@sarahryliegasparini/your-conceptual-guide-to-building-a-star-schema-data-warehouse-3ea25ccf0fce
  - https://www.youtube.com/watch?v=mPnnygpy2lY

**Components**
- **Fact Table**: Central table containing quantitative measures
  - Contains foreign keys to dimension tables
  - Stores numeric measures (sales, quantity, revenue)
  - [High cardinality](https://www.tigerdata.com/blog/what-is-high-cardinality)
  - [Grain](https://www.ibm.com/docs/en/ida/9.1.1?topic=phase-step-identify-grain): One row per unit of analysis (e.g., daily sales by product and country)

- **Dimension Tables**: Descriptive context
  - Low cardinality, wide tables
  - Contains descriptive attributes
  - Linked to fact table via foreign keys

**Advantages**
- Faster query performance (fewer joins)
- Simpler SQL queries
- Better for business user understanding
- Easier to aggregate and filter

**Trade-offs**
- Data redundancy (storage cost)
- Potential data inconsistency
- More complex ETL to maintain

### Medallion Architecture

![medallion architecture](./images/medallion.png)

**First Principles**
- Progressive refinement of data quality and structure
- Each layer adds value through transformation and validation
- Enables data lineage and traceability. [source](https://community.databricks.com/t5/community-articles/the-medallion-architecture-why-data-layers-matter-for-modern/td-p/140825#:~:text=The%20Bronze%20layer%20operates%20on,reprocess%20it%20correctly%20from%20scratch.)

**Layers**

**Bronze Layer (Raw)**
- Purpose: Ingestion and initial storage
- Characteristics:
  - Raw data as-is from source
  - Minimal transformation (format conversion)
  - Append-only
  - High storage cost, low quality
- Use case: Data recovery, audit trail, source for reprocessing

**Silver Layer (Intermediate)**
- Purpose: Data cleaning and standardization
- Characteristics:
  - 3NF normalized structure
  - Basic validation and cleaning
  - Deduplication
  - Standardized naming conventions
- Use case: Intermediate analysis, data quality checks

**Gold Layer (Curated)**
- Purpose: Business-ready analytics
- Characteristics:
  - Star schema (denormalized)
  - Aggregated metrics
  - Business-optimized structure
  - High data quality
- Use case: BI dashboards, reporting, analytics

## Implementation Considerations

### Fact Table Design
- Define grain: What does one row represent?
- Include dimension keys (date, product, customer)
- Include measures (revenue, quantity, transactions)
- Add metadata (created_at, updated_at)

### Dimension Table Design
- Include natural key (source system ID)
- Include surrogate key (integer for joins)
- Include descriptive attributes
- Include slowly changing dimension (SCD) columns
- Type 1: Overwrite (current state only)
- Type 2: History (versioning with valid dates)

### Performance Optimization
- Indexes: Create on foreign keys and frequently filtered columns
- Partitioning: Partition large tables by date (range partitioning)
- Materialized views: Pre-compute expensive aggregations

### Data Quality
- Validate referential integrity
- Check for null/invalid values
- Monitor data volumes and row counts
- Implement reconciliation checks between layers
