"""Trends analysis API endpoints."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pymongo import MongoClient
from pymongo.database import Database

from ..database.utils import get_db_connection
from ..auth.middleware import get_current_user

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/data")
async def get_trends_data(
    request: Request,
    category: str = Query(..., description="Category to analyse"),
    metric: str = Query(..., description="Metric to track"),
    time_range: str = Query("30", description="Time range in days or 'all'"),
    group_by: str = Query("week", description="Grouping: day, week, month"),
    classification: str = Query("all", description="Classification filter"),
    sample_type: str = Query("all", description="Sample type filter from metadata"),
    tissue: str = Query("all", description="Tissue filter from metadata"),
    extraction_kit: str = Query("all", description="Extraction kit filter from metadata"),
    library_prep_kit: str = Query("all", description="Library prep kit filter from metadata"),
    dilution: str = Query("all", description="Dilution filter from metadata"),
    spike_concentration: str = Query("all", description="Spike concentration filter from metadata"),
    qc: str = Query("all", description="QC status filter"),
    read_quality_filtering: str = Query("all", description="Read quality filtering filter"),
    genus: str = Query("all", description="Genus filter for dominant species analysis")
) -> Dict[str, Any]:
    """Get trends data for visualisation."""

    try:
        current_user = get_current_user(request)
        time_filter = {}
        if time_range != "all":
            days = int(time_range)
            start_date = datetime.utcnow() - timedelta(days=days)
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
        if tissue != "all":
            metadata_filter["metadata.tissue"] = tissue
        if extraction_kit != "all":
            metadata_filter["metadata.extraction_kit"] = extraction_kit
        if library_prep_kit != "all":
            metadata_filter["metadata.library_prep_kit"] = library_prep_kit
        if dilution != "all":
            metadata_filter["metadata.dilution"] = dilution
        if spike_concentration != "all":
            metadata_filter["metadata.spike_concentration"] = spike_concentration

        match_filter = {**time_filter, **classification_filter, **qc_filter, **metadata_filter}

        async with get_db_connection() as db:
            samples_collection = db.samples
            cursor = samples_collection.find(match_filter)
            samples = await cursor.to_list(length=None)

        # Apply genus filter for dominant species analysis
        if genus != "all":
            filtered_samples = []
            for sample in samples:
                taxonomic_data = sample.get("taxonomic_data", {})
                hits = taxonomic_data.get("hits", [])
                if hits and hits[0].get("genus", "").lower() == genus.lower():
                    filtered_samples.append(sample)
            samples = filtered_samples

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
        if metric == "species_frequency" and category == "dominant_species":
            # For species frequency analysis, we need the period count from the grouped data
            time_groups = group_by_time_period(samples, group_by)
            period_count = len(time_groups)
            series_data = process_species_frequency_data(samples, group_by)
        else:
            # Standard trends analysis
            period_count = len(group_by_time_period(samples, group_by))
            series_data = process_trends_data(samples, category, metric, group_by, read_quality_filtering)

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


def process_trends_data(samples: List[Dict], category: str, metric: str, group_by: str, read_quality_filtering: str = "all") -> List[Dict[str, Any]]:
    """Process samples data into trends series."""

    # Check if this is species frequency analysis
    if metric == "species_frequency" and category == "dominant_species":
        return process_species_frequency_data(samples, group_by)

    # Standard trends analysis
    category_groups = group_samples_by_category(samples, category)

    series_list = []

    for category_value, category_samples in category_groups.items():
        time_groups = group_by_time_period(category_samples, group_by)

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


def process_species_frequency_data(samples: List[Dict], group_by: str) -> List[Dict[str, Any]]:
    """Process samples for species frequency analysis (stacked area/bar charts)."""

    # Group samples by time period/sequencing run first
    time_groups = group_by_time_period(samples, group_by)

    # Collect all unique dominant species across all periods
    all_species = set()
    for period_samples in time_groups.values():
        for sample in period_samples:
            taxonomic_data = sample.get("taxonomic_data", {})
            hits = taxonomic_data.get("hits", [])
            if hits:
                species = hits[0].get("species", "Unknown")
                all_species.add(species)

    # Build series for each species
    series_list = []
    sorted_dates = sorted(time_groups.keys())

    for species in sorted(all_species):
        dates = []
        values = []

        for date_key in sorted_dates:
            period_samples = time_groups[date_key]

            # Count how many samples have this species as dominant
            species_count = 0
            total_samples = len(period_samples)

            for sample in period_samples:
                taxonomic_data = sample.get("taxonomic_data", {})
                hits = taxonomic_data.get("hits", [])
                if hits and hits[0].get("species", "") == species:
                    species_count += 1

            # Calculate percentage
            percentage = (species_count / total_samples * 100) if total_samples > 0 else 0

            dates.append(date_key)
            values.append(percentage)

        if any(value > 0 for value in values):  # Only include species that appear
            series_list.append({
                "name": species,
                "dates": dates,
                "values": values
            })
    return series_list


def group_samples_by_category(samples: List[Dict], category: str) -> Dict[str, List[Dict]]:
    """Group samples by the specified category."""

    groups = {}

    for sample in samples:
        if category == "sample_id":
            # Individual sample ID for tracking specific samples over time
            key = sample.get("sample_id", "Unknown")
        elif category == "read_quality_filtering":
            # Group by processing status - create separate entries for both processed and unprocessed if both exist
            nanoplot = sample.get("nanoplot", {})
            processed_stats = nanoplot.get("processed", {}).get("nanostats")
            unprocessed_stats = nanoplot.get("unprocessed", {}).get("nanostats")

            # Create separate sample entries for each processing type that exists
            if processed_stats:
                processed_sample = sample.copy()
                processed_sample["_nanostats_type"] = "processed"
                if "Processed" not in groups:
                    groups["Processed"] = []
                groups["Processed"].append(processed_sample)

            if unprocessed_stats:
                unprocessed_sample = sample.copy()
                unprocessed_sample["_nanostats_type"] = "unprocessed"
                if "Unprocessed" not in groups:
                    groups["Unprocessed"] = []
                groups["Unprocessed"].append(unprocessed_sample)

            # Skip the normal grouping logic for this category
            continue
        elif category == "spike_concentration":
            # Spike concentration from metadata (IC3 or IC4)
            metadata = sample.get("metadata", {})
            key = metadata.get("spike_concentration", "Unknown") if metadata else "Unknown"
        elif category == "classification_type":
            # Classification type (16S, ITS)
            key = sample.get("classification", "Unknown")
        elif category == "sample_type":
            # Sample type from metadata (validation, patient, negative, positive)
            metadata = sample.get("metadata", {})
            key = metadata.get("sample_type", "Unknown") if metadata else "Unknown"
        elif category == "tissue":
            # Tissue type from metadata
            metadata = sample.get("metadata", {})
            key = metadata.get("tissue", "Unknown") if metadata else "Unknown"
        elif category == "dilution":
            # Dilution from metadata
            metadata = sample.get("metadata", {})
            key = metadata.get("dilution", "Unknown") if metadata else "Unknown"
        elif category == "extraction_kit":
            # Extraction kit from metadata
            metadata = sample.get("metadata", {})
            key = metadata.get("extraction_kit", "Unknown") if metadata else "Unknown"
        elif category == "library_prep_kit":
            # Library prep kit from metadata
            metadata = sample.get("metadata", {})
            key = metadata.get("library_prep_kit", "Unknown") if metadata else "Unknown"
        elif category == "sequencing_run_id":
            # Sequencing run identifier
            key = sample.get("sequencing_run_id", "Unknown")
        elif category == "sequencing_run_date":
            # Sequencing run date in YYMMDD format
            key = sample.get("sequencing_run_date", "Unknown")
        elif category == "dominant_species":
            # Dominant species from taxonomic data for proportion analysis
            taxonomic_data = sample.get("taxonomic_data", {})
            hits = taxonomic_data.get("hits", [])
            if hits:
                key = hits[0].get("species", "Unknown")
            else:
                key = "Unknown"
        else:
            key = "All Samples"

        if key not in groups:
            groups[key] = []
        groups[key].append(sample)

    return groups


def group_by_time_period(samples: List[Dict], group_by: str) -> Dict[str, List[Dict]]:
    """Group samples by time period or sequencing run ID."""

    groups = {}

    for sample in samples:
        # Handle sequencing run ID or date grouping
        if group_by == "sequencing_run_id":
            period_key = sample.get("sequencing_run_id", "Unknown")
        elif group_by == "sequencing_run_date":
            period_key = sample.get("sequencing_run_date", "Unknown")
        else:
            # Get sample date for time-based grouping
            sample_date = sample.get("sequencing_run_date") or sample.get("created_date")
            if not sample_date:
                continue

            if isinstance(sample_date, str):
                sample_date = datetime.fromisoformat(sample_date.replace('Z', '+00:00'))

            # Generate period key
            if group_by == "day":
                period_key = sample_date.strftime("%Y-%m-%d")
            elif group_by == "week":
                # Start of week (Monday)
                start_of_week = sample_date - timedelta(days=sample_date.weekday())
                period_key = start_of_week.strftime("%Y-%m-%d")
            elif group_by == "month":
                period_key = sample_date.strftime("%Y-%m-01")
            else:
                period_key = sample_date.strftime("%Y-%m-%d")

        if period_key not in groups:
            groups[period_key] = []
        groups[period_key].append(sample)

    return groups


def get_nanostats(sample: Dict, read_quality_filtering: str) -> Dict:
    """Get nanostats from sample based on read quality filtering setting."""
    nanoplot = sample.get("nanoplot", {})

    # Check if sample has a specific nanostats type tag (for read_quality_filtering category)
    nanostats_type = sample.get("_nanostats_type")
    if nanostats_type:
        if nanostats_type == "processed":
            return nanoplot.get("processed", {}).get("nanostats", {})
        elif nanostats_type == "unprocessed":
            return nanoplot.get("unprocessed", {}).get("nanostats", {})

    # Otherwise use the read_quality_filtering parameter
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


def calculate_metric_value(samples: List[Dict], metric: str, read_quality_filtering: str = "all") -> float:
    """Calculate metric value for a group of samples."""

    if not samples:
        return 0.0

    if metric == "number_of_reads":
        total_reads = 0
        count = 0
        for sample in samples:
            stats = get_nanostats(sample, read_quality_filtering)
            if "number_of_reads" in stats and stats["number_of_reads"] is not None:
                total_reads += stats["number_of_reads"]
                count += 1
        if len(samples) == 1 and count == 1:
            return total_reads
        return total_reads / count if count > 0 else 0.0

    elif metric == "mean_read_length":
        total_length = 0
        count = 0
        for sample in samples:
            stats = get_nanostats(sample, read_quality_filtering)
            if "mean_read_length" in stats and stats["mean_read_length"]:
                total_length += stats["mean_read_length"]
                count += 1
        return total_length / count if count > 0 else 0.0

    elif metric == "mean_read_quality":
        total_quality = 0
        count = 0
        for sample in samples:
            stats = get_nanostats(sample, read_quality_filtering)
            if "mean_read_quality" in stats and stats["mean_read_quality"]:
                total_quality += stats["mean_read_quality"]
                count += 1
        return total_quality / count if count > 0 else 0.0

    elif metric == "contaminants_count":
        total_contaminants = 0
        for sample in samples:
            contaminants = sample.get("flagged_contaminants", [])
            total_contaminants += len(contaminants)
        return total_contaminants / len(samples) if samples else 0.0

    elif metric == "top_hits_count":
        total_hits = 0
        for sample in samples:
            hits = sample.get("flagged_top_hits", [])
            total_hits += len(hits)
        return total_hits / len(samples) if samples else 0.0

    elif metric == "qc_pass_rate":
        passed_count = 0
        for sample in samples:
            if sample.get("qc") == "passed":
                passed_count += 1
        return (passed_count / len(samples)) * 100 if samples else 0.0

    elif metric == "total_bases":
        total_bases = 0
        count = 0
        for sample in samples:
            stats = get_nanostats(sample, read_quality_filtering)
            if "total_bases" in stats and stats["total_bases"]:
                total_bases += stats["total_bases"]
                count += 1
        return total_bases / count if count > 0 else 0.0

    elif metric == "read_length_n50":
        total_n50 = 0
        count = 0
        for sample in samples:
            stats = get_nanostats(sample, read_quality_filtering)
            if "read_length_n50" in stats and stats["read_length_n50"]:
                total_n50 += stats["read_length_n50"]
                count += 1
        return total_n50 / count if count > 0 else 0.0

    elif metric == "library_concentration":
        # Average library concentration from metadata
        total_concentration = 0
        count = 0
        for sample in samples:
            metadata = sample.get("metadata", {})
            if metadata and "library_concentration" in metadata:
                try:
                    # Extract numeric value from concentration string
                    conc_str = metadata["library_concentration"]
                    if conc_str and isinstance(conc_str, str):
                        # Extract number from string (e.g., "50 ng/μL" -> 50)
                        import re
                        numbers = re.findall(r'\d+\.?\d*', conc_str)
                        if numbers:
                            total_concentration += float(numbers[0])
                            count += 1
                except (ValueError, TypeError):
                    continue
        return total_concentration / count if count > 0 else 0.0

    elif metric == "multiple_finds_rate":
        # Percentage of samples with multiple bacterial findings
        multiple_finds_count = 0
        for sample in samples:
            metadata = sample.get("metadata", {})
            if metadata and metadata.get("multiple_finds"):
                multiple_finds_str = str(metadata["multiple_finds"]).lower()
                if multiple_finds_str in ["yes", "true", "1", "multiple"]:
                    multiple_finds_count += 1
        return (multiple_finds_count / len(samples)) * 100 if samples else 0.0

    elif metric == "sample_count":
        # Simple count of samples (useful for categorical analysis)
        return len(samples)

    elif metric == "sanger_match_rate":
        # Rate of samples where top species matches Sanger expected species
        matches = 0
        total_with_sanger = 0
        for sample in samples:
            metadata = sample.get("metadata", {})
            expected_species = metadata.get("sanger_expected_species") if metadata else None
            if expected_species and expected_species.strip():
                total_with_sanger += 1
                # Get top species from taxonomic data
                taxonomic_data = sample.get("taxonomic_data", {})
                top_species = None
                if taxonomic_data and "species_abundance" in taxonomic_data:
                    abundances = taxonomic_data["species_abundance"]
                    if abundances and len(abundances) > 0:
                        top_species = abundances[0].get("species")

                if top_species and expected_species.lower() in top_species.lower():
                    matches += 1

        return (matches / total_with_sanger) * 100 if total_with_sanger > 0 else 0.0

    elif metric == "abundance_percentage":
        # Average abundance percentage for dominant species (for proportion analysis)
        total_abundance = 0
        count = 0
        for sample in samples:
            taxonomic_data = sample.get("taxonomic_data", {})
            hits = taxonomic_data.get("hits", [])
            if hits and "abundance" in hits[0]:
                total_abundance += hits[0]["abundance"]
                count += 1
        return total_abundance / count if count > 0 else 0.0

    elif metric == "species_frequency":
        # Count of samples (for species frequency analysis)
        return len(samples)

    else:
        return 0.0


@router.get("/summary")
async def get_trends_summary(
    request: Request
) -> Dict[str, Any]:
    """Get summary statistics for trends dashboard."""

    try:
        current_user = get_current_user(request)

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        async with get_db_connection() as db:
            samples_collection = db.samples
            cursor = samples_collection.find(
                {"created_date": {"$gte": thirty_days_ago}}
            )
            recent_samples = await cursor.to_list(length=None)

        # Calculate summary stats
        total_samples = len(recent_samples)
        qc_passed = len([s for s in recent_samples if s.get("qc") == "passed"])
        avg_contaminants = sum(len(s.get("flagged_contaminants", [])) for s in recent_samples) / total_samples if total_samples > 0 else 0
        avg_top_hits = sum(len(s.get("flagged_top_hits", [])) for s in recent_samples) / total_samples if total_samples > 0 else 0

        # Calculate metadata statistics
        samples_with_metadata = [s for s in recent_samples if s.get("metadata")]
        metadata_coverage = (len(samples_with_metadata) / total_samples * 100) if total_samples > 0 else 0

        # Sample type distribution
        sample_types = {}
        tissue_types = {}
        extraction_kits = {}

        for sample in samples_with_metadata:
            metadata = sample.get("metadata", {})

            # Count sample types
            sample_type = metadata.get("sample_type", "Unknown")
            sample_types[sample_type] = sample_types.get(sample_type, 0) + 1

            # Count tissue types
            tissue = metadata.get("tissue", "Unknown")
            tissue_types[tissue] = tissue_types.get(tissue, 0) + 1

            # Count extraction kits
            extraction_kit = metadata.get("extraction_kit", "Unknown")
            extraction_kits[extraction_kit] = extraction_kits.get(extraction_kit, 0) + 1

        return {
            "period": "Last 30 days",
            "total_samples": total_samples,
            "qc_pass_rate": round((qc_passed / total_samples) * 100, 1) if total_samples > 0 else 0,
            "avg_contaminants": round(avg_contaminants, 1),
            "avg_top_hits": round(avg_top_hits, 1),
            "classifications": {
                "16S": len([s for s in recent_samples if s.get("classification") == "16S"]),
                "ITS": len([s for s in recent_samples if s.get("classification") == "ITS"])
            },
            "metadata": {
                "coverage_rate": round(metadata_coverage, 1),
                "sample_types": sample_types,
                "tissue_types": tissue_types,
                "extraction_kits": extraction_kits
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/metadata/filters")
async def get_metadata_filters(
    request: Request
) -> Dict[str, Any]:
    """Get available metadata filter values."""

    try:
        current_user = get_current_user(request)

        async with get_db_connection() as db:
            samples_collection = db.samples
            # Get samples with metadata for metadata fields
            metadata_cursor = samples_collection.find({"metadata": {"$exists": True, "$ne": None}})
            samples_with_metadata = await metadata_cursor.to_list(length=None)

            # Get samples with taxonomic data for genera collection
            taxonomic_cursor = samples_collection.find({"taxonomic_data.hits": {"$exists": True, "$ne": []}})
            samples_with_taxonomic = await taxonomic_cursor.to_list(length=None)

        # Collect unique genera from dominant species (hits[0])
        genera = set()
        for sample in samples_with_taxonomic:
            taxonomic_data = sample.get("taxonomic_data", {})
            hits = taxonomic_data.get("hits", [])
            if hits and hits[0].get("genus"):
                genera.add(hits[0]["genus"])

        # Collect dynamic metadata fields
        tissues = set()
        extraction_kits = set()
        library_prep_kits = set()

        for sample in samples_with_metadata:
            metadata = sample.get("metadata", {})
            if not metadata:
                continue

            if metadata.get("tissue"):
                tissues.add(metadata["tissue"])
            if metadata.get("extraction_kit"):
                extraction_kits.add(metadata["extraction_kit"])
            if metadata.get("library_prep_kit"):
                library_prep_kits.add(metadata["library_prep_kit"])

        return {
            "tissues": sorted(list(tissues)),
            "extraction_kits": sorted(list(extraction_kits)),
            "library_prep_kits": sorted(list(library_prep_kits)),
            "genera": sorted(list(genera)),
            "total_samples_with_metadata": len(samples_with_metadata)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
