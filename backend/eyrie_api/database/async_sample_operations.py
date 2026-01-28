"""Async sample database operations."""

import math
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from .utils import get_db_connection


async def get_all_samples() -> List[Dict[str, Any]]:
    """Get all samples."""
    async with get_db_connection() as db:
        cursor = db.samples.find()
        return await cursor.to_list(length=None)


async def find_sample(sample_id: str) -> Optional[Dict[str, Any]]:
    """Find sample by sample_id."""
    async with get_db_connection() as db:
        return await db.samples.find_one({'sample_id': sample_id})


async def create_sample(sample_data: Dict[str, Any]) -> str:
    """Create a new sample."""
    async with get_db_connection() as db:
        existing = await db.samples.find_one({'sample_id': sample_data['sample_id']})
        if existing:
            raise ValueError(f"Sample with ID '{sample_data['sample_id']}' already exists")

        sample_data['created_date'] = datetime.now()
        sample_data['updated_date'] = datetime.now()

        result = await db.samples.insert_one(sample_data)
        return str(result.inserted_id)


async def update_sample(sample_id: str, update_data: Dict[str, Any]) -> bool:
    """Update an existing sample."""
    async with get_db_connection() as db:
        filtered_data = {k: v for k, v in update_data.items() if v is not None}

        if not filtered_data:
            return False

        filtered_data['updated_date'] = datetime.now()

        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {'$set': filtered_data}
        )
        return result.matched_count > 0


async def upsert_sample(sample_data: Dict[str, Any]) -> Tuple[str, bool]:
    """Create sample if it doesn't exist, update if it does. Returns (id, was_created)."""
    async with get_db_connection() as db:
        existing = await db.samples.find_one({'sample_id': sample_data['sample_id']})

        if existing:
            update_data = {k: v for k, v in sample_data.items() if k != 'sample_id'}
            update_data['updated_date'] = datetime.now()

            await db.samples.update_one(
                {'sample_id': sample_data['sample_id']},
                {'$set': update_data}
            )
            return str(existing['_id']), False
        else:
            sample_data['created_date'] = datetime.now()
            sample_data['updated_date'] = datetime.now()
            result = await db.samples.insert_one(sample_data)
            return str(result.inserted_id), True


async def update_sample_qc(sample_id: str, qc_status: str, comments: Dict[str, Any]) -> bool:
    """Update sample QC status and comments."""
    async with get_db_connection() as db:
        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {
                '$set': {
                    'qc': qc_status,
                    'comments': comments,
                    'updated_date': datetime.now()
                }
            }
        )
        return result.matched_count > 0


async def update_sample_comment(sample_id: str, comments: Dict[str, Any]) -> bool:
    """Update sample comments only."""
    async with get_db_connection() as db:
        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {
                '$set': {
                    'comments': comments,
                    'updated_date': datetime.now()
                }
            }
        )
        return result.matched_count > 0


async def update_sample_species_flags(
    sample_id: str,
    flagged_contaminants: Optional[List] = None,
    flagged_top_hits: Optional[List] = None
) -> bool:
    """Update sample species flags (contaminants and/or top hits)."""
    async with get_db_connection() as db:
        update_data = {'updated_date': datetime.now()}

        if flagged_contaminants is not None:
            update_data['flagged_contaminants'] = flagged_contaminants

        if flagged_top_hits is not None:
            update_data['flagged_top_hits'] = flagged_top_hits

        result = await db.samples.update_one(
            {'sample_id': sample_id},
            {'$set': update_data}
        )
        return result.matched_count > 0


async def find_negative_controls_by_run_id(sequencing_run_id: str) -> List[Dict[str, Any]]:
    """Find negative control samples by sequencing_run_id."""
    async with get_db_connection() as db:
        cursor = db.samples.find(
            {
                'sequencing_run_id': sequencing_run_id,
                'metadata.sample_type': 'negative control'
            },
            {
                'sample_id': 1,
                'taxonomic_data.hits': 1,
                '_id': 0
            }
        )
        return await cursor.to_list(length=12)


