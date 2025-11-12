"""Parser for sample metadata from TSV/CSV files."""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..models.data import SampleMetadata


class MetadataParser:
    """Parse sample metadata from TSV/CSV files."""

    # Standard column name mappings (handles variations in column names)
    COLUMN_MAPPINGS = {
        'sample_id': ['sample_id', 'sample', 'id', 'sample_name'],
        'sample_type': ['sample_type', 'type', 'sample_category'],
        'tissue': ['tissue', 'sample_tissue', 'tissue_type'],
        'dilution': ['dilution', 'sample_dilution'],
        'library_concentration': ['library_concentration', 'lib_concentration', 'concentration', 'library_conc'],
        'multiple_finds': ['multiple_finds', 'multiple_bacteria', 'multi_finds'],
        'other_comments': ['other_comments', 'comments', 'notes', 'other_notes'],
        'qc_comment': ['qc_comment', 'qc_comments', 'quality_comment'],
        'sanger_expected_species': ['sanger_expected_species', 'expected_species', 'sanger_species']
    }

    def __init__(self, file_path: Union[str, Path]):
        """Initialize metadata parser with file path."""
        self.file_path = Path(file_path)

    def parse(self) -> Dict[str, SampleMetadata]:
        """Parse metadata file and return dictionary of sample_id -> SampleMetadata."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.file_path}")

        # Detect delimiter
        delimiter = self._detect_delimiter()

        # Parse the file
        metadata_dict = {}
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            # Normalize column names
            normalized_fieldnames = self._normalize_fieldnames(reader.fieldnames)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                try:
                    # Normalize row keys
                    normalized_row = {normalized_fieldnames.get(k, k): v for k, v in row.items()}

                    # Extract sample ID
                    sample_id = self._get_sample_id(normalized_row)
                    if not sample_id:
                        print(f"Warning: No sample_id found in row {row_num}, skipping")
                        continue

                    # Parse metadata
                    metadata = self._parse_row_metadata(normalized_row)
                    metadata_dict[sample_id] = metadata

                except Exception as e:
                    print(f"Warning: Error parsing row {row_num}: {e}")
                    continue

        return metadata_dict

    def _detect_delimiter(self) -> str:
        """Detect if file uses tabs or commas as delimiter."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to detect delimiter
            sample = f.read(1024)

        # Use csv.Sniffer to detect delimiter
        try:
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters='\t,').delimiter
            return delimiter
        except:
            # Default to tab if detection fails
            return '\t'

    def _normalize_fieldnames(self, fieldnames: List[str]) -> Dict[str, str]:
        """Normalize field names to standard column names."""
        normalized = {}

        for field in fieldnames:
            if not field:
                continue

            field_lower = field.strip().lower()

            # Find matching standard column
            for standard_col, variations in self.COLUMN_MAPPINGS.items():
                if field_lower in [v.lower() for v in variations]:
                    normalized[field] = standard_col
                    break
            else:
                # Keep original name if no mapping found
                normalized[field] = field_lower

        return normalized

    def _get_sample_id(self, row: Dict[str, str]) -> Optional[str]:
        """Extract sample ID from row."""
        for possible_key in ['sample_id', 'sample', 'id', 'sample_name']:
            if possible_key in row and row[possible_key]:
                return row[possible_key].strip()
        return None

    def _parse_row_metadata(self, row: Dict[str, str]) -> SampleMetadata:
        """Parse a single row into SampleMetadata."""
        # Extract metadata fields, handling empty strings as None
        def get_value(key: str) -> Optional[str]:
            value = row.get(key, '').strip()
            return value if value else None

        return SampleMetadata(
            sample_type=get_value('sample_type'),
            tissue=get_value('tissue'),
            dilution=get_value('dilution'),
            library_concentration=get_value('library_concentration'),
            multiple_finds=get_value('multiple_finds'),
            other_comments=get_value('other_comments'),
            qc_comment=get_value('qc_comment'),
            sanger_expected_species=get_value('sanger_expected_species')
        )


def validate_metadata_file(file_path: Union[str, Path]) -> tuple[bool, List[str]]:
    """Validate metadata file format and return status and error messages."""
    errors = []
    file_path = Path(file_path)

    if not file_path.exists():
        return False, [f"File does not exist: {file_path}"]

    try:
        parser = MetadataParser(file_path)

        # Try to parse a few rows to validate format
        with open(file_path, 'r', encoding='utf-8') as f:
            delimiter = parser._detect_delimiter()
            reader = csv.DictReader(f, delimiter=delimiter)

            fieldnames = reader.fieldnames or []
            if not fieldnames:
                errors.append("No column headers found")
                return False, errors

            # Check for sample_id column
            normalized_fieldnames = parser._normalize_fieldnames(fieldnames)
            if 'sample_id' not in normalized_fieldnames.values():
                sample_id_variations = ", ".join(parser.COLUMN_MAPPINGS['sample_id'])
                errors.append(f"No sample ID column found. Expected one of: {sample_id_variations}")

            # Validate sample_type values if column exists
            if 'sample_type' in normalized_fieldnames.values():
                for row_num, row in enumerate(reader, start=2):
                    normalized_row = {normalized_fieldnames.get(k, k): v for k, v in row.items()}
                    sample_type = normalized_row.get('sample_type', '').strip()
                    if sample_type and sample_type not in ['validation', 'patient', 'negative', 'positive']:
                        errors.append(f"Row {row_num}: Invalid sample_type '{sample_type}'. Must be one of: validation, patient, negative, positive")

                    # Stop after checking 10 rows to avoid too many error messages
                    if row_num > 11:
                        break

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return len(errors) == 0, errors