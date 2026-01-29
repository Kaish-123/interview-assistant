# Apache Hudi Merge on Read (MOR) Optimization - Solution Guide

## Question:
Your real-time analytics dashboard queries an Apache Hudi Merge on Read (MOR) table every five seconds, but query performance degrades as the number of logs increases. What is the best way to optimize read latency?

## Answer: **E) Run frequent compactions to reduce log file sizes**

## Explanation:

### Why Option E is Correct:

**Compaction** is the process of merging log files (delta files) into base Parquet files in MOR tables. This is the **primary mechanism** for optimizing read performance in MOR tables:

1. **Reduces file count**: Compaction merges multiple log files into base Parquet files, reducing the number of files that need to be read and merged during queries
2. **Improves read latency**: Fewer files mean faster query execution
3. **Maintains data freshness**: Compaction preserves all data while optimizing storage
4. **Automated process**: Hudi provides automatic compaction policies that can be configured

### How Compaction Works:

```
Before Compaction:
- Base Parquet file (100 records)
- Log file 1 (10 updates)
- Log file 2 (15 updates)
- Log file 3 (20 updates)
→ Query must merge 4 files

After Compaction:
- Base Parquet file (145 records - merged)
→ Query reads only 1 file
```

### Configuration Example:

```properties
# Enable automatic compaction
hoodie.compact.inline=true
hoodie.compact.inline.max.delta.commits=5

# Compaction strategy
hoodie.compact.strategy=org.apache.hudi.table.action.compact.strategy.LogFileSizeBasedCompactionStrategy

# Schedule compaction
hoodie.compact.schedule.inline=true
```

### Why Other Options Are Incorrect:

**A) Disable Hudi's incremental queries to avoid complexity**
- ❌ Doesn't address the root cause (accumulating log files)
- ❌ Disabling features doesn't optimize performance
- ❌ Incremental queries are useful for many use cases

**B) Manually merge logs before running each query**
- ❌ Not scalable for queries every 5 seconds
- ❌ Manual process is error-prone and time-consuming
- ❌ Doesn't leverage Hudi's built-in compaction capabilities
- ❌ Not practical for production systems

**C) Use read.optimized mode to read only base Parquet files**
- ❌ Returns stale data (doesn't include latest updates from log files)
- ❌ Defeats the purpose of MOR tables (real-time updates)
- ❌ For real-time analytics, you need the latest data
- ❌ Not suitable for a dashboard querying every 5 seconds

**D) Switch to Copy on Write (COW) mode for better read performance**
- ❌ This is a workaround, not a solution for MOR optimization
- ❌ COW has worse write performance (slower writes)
- ❌ The question asks how to optimize MOR, not switch table types
- ❌ MOR is chosen for fast writes; switching defeats that purpose

## Understanding MOR vs COW:

### Merge on Read (MOR):
- **Writes**: Fast (writes to log files)
- **Reads**: Slower (must merge base + logs)
- **Use case**: High write throughput, eventual consistency acceptable
- **Solution**: Frequent compaction to optimize reads

### Copy on Write (COW):
- **Writes**: Slower (rewrites entire Parquet files)
- **Reads**: Fast (read Parquet files directly)
- **Use case**: Read-heavy workloads, immediate consistency required

## Best Practices for MOR Optimization:

1. **Enable automatic compaction**:
   ```properties
   hoodie.compact.inline=true
   hoodie.compact.inline.max.delta.commits=5
   ```

2. **Configure compaction strategy**:
   - `LogFileSizeBasedCompactionStrategy`: Based on log file sizes
   - `BoundedIOCompactionStrategy`: Based on I/O bounds
   - `UnBoundedCompactionStrategy`: Compact all log files

3. **Set appropriate compaction schedule**:
   ```properties
   # Compact after every 5 commits
   hoodie.compact.inline.max.delta.commits=5
   ```

4. **Monitor compaction metrics**:
   - Track compaction lag
   - Monitor read latency improvements
   - Adjust compaction frequency based on workload

## Example Spark Configuration:

```scala
val hudiOptions = Map(
  "hoodie.table.name" -> "analytics_table",
  "hoodie.table.type" -> "MERGE_ON_READ",
  "hoodie.datasource.write.recordkey.field" -> "id",
  "hoodie.datasource.write.partitionpath.field" -> "date",
  
  // Compaction configuration
  "hoodie.compact.inline" -> "true",
  "hoodie.compact.inline.max.delta.commits" -> "5",
  "hoodie.compact.schedule.inline" -> "true"
)
```

## Summary:

The correct solution is **E) Run frequent compactions**. Compaction is the standard and recommended way to optimize read latency in MOR tables by reducing the number of log files that need to be merged during queries. This can be automated using Hudi's built-in compaction policies, making it practical for production systems with frequent queries.
