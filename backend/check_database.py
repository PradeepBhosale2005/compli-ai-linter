"""Utility to verify the compliance_history SQLite database.

This script prints basic information about the database and the
expected tables: ``documents`` and ``document_rules``.

Usage: python check_database.py
"""

import os
import sqlite3
from typing import List


def check_database(db_path: str = "compliance_history.db") -> bool:
    """Check the database and print basic statistics.

    Returns True if checks complete without errors, otherwise False.
    """
    print("Checking CompliAI database...")

    if not os.path.exists(db_path):
        print("Database file not found:", db_path)
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables: List[str] = [t[0] for t in cursor.fetchall()]
        print("Tables found:", tables)

        def _count(table: str) -> int:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            return cursor.fetchone()[0]

        if "documents" in tables:
            doc_count = _count("documents")
            print("Documents stored:", doc_count)
        else:
            print("Table 'documents' not found.")
            doc_count = 0

        if "document_rules" in tables:
            rule_count = _count("document_rules")
            print("Document-specific rules:", rule_count)
        else:
            print("Table 'document_rules' not found.")
            rule_count = 0

        if doc_count > 0:
            cursor.execute(
                "SELECT id, filename, upload_date, compliance_score FROM documents ORDER BY upload_date DESC LIMIT 3"
            )
            recent_docs = cursor.fetchall()
            print("Recent documents:")
            for doc in recent_docs:
                print(f"  ID: {doc[0]}, File: {doc[1]}, Uploaded: {doc[2]}, Score: {doc[3]}")

        conn.close()
        print("Database check completed.")
        return True

    except Exception as exc:
        print("Database error:", exc)
        return False


if __name__ == "__main__":
    check_database()