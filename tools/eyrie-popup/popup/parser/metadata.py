"""Parser for sample metadata from TSV/CSV files."""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..models.data import SampleMetadata


class MetadataParser:
    """Parse sample metadata from TSV/CSV files."""

    COLUMN_MAPPINGS = {
        'sample_id': ['sample_id', 'sample', 'id', 'sample_name'],
        'sample_type': ['sample_type', 'type', 'sample_category'],
        'tissue': ['tissue', 'sample_tissue', 'tissue_type'],
        'dilution': ['dilution', 'sample_dilution'],
        'library_concentration': ['library_concentration', 'lib_concentration', 'concentration', 'library_conc'],
        'multiple_finds': ['multiple_finds', 'multiple_bacteria', 'multi_finds'],
        'spike_concentration': ['spike_concentration', 'spike_conc', 'spike'],
        'sanger_expected_species': ['sanger_expected_species', 'expected_species', 'sanger_species'],
        'extraction_kit': ['extraction_kit', 'dna_extraction_kit', 'extraction_method', 'dna_kit'],
        'library_prep_kit': ['library_prep_kit', 'lib_prep_kit', 'library_preparation_kit', 'prep_kit']
    }

    def __init__(self, file_path: Union[str, Path]):
        """Initialize metadata parser with file path."""
        self.file_path = Path(file_path)

    def parse(self) -> Dict[str, SampleMetadata]:
        """Parse metadata file and return dictionary of sample_id -> SampleMetadata."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.file_path}")

        delimiter = self._detect_delimiter()

        metadata_dict = {}
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            normalized_fieldnames = self._normalize_fieldnames(reader.fieldnames)

            for row_num, row in enumerate(reader, start=2):
                try:
                    normalized_row = {normalized_fieldnames.get(k, k): v for k, v in row.items()}

                    sample_id = self._get_sample_id(normalized_row)
                    if not sample_id:
                        print(f"Warning: No sample_id found in row {row_num}, skipping")
                        continue

                    metadata = self._parse_row_metadata(normalized_row)
                    metadata_dict[sample_id] = metadata

                except Exception as e:
                    print(f"Warning: Error parsing row {row_num}: {e}")
                    continue

        return metadata_dict

    def _detect_delimiter(self) -> str:
        """Detect if file uses tabs or commas as delimiter."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)

        try:
            sniffer = csv.Sniffer()
            # Only allow tabs and commas as valid delimiters
            delimiter = sniffer.sniff(sample, delimiters='\t,').delimiter

            # Double-check that the detected delimiter is actually tab or comma
            if delimiter not in ['\t', ',']:
                # Fallback: count occurrences of tabs vs commas in the first line
                first_line = sample.split('\n')[0] if sample else ''
                tab_count = first_line.count('\t')
                comma_count = first_line.count(',')

                if tab_count > comma_count:
                    return '\t'
                elif comma_count > 0:
                    return ','
                else:
                    return '\t'  # Default to tab

            return delimiter
        except:
            # Fallback: count occurrences of tabs vs commas in the first line
            try:
                first_line = sample.split('\n')[0] if sample else ''
                tab_count = first_line.count('\t')
                comma_count = first_line.count(',')

                if tab_count > comma_count:
                    return '\t'
                elif comma_count > 0:
                    return ','
                else:
                    return '\t'
            except:
                return '\t'

    def _normalize_fieldnames(self, fieldnames: List[str]) -> Dict[str, str]:
        """Normalize field names to standard column names."""
        normalized = {}

        for field in fieldnames:
            if not field:
                continue

            field_lower = field.strip().lower()

            for standard_col, variations in self.COLUMN_MAPPINGS.items():
                if field_lower in [v.lower() for v in variations]:
                    normalized[field] = standard_col
                    break
            else:
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
        def get_value(key: str) -> Optional[str]:
            value = row.get(key, '').strip()
            return value if value else None

        return SampleMetadata(
            sample_type=get_value('sample_type'),
            tissue=get_value('tissue'),
            dilution=get_value('dilution'),
            library_concentration=get_value('library_concentration'),
            multiple_finds=get_value('multiple_finds'),
            spike_concentration=get_value('spike_concentration'),
            sanger_expected_species=get_value('sanger_expected_species'),
            extraction_kit=get_value('extraction_kit'),
            library_prep_kit=get_value('library_prep_kit')
        )


def validate_metadata_file(file_path: Union[str, Path]) -> tuple[bool, List[str]]:
    """Validate metadata file format and return status and error messages."""
    errors = []
    file_path = Path(file_path)

    if not file_path.exists():
        return False, [f"File does not exist: {file_path}"]

    try:
        parser = MetadataParser(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            delimiter = parser._detect_delimiter()
            reader = csv.DictReader(f, delimiter=delimiter)

            fieldnames = reader.fieldnames or []
            if not fieldnames:
                errors.append("No column headers found")
                return False, errors

            normalized_fieldnames = parser._normalize_fieldnames(fieldnames)
            if 'sample_id' not in normalized_fieldnames.values():
                sample_id_variations = ", ".join(parser.COLUMN_MAPPINGS['sample_id'])
                errors.append(f"No sample ID column found. Expected one of: {sample_id_variations}")

            # Validate constrained fields
            for row_num, row in enumerate(reader, start=2):
                normalized_row = {normalized_fieldnames.get(k, k): v for k, v in row.items()}

                # Validate sample_type
                sample_type = normalized_row.get('sample_type', '').strip()
                if sample_type and sample_type not in ['validation', 'patient', 'negative control', 'positive control']:
                    errors.append(f"Row {row_num}: Invalid sample_type '{sample_type}'. Must be one of: validation, patient, negative control, positive control")

                # Validate dilution
                dilution = normalized_row.get('dilution', '').strip()
                if dilution and dilution not in ['1:1', '1:10']:
                    errors.append(f"Row {row_num}: Invalid dilution '{dilution}'. Must be one of: 1:1, 1:10")

                # Validate spike_concentration
                spike_concentration = normalized_row.get('spike_concentration', '').strip()
                if spike_concentration and spike_concentration not in ['IC3', 'IC4']:
                    errors.append(f"Row {row_num}: Invalid spike_concentration '{spike_concentration}'. Must be one of: IC3, IC4")

                if row_num > 11:  # Limit validation to first 10 rows for performance
                    break

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return len(errors) == 0, errors
