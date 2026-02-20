"""
Jinja2 template filters for server-side formatting
"""

def format_number_filter(num):
    """Format number with locale formatting"""
    if not num:
        return '--'
    return f"{num:,}"

def format_bases_filter(bases):
    """Format bases with appropriate unit"""
    if not bases:
        return '--'
    if bases >= 1e9:
        return f"{bases / 1e9:.1f} Gb"
    elif bases >= 1e6:
        return f"{bases / 1e6:.1f} Mb"
    elif bases >= 1e3:
        return f"{bases / 1e3:.1f} Kb"
    return f"{bases} bp"

def format_quality_filter(quality):
    """Format quality score"""
    if not quality:
        return '--'
    return f"Q{quality:.1f}"

def format_length_filter(length):
    """Format length in bp"""
    if not length:
        return '--'
    return f"{round(length):,} bp"

def qc_badge_class_filter(qc):
    """Get CSS class for QC badge"""
    qc_classes = {
        'passed': 'bg-success',
        'failed': 'bg-danger', 
        'unprocessed': 'bg-secondary'
    }
    return qc_classes.get(qc, 'bg-secondary')

def format_date_filter(date_obj):
    """Format date for display"""
    if not date_obj:
        return '--'
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%Y-%m-%d %H:%M')
    return str(date_obj)

def shannon_diversity_filter(species_hits):
    """Calculate Shannon diversity index - fallback if not pre-calculated"""
    if not species_hits:
        return 0.0
    
    # Handle case where species_hits might be the wrong data type
    if not isinstance(species_hits, list):
        return '--'
        
    try:
        total = sum(sp.get('abundance', 0) for sp in species_hits)
        if total == 0:
            return 0.0
        
        diversity = 0
        for sp in species_hits:
            abundance = sp.get('abundance', 0)
            if abundance > 0:
                proportion = abundance / total
                diversity -= proportion * __import__('math').log(proportion)
        
        return round(diversity, 2)
    except Exception:
        return '--'

def dominant_species_filter(species_hits):
    """Find dominant species - fallback if not pre-calculated"""
    if not species_hits:
        return '--'

    # Handle case where species_hits might be the wrong data type
    if not isinstance(species_hits, list):
        return '--'

    try:
        dominant = max(species_hits, key=lambda sp: sp.get('abundance', 0), default=None)
        return dominant.get('species', '--') if dominant else '--'
    except Exception:
        return '--'

def library_concentration_class_filter(concentration):
    """Get CSS class for library concentration badge based on value thresholds."""
    if not concentration:
        return ''
    try:
        value = float(concentration)
        if value < 1:
            return 'bg-danger'  # Red
        return ''  # Normal - no special styling
    except (ValueError, TypeError):
        return ''

def read_count_class_filter(count):
    """Get CSS class for read count — red when below 500."""
    if count is None:
        return ''
    try:
        if int(count) < 500:
            return 'text-danger'
        return ''
    except (ValueError, TypeError):
        return ''