async def get_contamination_analysis(sequencing_run_id: str) -> Dict[str, Any]:
    """Analyze contamination/barcode hopping for a sequencing run.

    Finds species present in negative controls and analyzes their abundance
    distribution across normal samples in the same sequencing run.
    """
    async with get_db_connection() as db:
        # Get negative control samples
        negative_controls = await find_negative_controls_by_run_id(sequencing_run_id)

        if not negative_controls:
            return {
                'contaminating_species': [],
                'normal_samples_count': 0,
                'sequencing_run_id': sequencing_run_id,
                'message': 'No negative control samples found for this sequencing run'
            }

        # Extract unique species from negative controls, tracking which controls they came from
        species_to_negative_controls = {}  # species -> list of negative control sample_ids
        for negative_sample in negative_controls:
            sample_id = negative_sample.get('sample_id', 'Unknown')
            taxonomic_data = negative_sample.get('taxonomic_data', {})
            hits = taxonomic_data.get('hits', [])
            for hit in hits:
                species = hit.get('species')
                if species and species.strip():
                    species = species.strip()
                    if species not in species_to_negative_controls:
                        species_to_negative_controls[species] = []
                    if sample_id not in species_to_negative_controls[species]:
                        species_to_negative_controls[species].append(sample_id)

        contaminating_species = set(species_to_negative_controls.keys())

        if not contaminating_species:
            return {
                'contaminating_species': [],
                'normal_samples_count': 0,
                'sequencing_run_id': sequencing_run_id,
                'message': 'No species detected in negative control samples'
            }

        # Get normal samples (exclude negative controls) from the same sequencing run
        normal_samples_cursor = db.samples.find(
            {
                'sequencing_run_id': sequencing_run_id,
                'metadata.sample_type': {'$ne': 'negative control'}
            },
            {
                'sample_id': 1,
                'taxonomic_data.hits': 1,
                '_id': 0
            }
        )
        normal_samples = await normal_samples_cursor.to_list(length=None)

        if not normal_samples:
            return {
                'contaminating_species': list(contaminating_species),
                'normal_samples_count': 0,
                'sequencing_run_id': sequencing_run_id,
                'message': 'No normal samples found for abundance analysis'
            }

        # Analyze abundance of contaminating species in normal samples
        species_analysis = {}
        for species in contaminating_species:
            abundances = []
            detected_samples = []

            for sample in normal_samples:
                taxonomic_data = sample.get('taxonomic_data', {})
                hits = taxonomic_data.get('hits', [])

                # Find this species in the sample's hits
                for hit in hits:
                    hit_species = hit.get('species', '').strip()
                    if hit_species == species:
                        abundance = hit.get('abundance', 0)
                        abundances.append(abundance)
                        detected_samples.append(sample.get('sample_id'))
                        break

            # Calculate average abundance for sorting
            avg_abundance = sum(abundances) / len(abundances) if abundances else 0

            species_analysis[species] = {
                'abundances': abundances,
                'detected_in_samples': detected_samples,
                'detection_rate': len(abundances) / len(normal_samples) * 100 if normal_samples else 0,
                'average_abundance': avg_abundance,
                'source_negative_controls': species_to_negative_controls.get(species, [])
            }

        # Sort species by average abundance (highest first)
        sorted_species_items = sorted(species_analysis.items(), 
                                    key=lambda x: x[1]['average_abundance'], 
                                    reverse=True)
        species_analysis = dict(sorted_species_items)

        return {
            'contaminating_species': list(contaminating_species),
            'normal_samples_count': len(normal_samples),
            'species_analysis': species_analysis,
            'negative_controls_count': len(negative_controls),
            'sequencing_run_id': sequencing_run_id,
            'message': None if contaminating_species else 'No contamination detected'
        }


async def get_qc_overview_analysis(sequencing_run_id: str) -> Dict[str, Any]:
    """Get QC overview analysis including Sanger species matching."""
    async with get_db_connection() as db:
        # Get all samples for this sequencing run
        samples_cursor = db.samples.find(
            {'sequencing_run_id': sequencing_run_id},
            {
                'sample_id': 1,
                'metadata': 1,
                'taxonomic_data.hits': 1,
                '_id': 0
            }
        )
        all_samples = await samples_cursor.to_list(length=None)

        if not all_samples:
            return {'message': 'No samples found for this sequencing run'}

        # Analyze Sanger expected species matching
        sanger_analysis = {'species_matches': 0, 'genus_matches': 0, 'total_analyzed': 0}
        sample_type_counts = {'validation': 0, 'patient': 0, 'negative control': 0, 'positive control': 0}
        tissue_type_counts = {}

        for sample in all_samples:
            metadata = sample.get('metadata', {})
            sample_type = metadata.get('sample_type')
            multiple_finds = metadata.get('multiple_finds')
            sanger_expected = metadata.get('sanger_expected_species')
            tissue_type = metadata.get('tissue')

            # Count sample types
            if sample_type:
                sample_type_counts[sample_type] = sample_type_counts.get(sample_type, 0) + 1

            # Count tissue types
            if tissue_type:
                tissue_type_counts[tissue_type] = tissue_type_counts.get(tissue_type, 0) + 1

            # Analyze Sanger matching only if multiple_finds is False and sanger_expected exists
            if multiple_finds is False and sanger_expected:
                sanger_analysis['total_analyzed'] += 1
                taxonomic_hits = sample.get('taxonomic_data', {}).get('hits', [])

                if taxonomic_hits:
                    # Get top hit (highest abundance)
                    top_hit = max(taxonomic_hits, key=lambda x: x.get('abundance', 0))
                    detected_species = top_hit.get('species', '').strip().lower()
                    detected_genus = top_hit.get('genus', '').strip().lower()

                    # Check species-level match
                    if detected_species and detected_species == sanger_expected.strip().lower():
                        sanger_analysis['species_matches'] += 1
                        sanger_analysis['genus_matches'] += 1  # Species match implies genus match
                    # Check genus-level match
                    elif detected_genus and sanger_expected.strip().lower().startswith(detected_genus):
                        sanger_analysis['genus_matches'] += 1

        return {
            'total_samples': len(all_samples),
            'sample_type_counts': sample_type_counts,
            'tissue_type_counts': tissue_type_counts,
            'sanger_analysis': sanger_analysis,
            'sequencing_run_id': sequencing_run_id
        }


