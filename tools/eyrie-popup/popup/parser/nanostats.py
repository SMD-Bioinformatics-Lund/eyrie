"""NanoStats parsing functionality."""

import re
from pathlib import Path
from typing import Optional

from ..models import NanoStats


class NanoStatsParser:
    """Parser for NanoStats files."""

    def __init__(self, seqrun_path: Path):
        self.seqrun_path = seqrun_path

    def parse_nano_stats(self, directory: str, filename: str) -> Optional[NanoStats]:
        """Parse NanoStats.txt file."""
        stats_file = self.seqrun_path / directory / filename

        if not stats_file.exists():
            return None

        try:
            with open(stats_file, 'r') as f:
                content = f.read()

            # Parse the stats using regex
            stats = {}

            # Extract basic statistics
            patterns = {
                'mean_read_length': r'Mean read length:\s+([0-9,]+\.?[0-9]*)',
                'mean_read_quality': r'Mean read quality:\s+([0-9]+\.?[0-9]*)',
                'median_read_length': r'Median read length:\s+([0-9,]+\.?[0-9]*)',
                'median_read_quality': r'Median read quality:\s+([0-9]+\.?[0-9]*)',
                'number_of_reads': r'Number of reads:\s+([0-9,]+\.?[0-9]*)',
                'read_length_n50': r'Read length N50:\s+([0-9,]+\.?[0-9]*)',
                'stdev_read_length': r'STDEV read length:\s+([0-9,]+\.?[0-9]*)',
                'total_bases': r'Total bases:\s+([0-9,]+\.?[0-9]*)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = match.group(1).replace(',', '')
                    if key == 'number_of_reads':
                        stats[key] = int(float(value))
                    else:
                        stats[key] = float(value)

            # Parse quality cutoffs
            quality_cutoffs = {}
            q_pattern = r'>Q(\d+):\s+(\d+)\s+\(([0-9.]+)%\)\s+([0-9.]+)Mb'
            for match in re.finditer(q_pattern, content):
                q_level = f"Q{match.group(1)}"
                count = int(match.group(2))
                percentage = float(match.group(3))
                megabases = float(match.group(4))
                quality_cutoffs[q_level] = (count, percentage, megabases)

            return NanoStats(
                quality_cutoffs=quality_cutoffs,
                **stats
            )

        except Exception as e:
            print(f"Error parsing NanoStats file {stats_file}: {e}")
            return None
