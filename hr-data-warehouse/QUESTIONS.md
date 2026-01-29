# Written Questions

## Question 1: Informatica Production Workflow Design

**Question:** Describe how you would design an Informatica PowerCenter workflow to productionize this ETL pipeline. Include the key components (sources, transformations, targets) and explain how you would handle incremental loads for a nightly batch process.

**Answer:**

### Workflow Architecture Overview

The Informatica PowerCenter workflow for this HR Data Warehouse ETL pipeline would be designed as a robust, production-ready solution with proper error handling, logging, and incremental load capabilities.

### Key Components

#### 1. **Sources**
- **HRIS Source**: Flat file source definition for `hris_extract.csv`
  - Configured with appropriate data types (employee_id as integer, dates as date/time, strings as varchar)
  - Source qualifier transformation to read and validate source data
- **Payroll Source**: Flat file source definition for `payroll_extract.csv`
- **Performance Management Source**: Flat file source definition for `perf_mgmt_extract.csv`

All sources would be configured with:
- File location parameters (parameterized for different environments)
- Date format specifications
- Error handling for missing files or malformed records
- Reject files for data quality issues

#### 2. **Transformations**

**a. Source Qualifiers (SQ_HRIS, SQ_PAYROLL, SQ_PERF_MGMT)**
- Read and validate data from respective CSV files
- Apply data type conversions
- Filter out invalid records (e.g., null employee_ids)

**b. Joiner Transformations**
- **JNR_HRIS_PAYROLL**: Left outer join HRIS with Payroll on `employee_id`
  - Preserves all HRIS records (master source)
  - Handles missing payroll records gracefully
- **JNR_HRIS_PERF**: Left outer join the result with Performance Management on `employee_id`
  - Preserves all employee records from HRIS
  - Handles missing performance records

**c. Expression Transformations**
- **EXP_DEFAULTS**: Set default values for optional fields
  - `bonus = IIF(ISNULL(bonus), 0, bonus)` - Default bonus to 0 if null
  - Handle other optional fields similarly
- **EXP_CALCULATIONS**: Calculate derived fields
  - `total_compensation = base_salary + bonus` (with null handling)
  - `performance_category = IIF(ISNULL(performance_score), NULL, 
     IIF(performance_score >= 4.5, 'Excellent',
     IIF(performance_score >= 4.0, 'Very Good',
     IIF(performance_score >= 3.5, 'Good',
     IIF(performance_score >= 3.0, 'Satisfactory', 'Needs Improvement')))))`
  - `load_timestamp = SYSDATE` - Current timestamp for audit trail

**d. Filter Transformation**
- **FIL_VALID_RECORDS**: Filter records that meet data quality requirements
  - Ensure required fields (employee_id, full_name, department, base_salary) are not null
  - Reject records that fail validation to error table

**e. Router Transformation (Optional)**
- Route records based on data quality or business rules
- Separate active vs. inactive employees if needed for different processing

**f. Update Strategy Transformation**
- Configure for insert/update logic if implementing incremental loads
- Use `DD_INSERT` for new records, `DD_UPDATE` for changed records

#### 3. **Targets**

**a. Primary Target: employee_analytics Table**
- SQL Server/Oracle target definition mapped to `employee_analytics` table
- Column mappings from transformation output
- Configure connection to target database with proper credentials

**b. Error/Reject Tables (Optional)**
- `employee_analytics_rejects`: Store records that fail validation
- `employee_analytics_errors`: Store records with transformation errors
- Enable audit and troubleshooting

**c. Control Tables (for Incremental Loads)**
- `etl_control_table`: Track last successful run date/time
- `etl_run_log`: Log each ETL execution with status, record counts, errors

### Incremental Load Strategy for Nightly Batch Process

#### Approach 1: Timestamp-Based Incremental Load (Recommended)

1. **Control Table Setup**
   - Create `etl_control_table` with columns: `last_run_timestamp`, `last_successful_run`, `status`
   - Initialize with baseline load date

2. **Pre-Session SQL (in Workflow)**
   - Query control table to get `last_run_timestamp`
   - Store in workflow variable `$$LAST_RUN_DATE`

