#!/usr/bin/env python3
"""
MongoDB migration script to rename 'metadata.tissue' to 'metadata.material' in all sample documents.

Usage:
    # Dry run (default) - shows what would be changed without making changes
    python migrate_tissue_to_material.py

    # Execute the migration
    python migrate_tissue_to_material.py --execute

    # With custom MongoDB connection
    python migrate_tissue_to_material.py --mongo-uri "mongodb://localhost:27017" --database "eyrie" --execute
"""

import argparse
import os
from pymongo import MongoClient


def migrate_tissue_to_material(mongo_uri: str, database: str, dry_run: bool = True):
    """Rename metadata.tissue to metadata.material in all sample documents."""

    client = MongoClient(mongo_uri)
    db = client[database]
    samples_collection = db.samples

    # Find all documents with metadata.tissue field
    query = {"metadata.tissue": {"$exists": True}}
    documents_to_update = samples_collection.count_documents(query)

    print(f"Database: {database}")
    print(f"Documents with 'metadata.tissue' field: {documents_to_update}")

    if documents_to_update == 0:
        print("No documents to migrate. Migration complete.")
        return

    if dry_run:
        print("\n[DRY RUN] Would rename 'metadata.tissue' to 'metadata.material' in the following documents:")

        # Show sample of documents that would be affected
        cursor = samples_collection.find(query, {"sample_id": 1, "metadata.tissue": 1}).limit(10)
        for doc in cursor:
            sample_id = doc.get("sample_id", "unknown")
            tissue_value = doc.get("metadata", {}).get("tissue", "")
            print(f"  - sample_id: {sample_id}, tissue: '{tissue_value}' -> material: '{tissue_value}'")

        if documents_to_update > 10:
            print(f"  ... and {documents_to_update - 10} more documents")

        print("\nTo execute the migration, run with --execute flag")
    else:
        print("\n[EXECUTING] Renaming 'metadata.tissue' to 'metadata.material'...")

        # Perform the rename operation
        result = samples_collection.update_many(
            query,
            {"$rename": {"metadata.tissue": "metadata.material"}}
        )

        print(f"Matched documents: {result.matched_count}")
        print(f"Modified documents: {result.modified_count}")
        print("Migration complete.")

    client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate metadata.tissue to metadata.material in MongoDB samples collection"
    )
    parser.add_argument(
        "--mongo-uri",
        default=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        help="MongoDB connection URI (default: from MONGO_URI env var or mongodb://localhost:27017)"
    )
    parser.add_argument(
        "--database",
        default=os.getenv("MONGO_DB", "eyrie"),
        help="MongoDB database name (default: from MONGO_DB env var or eyrie)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the migration (default is dry run)"
    )

    args = parser.parse_args()

    migrate_tissue_to_material(
        mongo_uri=args.mongo_uri,
        database=args.database,
        dry_run=not args.execute
    )


if __name__ == "__main__":
    main()