async def get_read_quality_analysis(sequencing_run_id: str) -> Dict[str, Any]:
    """Get read quality analysis across all samples in sequencing run."""
    async with get_db_connection() as db:
        samples_cursor = db.samples.find(
            {'sequencing_run_id': sequencing_run_id},
            {
                'sample_id': 1,
                'nanoplot': 1,
                '_id': 0
            }
        )
        samples = await samples_cursor.to_list(length=None)

        if not samples:
            return {'message': 'No samples found for this sequencing run'}

        quality_data = []
        # Aggregate metrics for box plots
        metrics = {
            'processed_reads': {'processed': [], 'unprocessed': []},
            'mean_quality': {'processed': [], 'unprocessed': []},
            'mean_length': {'processed': [], 'unprocessed': []},
            'total_bases': {'processed': [], 'unprocessed': []}
        }
        sample_ids = {'processed': [], 'unprocessed': []}

        for sample in samples:
            sample_id = sample.get('sample_id')
            nanoplot = sample.get('nanoplot', {})
            processed_stats = nanoplot.get('processed', {}).get('nanostats', {})
            unprocessed_stats = nanoplot.get('unprocessed', {}).get('nanostats', {})

            # Include sample if it has any nanoplot data (even if nanostats are empty)
            if nanoplot and (nanoplot.get('processed') or nanoplot.get('unprocessed')):
                quality_data.append({
                    'sample_id': sample_id,
                    'processed': processed_stats,
                    'unprocessed': unprocessed_stats
                })

                # Collect processed metrics for box plots
                if processed_stats:
                    if processed_stats.get('number_of_reads'):
                        metrics['processed_reads']['processed'].append(processed_stats.get('number_of_reads'))
                        sample_ids['processed'].append(sample_id)
                    if processed_stats.get('mean_read_quality'):
                        metrics['mean_quality']['processed'].append(processed_stats.get('mean_read_quality'))
                    if processed_stats.get('mean_read_length'):
                        metrics['mean_length']['processed'].append(processed_stats.get('mean_read_length'))
                    if processed_stats.get('total_bases'):
                        metrics['total_bases']['processed'].append(processed_stats.get('total_bases'))

                # Collect unprocessed metrics for box plots
                if unprocessed_stats:
                    if unprocessed_stats.get('number_of_reads'):
                        metrics['processed_reads']['unprocessed'].append(unprocessed_stats.get('number_of_reads'))
                        sample_ids['unprocessed'].append(sample_id)
                    if unprocessed_stats.get('mean_read_quality'):
                        metrics['mean_quality']['unprocessed'].append(unprocessed_stats.get('mean_read_quality'))
                    if unprocessed_stats.get('mean_read_length'):
                        metrics['mean_length']['unprocessed'].append(unprocessed_stats.get('mean_read_length'))
                    if unprocessed_stats.get('total_bases'):
                        metrics['total_bases']['unprocessed'].append(unprocessed_stats.get('total_bases'))

        return {
            'sequencing_run_id': sequencing_run_id,
            'samples_analyzed': len(quality_data),
            'quality_data': quality_data,
            'metrics': metrics,
            'sample_ids': sample_ids
        }


async def get_taxonomic_diversity_analysis(sequencing_run_id: str) -> Dict[str, Any]:
    """Get taxonomic diversity analysis for sequencing run."""
    async with get_db_connection() as db:
        samples_cursor = db.samples.find(
            {'sequencing_run_id': sequencing_run_id},
            {
                'sample_id': 1,
                'taxonomic_data.hits': 1,
                'metadata.sample_type': 1,
                '_id': 0
            }
        )
        samples = await samples_cursor.to_list(length=None)

        if not samples:
            return {'message': 'No samples found for this sequencing run'}

        coverage_data = []
        for sample in samples:
            sample_id = sample.get('sample_id')
            sample_type = sample.get('metadata', {}).get('sample_type')
            hits = sample.get('taxonomic_data', {}).get('hits', [])

            if hits:
                # Calculate Shannon diversity index
                total_abundance = sum(hit.get('abundance', 0) for hit in hits)
                shannon_diversity = 0
                if total_abundance > 0:
                    for hit in hits:
                        abundance = hit.get('abundance', 0)
                        if abundance > 0:
                            proportion = abundance / total_abundance
                            shannon_diversity -= proportion * math.log(proportion)

                coverage_data.append({
                    'sample_id': sample_id,
                    'sample_type': sample_type,
                    'total_species': len(hits),
                    'shannon_diversity': shannon_diversity,
                    'top_species_abundance': max(hit.get('abundance', 0) for hit in hits) if hits else 0
                })

        return {
            'sequencing_run_id': sequencing_run_id,
            'samples_analyzed': len(coverage_data),
            'diversity_data': coverage_data
        }


