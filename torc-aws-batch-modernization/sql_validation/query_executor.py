"""
SQL Query Executor for Settlement Validation
"""
import sqlite3
import os


def get_db_path():
    """Get database path relative to script location"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'settlement_db.db')


def get_sql_file_path():
    """Get SQL file path"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'settlement_validation.sql')


def split_sql_queries(sql_content):
    """Split SQL file into individual queries"""
    # Split by semicolon followed by newlines (end of query)
    queries = []
    current_query = []
    lines = sql_content.split('\n')

    for line in lines:
        # Skip comment-only lines at the beginning
        if line.strip().startswith('--') and not current_query:
            current_query.append(line)
        elif line.strip().startswith('--'):
            current_query.append(line)
        elif line.strip():
            current_query.append(line)
        elif current_query:
            # Empty line might indicate query separation
            if any(l.strip() and not l.strip().startswith('--') for l in current_query):
                query_text = '\n'.join(current_query)
                if 'SELECT' in query_text.upper():
                    queries.append(query_text)
            current_query = []

    # Add the last query if exists
    if current_query:
        query_text = '\n'.join(current_query)
        if 'SELECT' in query_text.upper():
            queries.append(query_text)

    return queries


def extract_query_title(query):
    """Extract title from query comments"""
    lines = query.split('\n')
    for line in lines:
        if line.strip().startswith('-- Query'):
            return line.strip()[3:].strip()
    return "Query"


def execute_query(cursor, query):
    """Execute a single query and return results"""
    # Remove comment lines for execution
    query_lines = [line for line in query.split('\n')
                   if not line.strip().startswith('--') or 'TODO' in line]
    # Remove TODO lines too
    query_lines = [line for line in query_lines if 'TODO' not in line]
    clean_query = '\n'.join(query_lines)

    try:
        cursor.execute(clean_query)
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []
        return column_names, results
    except Exception as e:
        return None, f"Error: {str(e)}"


def format_results(column_names, results):
    """Format query results as a table"""
    if not results:
        return "No results found."

    # Calculate column widths
    widths = [len(name) for name in column_names]
    for row in results:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Create separator
    separator = '-+-'.join(['-' * w for w in widths])

    # Create header
    header = ' | '.join([name.ljust(widths[i]) for i, name in enumerate(column_names)])

    # Create rows
    rows = []
    for row in results:
        rows.append(' | '.join([str(val).ljust(widths[i]) for i, val in enumerate(row)]))

    return '\n'.join([header, separator] + rows)


def main():
    """Main execution"""
    print("=== Settlement Data Quality Validation ===\n")

    # Load SQL file
    sql_file = get_sql_file_path()
    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Split into individual queries
    queries = split_sql_queries(sql_content)
    print(f"Found {len(queries)} validation queries\n")

    # Connect to database
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute each query
    for i, query in enumerate(queries, 1):
        title = extract_query_title(query)
        print(f"\n{'=' * 80}")
        print(f"{title}")
        print('=' * 80)

        column_names, results = execute_query(cursor, query)

        if column_names is None:
            print(results)  # Error message
        else:
            print(format_results(column_names, results))

    conn.close()
    print("\n=== Validation Complete ===")


if __name__ == '__main__':
    main()


