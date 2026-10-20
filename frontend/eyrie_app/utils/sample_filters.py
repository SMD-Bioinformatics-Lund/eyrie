"""
Server-side filtering of the samples and sequencing runs tables
"""
from urllib.parse import urlencode

from flask import request

from .template_filters import qc_class_filter, read_stats_filter, seqrun_date_filter

SEARCH_FIELDS = ['sample_name', 'sample_id', 'lims_id', 'sequencing_run_id']
CATEGORIES = ['production', 'validation', 'test']
SPIKE_LEVELS = {'complete': 'table-success', 'partial': 'table-warning', 'low': 'table-danger'}
QC_STATUSES = ['passed', 'failed', 'unprocessed']


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def filter_samples(samples, args):
    search = args.get('q', '').strip().lower()
    equal_filters = [
        (args.get('seqrun'), lambda s: s.get('sequencing_run_id')),
        (args.get('sample_type'), lambda s: (s.get('metadata') or {}).get('sample_type')),
        (args.get('material'), lambda s: (s.get('metadata') or {}).get('material')),
        (args.get('qc'), lambda s: s.get('qc')),
    ]
    categories = args.getlist('category')
    minimums = [
        ('reads', to_float(args.get('min_reads'))),
        ('quality', to_float(args.get('min_quality'))),
        ('filtered_percent', to_float(args.get('min_filtered'))),
    ]

    def keep(sample):
        if search and not any(search in str(sample.get(field) or '').lower() for field in SEARCH_FIELDS):
            return False
        if any(wanted and value(sample) != wanted for wanted, value in equal_filters):
            return False
        if categories and (sample.get('metadata') or {}).get('category') not in categories:
            return False
        stats = read_stats_filter(sample)
        return all(minimum is None or (stats[name] is not None and stats[name] >= minimum) for name, minimum in minimums)

    return [sample for sample in samples if keep(sample)]


def filter_options(samples):
    def distinct(values):
        return sorted({value for value in values if value})

    return {
        'seqruns': distinct(s.get('sequencing_run_id') for s in samples)[::-1],
        'sample_types': distinct((s.get('metadata') or {}).get('sample_type') for s in samples),
        'materials': distinct((s.get('metadata') or {}).get('material') for s in samples),
        'qc_statuses': QC_STATUSES,
        'categories': CATEGORIES,
    }


def spike_missing_percent(seqrun):
    total = seqrun.get('total_samples') or 0
    return 100 * (total - (seqrun.get('spikes_detected') or 0)) / total if total else None


def filter_seqruns(seqruns, args):
    search = args.get('q', '').strip().lower()
    pipeline_status = args.get('pipeline_status')
    spike_class = SPIKE_LEVELS.get(args.get('spikes'))
    min_samples = to_float(args.get('min_samples'))
    run_from, run_to = args.get('run_from'), args.get('run_to')

    def keep(seqrun):
        run_id = seqrun.get('sequencing_run_id') or ''
        run_date = seqrun_date_filter(run_id)
        if search and search not in run_id.lower():
            return False
        if pipeline_status and seqrun.get('pipeline_status') != pipeline_status:
            return False
        if spike_class and qc_class_filter(spike_missing_percent(seqrun), 'spike_missing_percent') != spike_class:
            return False
        if min_samples is not None and (seqrun.get('total_samples') or 0) < min_samples:
            return False
        if (run_from or run_to) and not run_date:
            return False
        return not (run_from and run_date < run_from) and not (run_to and run_date > run_to)

    return [seqrun for seqrun in seqruns if keep(seqrun)]


def seqrun_filter_options(seqruns):
    return {'pipeline_statuses': sorted({s.get('pipeline_status') for s in seqruns if s.get('pipeline_status')})}


def url_with_args(**changes):
    """Current URL with some query arguments replaced, or removed when None."""
    args = request.args.to_dict(flat=False)
    for key, value in changes.items():
        if value is None:
            args.pop(key, None)
        else:
            args[key] = [value]
    query = urlencode(args, doseq=True)
    return f"{request.path}?{query}" if query else request.path
