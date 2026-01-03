"""Parser for software versions YAML files."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .pipeline_base import BasePipelineParser


class SoftwareVersionsParser(BasePipelineParser):
    """Parser for software versions YAML files (software_versions.yml)."""

    def __init__(self):
        super().__init__()
        self.tool_categories = {
            'quality_control': {
                'name': 'Quality Control',
                'tools': ['FASTQC', 'FILTLONG', 'NANOPLOT_PROCESSED_READS', 'NANOPLOT_UNPROCESSED_READS']
            },
            'taxonomy_analysis': {
                'name': 'Taxonomy Analysis', 
                'tools': ['EMU_ABUNDANCE', 'EMU_COMBINE_OUTPUTS', 'TRANSLATE_TAXIDS', 'KRONA_KTIMPORTTAXONOMY']
            },
            'visualization': {
                'name': 'Visualization',
                'tools': ['ASSIGNMENT_HEATMAP']
            },
            'workflow_management': {
                'name': 'Workflow Management',
                'tools': ['CUSTOM_DUMPSOFTWAREVERSIONS', 'Workflow']
            }
        }

    def _categorize_tools(self, versions_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize tools by their function.

        Args:
            versions_data: Raw versions data from YAML

        Returns:
            Categorized tools with versions
        """
        categorized = {}
        uncategorized = {}

        # Process defined categories
        for category_key, category_info in self.tool_categories.items():
            category_tools = {}

            for tool_name in category_info['tools']:
                if tool_name in versions_data:
                    tool_versions = versions_data[tool_name]

                    # Handle both dict and simple string formats
                    if isinstance(tool_versions, dict):
                        category_tools[tool_name] = tool_versions
                    else:
                        category_tools[tool_name] = {'version': str(tool_versions)}

            if category_tools:
                categorized[category_key] = {
                    'name': category_info['name'],
                    'tools': category_tools
                }

        # Collect uncategorized tools
        all_categorized_tools = set()
        for category_info in self.tool_categories.values():
            all_categorized_tools.update(category_info['tools'])

        for tool_name, tool_versions in versions_data.items():
            if tool_name not in all_categorized_tools:
                if isinstance(tool_versions, dict):
                    uncategorized[tool_name] = tool_versions
                else:
                    uncategorized[tool_name] = {'version': str(tool_versions)}

        if uncategorized:
            categorized['other'] = {
                'name': 'Other Tools',
                'tools': uncategorized
            }

        return categorized

    def _extract_workflow_info(self, versions_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract workflow-specific information.

        Args:
            versions_data: Raw versions data

        Returns:
            Workflow information
        """
        workflow_info = {}

        if 'Workflow' in versions_data:
            workflow_data = versions_data['Workflow']
            if isinstance(workflow_data, dict):
                workflow_info.update(workflow_data)

        return workflow_info

    def parse(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse software versions YAML file.

        Args:
            file_path: Path to the software_versions.yml file

        Returns:
            Parsed software versions organized by category, or None if parsing fails
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Software versions file not found: {file_path}")
                return None

            with open(file_path, 'r') as f:
                raw_versions = yaml.safe_load(f)

            if not raw_versions:
                self.logger.error("Empty software versions file")
                return None

            # Categorize tools
            categorized_tools = self._categorize_tools(raw_versions)

            # Extract workflow information
            workflow_info = self._extract_workflow_info(raw_versions)

            # Count total tools and versions
            total_tools = 0
            total_versions = 0

            for category_data in categorized_tools.values():
                tools = category_data.get('tools', {})
                total_tools += len(tools)

                for tool_versions in tools.values():
                    if isinstance(tool_versions, dict):
                        total_versions += len(tool_versions)
                    else:
                        total_versions += 1

            result = {
                'categories': categorized_tools,
                'workflow': workflow_info,
                'summary': {
                    'total_categories': len(categorized_tools),
                    'total_tools': total_tools,
                    'total_versions': total_versions
                },
                'parsed_at': self._get_current_timestamp()
            }

            self.logger.info(f"Successfully parsed {total_tools} software tools in {len(categorized_tools)} categories")
            return result

        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in software versions file {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing software versions file {file_path}: {e}")
            return None

    def validate_parsed_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate parsed software versions data.

        Args:
            data: Parsed software versions data

        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['categories', 'summary', 'parsed_at']

        for field in required_fields:
            if field not in data:
                self.logger.error(f"Missing required field: {field}")
                return False

        if not isinstance(data['categories'], dict):
            self.logger.error("Categories field must be a dictionary")
            return False

        required_summary_fields = ['total_categories', 'total_tools', 'total_versions']
        for field in required_summary_fields:
            if field not in data['summary']:
                self.logger.error(f"Missing required summary field: {field}")
                return False

        if data['summary']['total_tools'] <= 0:
            self.logger.error("Total tools must be greater than 0")
            return False

        return True
