"""Parser for pipeline execution trace TSV files."""

import csv
from pathlib import Path
from typing import Dict, Any, Optional
from .pipeline_base import BasePipelineParser


class ExecutionTraceParser(BasePipelineParser):
    """Parser for pipeline execution trace TSV files (execution_trace_*.txt)."""

    def __init__(self):
        super().__init__()

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse duration string to seconds.

        Args:
            duration_str: Duration in format like "4s", "14.6s", "39.8s"

        Returns:
            Duration in seconds as integer, or None if parsing fails
        """
        try:
            if not duration_str or duration_str == "0ms":
                return 0

            duration_str = duration_str.strip()

            if duration_str.endswith('s'):
                return int(float(duration_str[:-1]))
            elif duration_str.endswith('ms'):
                return int(float(duration_str[:-2]) / 1000)
            elif duration_str.endswith('m'):
                return int(float(duration_str[:-1]) * 60)
            elif duration_str.endswith('h'):
                return int(float(duration_str[:-1]) * 3600)
            else:
                # Try to parse as float seconds
                return int(float(duration_str))
        except (ValueError, AttributeError):
            return None

    def _parse_memory(self, memory_str: str) -> Optional[float]:
        """
        Parse memory string to MB.

        Args:
            memory_str: Memory in format like "2.2 MB", "1 GB", "87 MB"

        Returns:
            Memory in MB as float, or None if parsing fails
        """
        try:
            if not memory_str:
                return None

            memory_str = memory_str.strip()
            parts = memory_str.split()

            if len(parts) != 2:
                return None

            value = float(parts[0])
            unit = parts[1].upper()

            if unit == "MB":
                return value
            elif unit == "GB":
                return value * 1024
            elif unit == "KB":
                return value / 1024
            else:
                return None
        except (ValueError, IndexError):
            return None

    def _parse_percentage(self, percentage_str: str) -> Optional[float]:
        """
        Parse percentage string to float.

        Args:
            percentage_str: Percentage like "46.2%", "135.3%"

        Returns:
            Percentage as float, or None if parsing fails
        """
        try:
            if not percentage_str or not percentage_str.endswith('%'):
                return None
            return float(percentage_str[:-1])
        except ValueError:
            return None

    def parse(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse pipeline execution trace TSV file.

        Args:
            file_path: Path to the execution_trace_*.txt file

        Returns:
            Parsed execution trace data, or None if parsing fails
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Execution trace file not found: {file_path}")
                return None

            tasks = []
            total_duration = 0
            max_memory = 0
            total_cpu_time = 0

            with open(file_path, 'r') as f:
                reader = csv.DictReader(f, delimiter='\t')

                for row in reader:
                    task_data = {
                        'task_id': row.get('task_id'),
                        'hash': row.get('hash'),
                        'native_id': row.get('native_id'),
                        'name': row.get('name', '').replace('GMS_TRANA:TRANA:', ''),
                        'status': row.get('status'),
                        'exit_code': int(row.get('exit', 0)) if row.get('exit', '').isdigit() else 0,
                        'submit_time': row.get('submit'),
                        'duration_seconds': self._parse_duration(row.get('duration', '')),
                        'realtime_seconds': self._parse_duration(row.get('realtime', '')),
                        'cpu_percentage': self._parse_percentage(row.get('%cpu', '')),
                        'peak_memory_mb': self._parse_memory(row.get('peak_rss', '')),
                        'peak_vmem_mb': self._parse_memory(row.get('peak_vmem', '')),
                        'read_chars': row.get('rchar'),
                        'write_chars': row.get('wchar')
                    }

                    tasks.append(task_data)

                    # Calculate aggregates
                    if task_data['duration_seconds']:
                        total_duration += task_data['duration_seconds']

                    if task_data['peak_memory_mb']:
                        max_memory = max(max_memory, task_data['peak_memory_mb'])

                    if task_data['realtime_seconds']:
                        total_cpu_time += task_data['realtime_seconds']

            # Calculate summary statistics
            completed_tasks = [t for t in tasks if t['status'] == 'COMPLETED']
            failed_tasks = [t for t in tasks if t['status'] != 'COMPLETED']

            avg_duration = total_duration / len(completed_tasks) if completed_tasks else 0
            avg_memory = sum(t['peak_memory_mb'] for t in tasks if t['peak_memory_mb']) / len(tasks)

            result = {
                'tasks': tasks,
                'summary': {
                    'total_tasks': len(tasks),
                    'completed_tasks': len(completed_tasks),
                    'failed_tasks': len(failed_tasks),
                    'total_duration_seconds': total_duration,
                    'total_cpu_time_seconds': total_cpu_time,
                    'max_memory_mb': max_memory,
                    'avg_duration_seconds': int(avg_duration),
                    'avg_memory_mb': round(avg_memory, 1)
                },
                'parsed_at': self._get_current_timestamp()
            }

            self.logger.info(f"Successfully parsed {len(tasks)} execution trace tasks")
            return result

        except Exception as e:
            self.logger.error(f"Error parsing execution trace file {file_path}: {e}")
            return None

    def validate_parsed_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate parsed execution trace data.

        Args:
            data: Parsed execution trace data

        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['tasks', 'summary', 'parsed_at']

        for field in required_fields:
            if field not in data:
                self.logger.error(f"Missing required field: {field}")
                return False

        if not isinstance(data['tasks'], list):
            self.logger.error("Tasks field must be a list")
            return False

        if len(data['tasks']) == 0:
            self.logger.error("Tasks list cannot be empty")
            return False

        required_summary_fields = ['total_tasks', 'completed_tasks', 'total_duration_seconds']
        for field in required_summary_fields:
            if field not in data['summary']:
                self.logger.error(f"Missing required summary field: {field}")
                return False

        return True
