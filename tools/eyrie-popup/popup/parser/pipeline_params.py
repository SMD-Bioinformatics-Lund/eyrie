"""Parser for pipeline parameters JSON files."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .pipeline_base import BasePipelineParser


class PipelineParamsParser(BasePipelineParser):
    """Parser for pipeline parameters JSON files (params_*.json)."""

    def __init__(self):
        super().__init__()
        self.parameter_categories = {
            'input_output': {
                'name': 'Input/Output Settings',
                'params': ['input', 'outdir', 'tracedir', 'barcodes_samplesheet', 'merge_fastq_pass']
            },
            'quality_control': {
                'name': 'Quality Control',
                'params': ['quality_filtering', 'longread_qc_qualityfilter_minlength', 
                          'longread_qc_qualityfilter_maxlength', 'longread_qc_qualityfilter_min_mean_q',
                          'adapter_trimming', 'cutadapt_min_overlap', 'cutadapt_max_error_rate']
            },
            'taxonomy_analysis': {
                'name': 'Taxonomy Analysis',
                'params': ['db', 'seqtype', 'min_abundance', 'minimap_max_alignments', 'minibatch_size',
                          'combine_levels', 'combine_counts', 'run_krona', 'krona_taxonomy_tab']
            },
            'resource_limits': {
                'name': 'Resource Limits',
                'params': ['max_memory', 'max_cpus', 'max_time']
            },
            'pipeline_config': {
                'name': 'Pipeline Configuration', 
                'params': ['seqtype', 'keep_read_assignments', 'keep_files', 'output_unclassified',
                          'make_heatmap', 'save_intermediates', 'save_preprocessed_reads']
            },
            'multiqc': {
                'name': 'MultiQC Settings',
                'params': ['multiqc_config', 'multiqc_title', 'multiqc_logo', 'max_multiqc_email_size']
            }
        }

    def parse(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse pipeline parameters JSON file.

        Args:
            file_path: Path to the params_*.json file

        Returns:
            Parsed parameters organized by category, or None if parsing fails
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Pipeline params file not found: {file_path}")
                return None

            with open(file_path, 'r') as f:
                raw_params = json.load(f)

            # Extract trace timestamp for identification
            trace_timestamp = raw_params.get('trace_timestamp')

            # Organize parameters by category
            categorized_params = {}
            uncategorized_params = {}

            for category_key, category_info in self.parameter_categories.items():
                category_name = category_info['name']
                category_params = {}

                for param_name in category_info['params']:
                    if param_name in raw_params:
                        category_params[param_name] = {
                            'value': raw_params[param_name],
                            'type': type(raw_params[param_name]).__name__
                        }

                if category_params:
                    categorized_params[category_key] = {
                        'name': category_name,
                        'parameters': category_params
                    }

            # Collect any parameters not in defined categories
            all_categorized_params = set()
            for category_info in self.parameter_categories.values():
                all_categorized_params.update(category_info['params'])

            for param_name, param_value in raw_params.items():
                if param_name not in all_categorized_params and param_name != 'trace_timestamp':
                    uncategorized_params[param_name] = {
                        'value': param_value,
                        'type': type(param_value).__name__
                    }

            if uncategorized_params:
                categorized_params['other'] = {
                    'name': 'Other Parameters',
                    'parameters': uncategorized_params
                }

            result = {
                'trace_timestamp': trace_timestamp,
                'categories': categorized_params,
                'total_parameters': len(raw_params) - (1 if trace_timestamp else 0),
                'parsed_at': self._get_current_timestamp()
            }

            self.logger.info(f"Successfully parsed {len(raw_params)} pipeline parameters")
            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in pipeline params file {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing pipeline params file {file_path}: {e}")
            return None

    def validate_parsed_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate parsed pipeline parameters data.

        Args:
            data: Parsed parameters data

        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['categories', 'total_parameters', 'parsed_at']

        for field in required_fields:
            if field not in data:
                self.logger.error(f"Missing required field: {field}")
                return False

        if not isinstance(data['categories'], dict):
            self.logger.error("Categories field must be a dictionary")
            return False

        if data['total_parameters'] <= 0:
            self.logger.error("Total parameters must be greater than 0")
            return False

        return True
