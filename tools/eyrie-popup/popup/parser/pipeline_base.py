"""Base class for pipeline file parsers."""

import logging
from datetime import datetime


class BasePipelineParser:
    """Base class for parsing pipeline-related files."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        return datetime.now().isoformat()
