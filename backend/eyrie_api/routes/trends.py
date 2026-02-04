"""Trends analysis API endpoints."""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Request

from ..database.utils import get_db_connection
from ..auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trends", tags=["trends"])

# Supported categories for grouping samples
SUPPORTED_CATEGORIES = {
    "sequencing_run_id",
    "library_prep_kit",
    "library_prep_kit_lot_number",
    "extraction_kit",
    "extraction_kit_lot_number",
    "tissue",
}

# Supported metrics for calculation
SUPPORTED_METRICS = {
    "number_of_reads",
    "mean_read_quality",
    "mean_read_length",
    "read_length_n50",
    "total_contaminants_abundance",
    "library_concentration",
}


@router.get("/data")
async def get_trends_data(
    request: Request,
    category: str = Query(..., description="Category to analyse"),
    metric: str = Query(..., description="Metric to track"),
    time_range: str = Query("all", description="Time range in days or 'all'"),
    group_by: str = Query("week", description="Grouping: day, week, month"),
    classification: str = Query("all", description="Classification filter"),
    sample_type: str = Query("all", description="Sample type filter from metadata"),
    qc: str = Query("all", description="QC status filter"),
    read_quality_filtering: str = Query("all", description="Read quality filtering filter")
) -> Dict[str, Any]:
    """Get trends data for visualisation."""

    try:
        current_user = get_current_user(request)
        time_filter = {}
        if time_range != "all":
            days = int(time_range)
            start_date = datetime.now(datetime.timezone.utc) - timedelta(days=days)
            time_filter = {"created_date": {"$gte": start_date}}

        classification_filter = {}
        if classification != "all":
            classification_filter = {"classification": classification}

        qc_filter = {}
        if qc != "all":
            qc_filter = {"qc": qc}

        metadata_filter = {}
        if sample_type != "all":
            metadata_filter["metadata.sample_type"] = sample_type

        match_filter = {**time_filter, **classification_filter, **qc_filter, **metadata_filter}

        async with get_db_connection() as db:
            samples_collection = db.samples
            seqruns_collection = db.seqruns
            cursor = samples_collection.find(match_filter)
            samples = await cursor.to_list(length=None)

            # Get seqruns data and join with samples
            seqrun_ids = list(set(sample.get("sequencing_run_id") for sample in samples if sample.get("sequencing_run_id")))
            seqruns_cursor = seqruns_collection.find({"sequencing_run_id": {"$in": seqrun_ids}})
            seqruns = await seqruns_cursor.to_list(length=None)

            # Create seqrun lookup dict
            seqruns_dict = {seqrun["sequencing_run_id"]: seqrun for seqrun in seqruns}

            # Add seqrun exp_start_time to samples for processing
            for sample in samples:
                seqrun_id = sample.get("sequencing_run_id")
                if seqrun_id and seqrun_id in seqruns_dict:
                    seqrun = seqruns_dict[seqrun_id]
                    sequencing_metadata = seqrun.get("sequencing_metadata", {})
                    sample["_seqrun_exp_start_time"] = sequencing_metadata.get("exp_start_time")

        if not samples:
            return {
                "series": [],
                "metadata": {
                    "total_samples": 0,
                    "date_range": f"Last {time_range} days" if time_range != "all" else "All time",
                    "category": category,
                    "metric": metric
                }
            }

        # Process trends data and get period count
        period_count = len(group_by_time_period(samples))
        series_data = process_trends_data(samples, category, metric, read_quality_filtering)

        return {
            "series": series_data,
            "metadata": {
                "total_samples": len(samples),
                "date_range": f"Last {time_range} days" if time_range != "all" else "All time",
                "category": category,
                "metric": metric,
                "group_by": group_by,
                "period_count": period_count
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def process_trends_data(samples: List[Dict], category: str, metric: str, read_quality_filtering: str = "all") -> List[Dict[str, Any]]:
    """Process samples data into trends series."""

    category_groups = group_samples_by_category(samples, category)

    series_list = []

    for category_value, category_samples in category_groups.items():
        time_groups = group_by_time_period(category_samples)

        dates = []
        values = []

        for date_key in sorted(time_groups.keys()):
            period_samples = time_groups[date_key]
            metric_value = calculate_metric_value(period_samples, metric, read_quality_filtering)

            dates.append(date_key)
            values.append(metric_value)

        if dates and values:
            series_list.append({
                "name": str(category_value) if category_value is not None else "Unknown",
                "dates": dates,
                "values": values
            })

    return series_list


def group_samples_by_category(samples: List[Dict], category: str) -> Dict[str, List[Dict]]:
    """Group samples by the specified category.

    Supported categories:
    - sequencing_run_id
    - library_prep_kit
    - library_prep_kit_lot_number
    - extraction_kit
    - extraction_kit_lot_number
    - tissue
    """

    groups = {}

    for sample in samples:
        if category == "sequencing_run_id":
            key = sample.get("sequencing_run_id", "Unknown")
        elif category == "library_prep_kit":
            metadata = sample.get("metadata", {})
            key = metadata.get("library_prep_kit", "Unknown") if metadata else "Unknown"
        elif category == "library_prep_kit_lot_number":
            metadata = sample.get("metadata", {})
            key = metadata.get("library_prep_kit_lot_number", "Unknown") if metadata else "Unknown"
        elif category == "extraction_kit":
            metadata = sample.get("metadata", {})
            key = metadata.get("extraction_kit", "Unknown") if metadata else "Unknown"
        elif category == "extraction_kit_lot_number":
            metadata = sample.get("metadata", {})
            key = metadata.get("extraction_kit_lot_number", "Unknown") if metadata else "Unknown"
        elif category == "tissue":
            metadata = sample.get("metadata", {})
            key = metadata.get("tissue", "Unknown") if metadata else "Unknown"
        else:
            logger.warning(f"Unsupported category '{category}', grouping all samples together")
            key = "All Samples"

        if key not in groups:
            groups[key] = []
        groups[key].append(sample)

    return groups


def group_by_time_period(samples: List[Dict]) -> Dict[str, List[Dict]]:
    """Group samples by exp_start_time.

    Samples without exp_start_time are excluded and a warning is logged.
    """

    groups = {}
    excluded_samples = []
    missing_seqrun_ids = set()

    for sample in samples:
        exp_start_time = sample.get("_seqrun_exp_start_time")

        if not exp_start_time:
            excluded_samples.append(sample)
            seqrun_id = sample.get("sequencing_run_id")
            if seqrun_id:
                missing_seqrun_ids.add(seqrun_id)
            continue

        # Format datetime with full timestamp for grouping
        if isinstance(exp_start_time, str):
            exp_start_time = datetime.fromisoformat(exp_start_time.replace('Z', '+00:00'))
        period_key = exp_start_time.strftime("%Y-%m-%dT%H:%M:%S")

        if period_key not in groups:
            groups[period_key] = []
        groups[period_key].append(sample)

    # Log warning if samples were excluded
    if excluded_samples:
        logger.warning(
            f"Excluded {len(excluded_samples)} samples from trends analysis due to missing exp_start_time. "
            f"Upload sequencing run metadata for: {sorted(missing_seqrun_ids)}"
        )

    return groups


def get_nanostats(sample: Dict, read_quality_filtering: str) -> Dict:
    """Get nanostats from sample based on read quality filtering setting."""
    nanoplot = sample.get("nanoplot", {})

    if read_quality_filtering == "processed":
        return nanoplot.get("processed", {}).get("nanostats", {})
    elif read_quality_filtering == "unprocessed":
        return nanoplot.get("unprocessed", {}).get("nanostats", {})
    else:
        # Default to processed if available, else unprocessed
        processed_stats = nanoplot.get("processed", {}).get("nanostats")
        if processed_stats:
            return processed_stats
        return nanoplot.get("unprocessed", {}).get("nanostats", {})


def _average_nanostats_field(samples: List[Dict], field: str, read_quality_filtering: str) -> float:
    """Calculate average of a nanostats field across samples."""
    total = 0
    count = 0
    for sample in samples:
        stats = get_nanostats(sample, read_quality_filtering)
        value = stats.get(field)
        if value is not None:
            total += value
            count += 1
    return total / count if count > 0 else 0.0


def calculate_metric_value(samples: List[Dict], metric: str, read_quality_filtering: str = "all") -> float:
    """Calculate metric value for a group of samples.

    Supported metrics:
    - number_of_reads
    - mean_read_quality
    - mean_read_length
    - read_length_n50
    - total_contaminants_abundance
    - library_concentration
    """

    if not samples:
        return 0.0

    if metric == "number_of_reads":
        return _average_nanostats_field(samples, "number_of_reads", read_quality_filtering)

    elif metric == "mean_read_length":
        return _average_nanostats_field(samples, "mean_read_length", read_quality_filtering)

    elif metric == "mean_read_quality":
        return _average_nanostats_field(samples, "mean_read_quality", read_quality_filtering)

    elif metric == "read_length_n50":
        return _average_nanostats_field(samples, "read_length_n50", read_quality_filtering)

    elif metric == "total_contaminants_abundance":
        # Total abundance percentage of flagged contaminants per sample
        total_abundance = 0
        count = 0
        for sample in samples:
            contaminants = sample.get("flagged_contaminants", [])
            if contaminants:
                taxonomic_data = sample.get("taxonomic_data", {})
                hits = taxonomic_data.get("hits", [])
                sample_contaminant_abundance = 0
                for hit in hits:
                    if hit.get("species") in contaminants:
                        sample_contaminant_abundance += hit.get("abundance", 0)
                total_abundance += sample_contaminant_abundance
                count += 1
        return total_abundance / count if count > 0 else 0.0

    elif metric == "library_concentration":
        # Average library concentration from metadata
        total_concentration = 0
        count = 0
        for sample in samples:
            metadata = sample.get("metadata", {})
            if metadata and "library_concentration" in metadata:
                try:
                    conc_str = metadata["library_concentration"]
                    if conc_str and isinstance(conc_str, str):
                        # Extract number from string (e.g., "50 ng/μL" -> 50)
                        numbers = re.findall(r'\d+\.?\d*', conc_str)
                        if numbers:
                            total_concentration += float(numbers[0])
                            count += 1
                except (ValueError, TypeError):
                    continue
        return total_concentration / count if count > 0 else 0.0

    else:
        logger.warning(f"Unsupported metric '{metric}', returning 0.0")
        return 0.0