async def get_outlier_detection_analysis(sequencing_run_id: str) -> Dict[str, Any]:
    """Get outlier detection analysis for sequencing run."""
    async with get_db_connection() as db:
        samples_cursor = db.samples.find(
            {'sequencing_run_id': sequencing_run_id},
            {
                'sample_id': 1,
                'nanoplot': 1,
                'taxonomic_data.hits': 1,
                'metadata.sample_type': 1,
                '_id': 0
            }
        )
        samples = await samples_cursor.to_list(length=None)

        if not samples:
            return {'message': 'No samples found for this sequencing run'}

        outliers = []
        metrics = []

        for sample in samples:
            sample_id = sample.get('sample_id')
            sample_type = sample.get('metadata', {}).get('sample_type')
            nanoplot = sample.get('nanoplot', {})
            nano_stats = nanoplot.get('processed', {}).get('nanostats', {})
            hits = sample.get('taxonomic_data', {}).get('hits', [])

            # Collect key metrics for outlier detection
            read_count = nano_stats.get('number_of_reads', 0)
            mean_quality = nano_stats.get('mean_read_quality', 0)
            total_species = len(hits)

            metrics.append({
                'sample_id': sample_id,
                'sample_type': sample_type,
                'read_count': read_count,
                'mean_quality': mean_quality,
                'total_species': total_species
            })

        # Simple outlier detection using IQR method for read count
        if len(metrics) > 4:  # Need sufficient samples for outlier detection
            read_counts = [m['read_count'] for m in metrics if m['read_count'] > 0]
            if read_counts:
                read_counts.sort()
                n = len(read_counts)
                q1 = read_counts[n // 4]
                q3 = read_counts[3 * n // 4]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                for metric in metrics:
                    if metric['read_count'] > 0 and (metric['read_count'] < lower_bound or metric['read_count'] > upper_bound):
                        outliers.append({
                            'sample_id': metric['sample_id'],
                            'sample_type': metric['sample_type'],
                            'outlier_type': 'read_count',
                            'value': metric['read_count'],
                            'expected_range': f"{lower_bound:.0f} - {upper_bound:.0f}"
                        })

        return {
            'sequencing_run_id': sequencing_run_id,
            'samples_analyzed': len(metrics),
            'outliers_detected': len(outliers),
            'outliers': outliers,
            'metrics_summary': metrics
        }


async def get_positive_control_validation(sequencing_run_id: str) -> Dict[str, Any]:
    """Get positive control validation analysis."""
    async with get_db_connection() as db:
        # Find positive control samples
        positive_controls_cursor = db.samples.find(
            {
                'sequencing_run_id': sequencing_run_id,
                'metadata.sample_type': 'positive control'
            },
            {
                'sample_id': 1,
                'taxonomic_data.hits': 1,
                'metadata': 1,
                '_id': 0
            }
        )
        positive_controls = await positive_controls_cursor.to_list(length=None)

        if not positive_controls:
            return {'message': 'No positive control samples found for this sequencing run'}

        validation_results = []
        for control in positive_controls:
            sample_id = control.get('sample_id')
            metadata = control.get('metadata', {})
            hits = control.get('taxonomic_data', {}).get('hits', [])

            # Check if expected species are detected
            expected_species = metadata.get('sanger_expected_species')
            spike_species = metadata.get('spike_concentration')

            top_species = None
            expected_detected = False
            if hits:
                top_hit = max(hits, key=lambda x: x.get('abundance', 0))
                top_species = top_hit.get('species')

                if expected_species:
                    expected_detected = any(
                        hit.get('species', '').lower() == expected_species.lower()
                        for hit in hits
                    )

            validation_results.append({
                'sample_id': sample_id,
                'expected_species': expected_species,
                'spike_concentration': spike_species,
                'top_detected_species': top_species,
                'expected_species_detected': expected_detected,
                'total_species_detected': len(hits)
            })

        return {
            'sequencing_run_id': sequencing_run_id,
            'positive_controls_count': len(positive_controls),
            'validation_results': validation_results
        }
