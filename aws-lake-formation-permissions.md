# AWS Lake Formation Permissions - Solution Guide

## Question:
A data lake administrator enabled Lake Formation permissions, but now users cannot crawl or access data as they did previously using AWS Glue. What is the most likely cause?

## Answer Analysis:

**Important Note:** None of the provided options directly state the most common cause, which is that **users need explicit Lake Formation permissions granted** after enabling Lake Formation. However, based on AWS Lake Formation behavior, the answer is likely related to **permission migration**.

## Understanding the Problem:

### What Happens When Lake Formation Permissions Are Enabled:

1. **Lake Formation takes over access control**: When you enable Lake Formation permissions, it supersedes IAM policies for Glue Data Catalog access
2. **IAM policies are bypassed**: Users who previously had access via IAM policies lose that access
3. **Explicit Lake Formation permissions required**: Users must be granted permissions through Lake Formation

### The Root Cause:

When Lake Formation permissions are enabled, **IAM-based access is disabled** for the Glue Data Catalog. Users need:
- Lake Formation database permissions
- Lake Formation table permissions  
- Lake Formation column-level permissions (if needed)

## Analysis of Each Option:

### Option A: "Use Redshift Spectrum to control access and then federate to Lake Formation"
- ❌ **Incorrect**: This is a solution/workaround, not the cause
- ❌ Redshift Spectrum is for querying S3 data, not related to Glue crawling issues
- ❌ Doesn't address the root cause

### Option B: "Grant Lake Formation permissions at the column level and create a resource link in the recipient account"
- ⚠️ **Partially relevant**: This describes a solution (granting permissions)
- ⚠️ However, it's about column-level permissions and cross-account sharing
- ⚠️ The question asks for the **cause**, not the solution
- ⚠️ Cross-account resource links are only needed for cross-account scenarios

### Option C: "The Glue Data Catalog is not synced with the S3 inventory"
- ❌ **Incorrect**: This doesn't make technical sense
- ❌ S3 Inventory is a feature for listing S3 objects, not something that syncs with Glue Data Catalog
- ❌ Glue crawlers read S3 directly; there's no "sync" with S3 inventory
- ❌ This is not a real AWS concept

### Option D: "Use AWS Glue table-level IAM policies to manage access"
- ❌ **Incorrect**: This is the OLD method that no longer works
- ❌ When Lake Formation is enabled, IAM policies are bypassed
- ❌ This suggests using the method that was disabled, which is wrong

### Option E: "Share the entire database using Lake Formation cross-account resource link"
- ❌ **Incorrect**: This is a solution for cross-account sharing
- ❌ Only relevant if this is a cross-account scenario (not mentioned)
- ❌ Doesn't address the root cause for same-account access issues

## The Actual Root Cause (Not Explicitly Stated):

The most likely cause is that **users don't have Lake Formation permissions granted** after enabling Lake Formation permissions. When Lake Formation takes over access control:

1. IAM policies are ignored
2. Users lose their previous IAM-based access
3. They need explicit Lake Formation grants

## Solution Steps:

### 1. Grant Database Permissions:
```sql
-- Grant access to database
GRANT SELECT ON DATABASE my_database TO 'arn:aws:iam::123456789012:user/analyst';
```

### 2. Grant Table Permissions:
```sql
-- Grant access to specific tables
GRANT SELECT ON TABLE my_database.my_table TO 'arn:aws:iam::123456789012:user/analyst';
```

### 3. Grant Crawler Permissions:
```sql
-- Grant CREATE_TABLE permission for crawlers
GRANT CREATE_TABLE ON DATABASE my_database TO 'arn:aws:iam::123456789012:role/glue-crawler-role';
```

### 4. Use Lake Formation Console:
- Navigate to Lake Formation → Permissions
- Grant database/table permissions to users/roles
- Ensure Glue crawler roles have CREATE_TABLE permissions

## Migration Best Practices:

1. **Before enabling Lake Formation**:
   - Document all existing IAM policies
   - Identify all users/roles that need access
   - Plan permission migration

2. **After enabling Lake Formation**:
   - Grant equivalent permissions in Lake Formation
   - Test access for all users
   - Update Glue crawler IAM roles with Lake Formation permissions

3. **For Glue Crawlers**:
   - Grant CREATE_TABLE permission on databases
   - Grant SELECT permission on source tables (if reading existing data)
   - Ensure S3 bucket permissions are still in place

## Common Issues:

1. **Glue Crawlers fail**: Need CREATE_TABLE permission in Lake Formation
2. **Users can't query**: Need SELECT permission on tables/databases
3. **Cross-account access broken**: Need resource links and permissions
4. **IAM policies not working**: This is expected - Lake Formation supersedes IAM

## Answer Selection:

Given the options provided, **none directly state the root cause**. However, if forced to choose:

- **Option B** is closest to the solution (granting permissions), though it's phrased as a solution rather than a cause
- **Option C** is clearly incorrect (not a real concept)
- **Option D** is incorrect (suggests using the old method)
- **Options A and E** are solutions for specific scenarios, not the general cause

**Most likely answer based on AWS documentation**: The issue is that **users need Lake Formation permissions granted**, which is closest to **Option B** (though it's phrased as a solution).

## Summary:

When Lake Formation permissions are enabled, IAM policies are bypassed and users lose access. They need explicit Lake Formation permissions granted. The most common fix is to grant database and table permissions in Lake Formation, which is closest to what Option B describes (though it focuses on column-level and cross-account, which may not be necessary for all cases).
