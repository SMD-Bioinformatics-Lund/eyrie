"""Parser for sequencing run metadata from markdown report files."""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class SeqrunMetadataParser:
    """Parser for extracting JSON metadata from markdown report files."""

    def parse(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse sequencing run metadata from markdown report file.

        Args:
            file_path: Path to the markdown report file

        Returns:
            Dictionary containing parsed metadata fields, or None if parsing fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract JSON from markdown - look for first JSON block
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if not json_match:
                print(f"⚠ Warning: No JSON object found in {file_path}")
                return None

            json_str = json_match.group(0)
            metadata = json.loads(json_str)

            # Validate and parse exp_start_time format if present
            if 'exp_start_time' in metadata:
                try:
                    # Parse ISO string with timezone handling
                    dt_string = metadata['exp_start_time']
                    # Handle ISO string with or without 'Z' suffix
                    if dt_string.endswith('Z'):
                        dt_string = dt_string[:-1] + '+00:00'
                    metadata['exp_start_time'] = dt_string
                except (ValueError, AttributeError) as e:
                    print(f"⚠ Warning: Could not parse exp_start_time: {metadata.get('exp_start_time')} - {e}")
                    metadata['exp_start_time'] = None

            return metadata

        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return None

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate that required fields are present in metadata.

        Args:
            metadata: Parsed metadata dictionary

        Returns:
            True if metadata is valid, False otherwise
        """
        if not metadata:
            return False

        # Check for key fields that should be present
        required_fields = ['device_id', 'flow_cell_id']
        optional_but_important = ['exp_start_time', 'protocol_group_id', 'hostname']

        missing_required = [field for field in required_fields if field not in metadata or metadata[field] is None]
        if missing_required:
            print(f"⚠ Warning: Missing required fields: {missing_required}")
            return False

        missing_optional = [field for field in optional_but_important if field not in metadata or metadata[field] is None]
        if missing_optional:
            print(f"ℹ Note: Missing optional fields: {missing_optional}")

        return True