3. **Source Filtering**
   - Add filter conditions in Source Qualifiers:
     - HRIS: `hire_date > $$LAST_RUN_DATE OR employment_status_changed_date > $$LAST_RUN_DATE`
     - Payroll: `salary_update_date > $$LAST_RUN_DATE OR bonus_update_date > $$LAST_RUN_DATE`
     - Performance: `review_date > $$LAST_RUN_DATE`
   - **Note**: This assumes source systems have change tracking columns. If not available, use Approach 2.

4. **Change Detection**
   - Use Lookup transformation to check if `employee_id` exists in target
   - If exists, compare key fields (salary, bonus, performance_score) to detect changes
   - Route to Update Strategy: `DD_UPDATE` for changed records, `DD_INSERT` for new records

5. **Post-Session SQL**
   - Update control table: `UPDATE etl_control_table SET last_run_timestamp = SYSDATE, status = 'SUCCESS'`
   - Insert into run log table with statistics

#### Approach 2: Full Load with Truncate (Simpler, if change tracking unavailable)

1. **Pre-Session SQL**
   - `TRUNCATE TABLE employee_analytics` - Clear existing data (prevents duplicates)

2. **Load Process**
   - Load all records from source systems
   - No change detection needed

3. **Post-Session SQL**
   - Update control table with run statistics
   - Log execution details

#### Approach 3: Change Data Capture (CDC) - Advanced

1. **Source System Integration**
   - Implement CDC at source systems (if supported)
   - Use Informatica CDC capabilities to capture only changed records

2. **Merge Strategy**
   - Use Informatica's Merge transformation or SQL MERGE statement
   - Update existing records, insert new ones

### Workflow Design Best Practices

1. **Workflow Structure**
   - **Start Task**: Initialize variables, check prerequisites
   - **Session Tasks**: Separate sessions for each major transformation stage
   - **Command Task**: Execute pre/post SQL scripts
   - **Email Task**: Send notifications on success/failure
   - **Decision Task**: Conditional logic based on session status

2. **Error Handling**
   - Configure session properties: `Stop on errors = FALSE` initially
   - Implement error handling workflow with retry logic
   - Route failed records to reject tables
   - Send alerts for critical failures

3. **Performance Optimization**
   - Use partition points for parallel processing
   - Configure buffer sizes appropriately
   - Implement index strategies on target table
   - Use bulk loading where possible

4. **Scheduling**
   - Schedule workflow to run nightly (e.g., 2:00 AM)
   - Configure dependencies (wait for source file availability)
   - Implement file watcher or polling mechanism for source files

5. **Monitoring and Logging**
   - Enable detailed logging at session level
   - Track metrics: records read, written, rejected, errors
   - Integrate with monitoring tools (Informatica Monitor, external dashboards)
   - Generate daily ETL reports

6. **Data Quality**
   - Implement data quality rules in Expression transformations
   - Validate referential integrity
   - Check for duplicates before loading
   - Generate data quality scorecards

### Example Workflow Flow

```
START
  ↓
[Command Task: Pre-Session - Get Last Run Date]
  ↓
[Session: Extract and Transform HRIS Data]
  ↓
[Session: Extract and Transform Payroll Data]
  ↓
[Session: Extract and Transform Performance Data]
  ↓
[Session: Join and Merge All Sources]
  ↓
[Session: Apply Business Rules and Calculations]
  ↓
[Session: Load to Target (Incremental/Full)]
  ↓
[Command Task: Post-Session - Update Control Tables]
  ↓
[Email Task: Send Success Notification]
  ↓
END
```

### Handling Edge Cases

1. **Missing Source Files**: Implement file existence check in pre-session, fail gracefully with notification
2. **Data Type Mismatches**: Use data type conversion functions in Expression transformations
3. **Duplicate Employee IDs**: Use Aggregator or Rank transformation to handle duplicates
4. **Large Data Volumes**: Implement partitioning and parallel processing
5. **Network/Connection Issues**: Implement retry logic and connection pooling

This design ensures a production-ready, maintainable, and scalable ETL solution that can handle the nightly batch processing requirements while maintaining data quality and providing proper audit trails.
