import json
import requests
from flask import Blueprint, render_template, url_for, redirect, session, request, flash
from flask_login import login_required
import urllib.parse
from collections import defaultdict
from ...config import settings
from ...eyrie import (
    get_samples_from_backend, serve_analysis_file, get_seqrun_from_backend, get_analysis_path,
    get_contamination_analysis_from_backend, get_qc_overview_from_backend,
    get_read_quality_from_backend, get_taxonomic_diversity_from_backend,
    get_outlier_detection_from_backend, get_positive_control_validation_from_backend
)

bp = Blueprint('seqruns', __name__, template_folder='templates')


def group_samples_by_seqrun(samples):
    """Group samples by sequencing run ID and calculate statistics"""
    seqruns = defaultdict(lambda: {
        'samples': [],
        'total_samples': 0,
        'approved_samples': 0,
        'true_hits': 0,
        'spikes_detected': 0,
        'pipeline_status': 'completed',
        'created_date': None,
        'pipeline_software': None,
        'pipeline_files': {}
    })

    for sample in samples:
        seqrun_id = sample.get('sequencing_run_id')
        if not seqrun_id:
            continue

        seqrun_data = seqruns[seqrun_id]
        seqrun_data['samples'].append(sample)
        seqrun_data['total_samples'] += 1

        # Calculate statistics
        if sample.get('qc') == 'approved':
            seqrun_data['approved_samples'] += 1

        if sample.get('flagged_top_hits'):
            seqrun_data['true_hits'] += 1

        if sample.get('spike'):
            seqrun_data['spikes_detected'] += 1

        if not seqrun_data['created_date'] or sample.get('created_date'):
            seqrun_data['created_date'] = sample.get('created_date')

    # Convert to list and add sequencing_run_id to each entry
    result = []
    for seqrun_id, data in seqruns.items():
        data['sequencing_run_id'] = seqrun_id
        result.append(data)

    # Sort by sequencing run ID (most recent first)
    result.sort(key=lambda x: x['sequencing_run_id'], reverse=True)
    return result

def get_seqrun_by_id(samples, seqrun_id):
    """Get specific sequencing run data by ID"""
    grouped = group_samples_by_seqrun(samples)

    # Try exact match first
    for seqrun in grouped:
        if seqrun['sequencing_run_id'] == seqrun_id:
            return seqrun

    # Try case insensitive match
    seqrun_id_lower = seqrun_id.lower()
    for seqrun in grouped:
        current_id = seqrun['sequencing_run_id']
        if current_id and current_id.lower() == seqrun_id_lower:
            return seqrun

    # Try with stripped whitespace
    seqrun_id_stripped = seqrun_id.strip()
    for seqrun in grouped:
        current_id = seqrun['sequencing_run_id']
        if current_id and current_id.strip() == seqrun_id_stripped:
            return seqrun

    return None


def generate_read_quality_plot_config(read_quality_data):
    """Generate Plotly configuration for read quality box plot analysis."""
    if not read_quality_data or read_quality_data.get('message'):
        return None

    metrics = read_quality_data.get('metrics', {})
    if not metrics:
        return None

    # Create subplots data
    subplot_data = []
    subplot_titles = ['Read Counts', 'Mean Quality', 'Mean Length', 'Total Bases']

    # Define metric configurations
    metric_configs = [
        ('processed_reads', 'Read Count', '#'),
        ('mean_quality', 'Quality Score', 'Q'),
        ('mean_length', 'Length', 'bp'),
        ('total_bases', 'Total Bases', 'bases')
    ]

    # Collect all values for each metric to calculate ranges
    metric_ranges = {}

    # Get sample IDs for hover text
    sample_ids = read_quality_data.get('sample_ids', {})
    unprocessed_sample_ids = sample_ids.get('unprocessed', [])
    processed_sample_ids = sample_ids.get('processed', [])

    for i, (metric_key, y_label, unit) in enumerate(metric_configs):
        metric_data = metrics.get(metric_key, {})

        # Collect all values for this metric to calculate range
        all_metric_values = []

        # Add unprocessed data first (left position)
        unprocessed_values = metric_data.get('unprocessed', [])
        if unprocessed_values:
            all_metric_values.extend(unprocessed_values)
            subplot_data.append({
                'y': unprocessed_values,
                'name': 'Unprocessed',
                'type': 'box',
                'boxpoints': 'all',
                'jitter': 0.3,
                'pointpos': -1.8,
                'marker': {'color': '#dc3545'},
                'legendgroup': 'unprocessed',
                'showlegend': i == 0,  # Only show legend for first subplot
                'xaxis': f'x{i+1}',
                'yaxis': f'y{i+1}',
                'text': [f"Sample: {sample_id}" for sample_id in unprocessed_sample_ids],
                'hovertemplate': f'<b>Unprocessed</b><br>{y_label}: %{{y:,.0f}} {unit}<br>%{{text}}<extra></extra>'
            })

        # Add processed data second (right position)
        processed_values = metric_data.get('processed', [])
        if processed_values:
            all_metric_values.extend(processed_values)
            subplot_data.append({
                'y': processed_values,
                'name': 'Processed',
                'type': 'box',
                'boxpoints': 'all',
                'jitter': 0.3,
                'pointpos': 1.8,
                'marker': {'color': '#28a745'},
                'legendgroup': 'processed',
                'showlegend': i == 0,  # Only show legend for first subplot
                'xaxis': f'x{i+1}',
                'yaxis': f'y{i+1}',
                'text': [f"Sample: {sample_id}" for sample_id in processed_sample_ids],
                'hovertemplate': f'<b>Processed</b><br>{y_label}: %{{y:,.0f}} {unit}<br>%{{text}}<extra></extra>'
            })

        # Calculate padded range for this metric
        if all_metric_values:
            y_min = min(all_metric_values)
            y_max = max(all_metric_values)
            y_range = y_max - y_min

            # Different padding strategies based on metric type
            if metric_key == 'mean_quality':
                # Quality scores: fixed padding of ±0.5 points (or 10% of range)
                padding = max(0.5, y_range * 0.1)
                y_min_padded = max(0, y_min - padding)  # Quality can't go below 0
                y_max_padded = min(50, y_max + padding)  # Cap at reasonable quality max
            elif metric_key in ['processed_reads', 'total_bases']:
                # Count-based metrics: can't have negative values
                y_min_padded = max(0, y_min - y_range * 0.1)
                y_max_padded = y_max + y_range * 0.15
            else:
                # Length metrics: allow padding below minimum
                y_min_padded = y_min - y_range * 0.1
                y_max_padded = y_max + y_range * 0.15
                # Only enforce 0 minimum if data is very close to 0
                if y_min < 100:  # For length values below 100bp
                    y_min_padded = max(0, y_min_padded)

            metric_ranges[f'y{i+1}'] = [y_min_padded, y_max_padded]
        else:
            # Default range if no data
            metric_ranges[f'y{i+1}'] = [0, 100]

    if not subplot_data:
        return None

    # Layout with subplots (2x2 grid)
    layout = {
        'title': {
            'text': f'Read Quality Analysis - {read_quality_data.get("sequencing_run_id", "")}',
            'x': 0.5,
            'font': {'size': 16}
        },
        'grid': {'rows': 2, 'columns': 2, 'pattern': 'independent'},
        'showlegend': True,
        'legend': {'x': 1.02, 'y': 1},
        # Subplot annotations
        'annotations': [
            {'text': subtitle, 'x': x_pos, 'y': y_pos, 'xref': 'paper', 'yref': 'paper', 
             'xanchor': 'center', 'yanchor': 'bottom', 'showarrow': False, 'font': {'size': 12}}
            for subtitle, x_pos, y_pos in zip(subplot_titles, [0.225, 0.775, 0.225, 0.775], [1, 1, 0.48, 0.48])
        ],
        # Individual subplot axes with calculated ranges
        'xaxis1': {'domain': [0, 0.45], 'anchor': 'y1'},
        'yaxis1': {'domain': [0.52, 1], 'anchor': 'x1', 'title': 'Read Count', 'range': metric_ranges.get('y1', [0, 100])},
        'xaxis2': {'domain': [0.55, 1], 'anchor': 'y2'},
        'yaxis2': {'domain': [0.52, 1], 'anchor': 'x2', 'title': 'Quality Score', 'range': metric_ranges.get('y2', [0, 50])},
        'xaxis3': {'domain': [0, 0.45], 'anchor': 'y3'},
        'yaxis3': {'domain': [0, 0.48], 'anchor': 'x3', 'title': 'Length (bp)', 'range': metric_ranges.get('y3', [0, 1000])},
        'xaxis4': {'domain': [0.55, 1], 'anchor': 'y4'},
        'yaxis4': {'domain': [0, 0.48], 'anchor': 'x4', 'title': 'Total Bases', 'range': metric_ranges.get('y4', [0, 1000000])}
    }

    return {
        'data': subplot_data,
        'layout': layout,
        'config': {
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True,
            'modeBarButtonsToRemove': ['select2d', 'lasso2d']
        }
    }


def generate_contamination_plot_config(contamination_data):
    """Generate Plotly configuration for contamination analysis."""
    if not contamination_data or contamination_data.get('message'):
        return None

    species_analysis = contamination_data.get('species_analysis', {})
    if not species_analysis:
        return None

    # Create box plot data and collect all abundance values for range calculation
    plot_data = []
    all_abundances = []
    for species, analysis in species_analysis.items():
        abundances = analysis.get('abundances', [])
        if abundances:  # Only include species with actual abundance data
            all_abundances.extend(abundances)
            # Get sample IDs that correspond to each abundance value
            detected_sample_ids = analysis.get('detected_in_samples', [])

            plot_data.append({
                'y': abundances,
                'name': species,
                'type': 'box',
                'boxpoints': 'all',  # Show all data points
                'jitter': 0.3,
                'pointpos': -1.8,
                'text': [f"Sample: {sample_id}" for sample_id in detected_sample_ids],
                'hovertemplate': f'<b>{species}</b><br>Abundance: %{{y:.2f}}%<br>%{{text}}<extra></extra>'
            })

    if not plot_data:
        return None

    # Calculate y-axis range with padding
    if all_abundances:
        y_min = min(all_abundances)
        y_max = max(all_abundances)
        y_range = y_max - y_min

        # Add 15% padding above max and 10% below min (or at least 0.5% for very small values)
        padding_below = max(y_range * 0.1, 0.5)
        padding_above = max(y_range * 0.15, 0.5)

        y_min_padded = y_min - padding_below
        y_max_padded = y_max + padding_above

        # Only enforce 0 minimum if the data actually contains very low values (< 1%)
        if y_min < 1.0:
            y_min_padded = max(0, y_min_padded)
    else:
        y_min_padded, y_max_padded = 0, 10

    # Layout configuration
    layout = {
        'title': {
            'text': 'Contamination Analysis - Species from Negative Controls',
            'x': 0.5,
            'font': {'size': 16}
        },
        'xaxis': {
            'title': 'Species',
            'tickangle': -45 if len(plot_data) > 3 else 0
        },
        'yaxis': {
            'title': 'Abundance (%)',
            'type': 'log' if any(max(trace['y']) > 100 for trace in plot_data if trace['y']) else 'linear',
            'range': [y_min_padded, y_max_padded]
        },
        'margin': {'l': 80, 'r': 50, 'b': 120, 't': 80, 'pad': 10},
        'showlegend': False,
        'plot_bgcolor': '#f8f9fa',
        'paper_bgcolor': 'white'
    }

    return {
        'data': plot_data,
        'layout': layout,
        'config': {
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'autoScale2d'],
            'responsive': True
        }
    }


def get_contamination_data_for_seqrun(seqrun_id):
    """Get contamination analysis data for a sequencing run via API."""
    try:
        return get_contamination_analysis_from_backend(seqrun_id)
    except Exception as e:
        print(f"Error getting contamination data: {e}")
        return {'message': f'Error analyzing contamination: {str(e)}', 'contaminating_species': []}


@bp.route('/seqruns')
@login_required
def seqruns_page():
    """Display list of sequencing runs"""
    try:
        # Get all samples and group by sequencing run
        samples = get_samples_from_backend()
        seqruns = group_samples_by_seqrun(samples)
        return render_template('seqruns.html', seqruns=seqruns)
    except ValueError as e:
        # Authentication error
        return render_template('seqruns.html', seqruns=[], error='Backend authentication required')
    except Exception as e:
        # Other errors
        return render_template('seqruns.html', seqruns=[], error=str(e))

@bp.route('/seqruns/<seqrun_id>/samples')
@login_required
def seqrun_samples(seqrun_id):
    """Display samples table for a specific sequencing run"""
    try:
        # URL decode the seqrun_id in case there are encoded characters
        decoded_seqrun_id = urllib.parse.unquote(seqrun_id)

        # Get all samples and filter for this sequencing run
        all_samples = get_samples_from_backend()

        # Try both original and decoded IDs
        seqrun = get_seqrun_by_id(all_samples, seqrun_id)
        if seqrun is None and decoded_seqrun_id != seqrun_id:
            seqrun = get_seqrun_by_id(all_samples, decoded_seqrun_id)

        if seqrun is None:
            # Get all available seqrun IDs for debugging
            all_seqruns = group_samples_by_seqrun(all_samples)
            available_ids = [sr['sequencing_run_id'] for sr in all_seqruns]

            error_msg = f"""
            Sequencing run not found!

            Requested ID: '{seqrun_id}'
            Decoded ID: '{decoded_seqrun_id}'

            Available sequencing run IDs:
            {', '.join(available_ids)}

            Total samples: {len(all_samples)}
            Total sequencing runs: {len(all_seqruns)}
            """

            return render_template('seqrun_samples.html', 
                                 seqrun={'sequencing_run_id': seqrun_id, 'samples': []}, 
                                 samples=[], 
                                 error=error_msg)

        # Get filtered samples for this sequencing run
        filtered_samples = seqrun['samples']

        return render_template('seqrun_samples.html', 
                             seqrun=seqrun, 
                             samples=filtered_samples)
    except ValueError as e:
        # Authentication error
        return render_template('seqrun_samples.html', 
                             seqrun=None, 
                             samples=[], 
                             error='Backend authentication required')
    except Exception as e:
        # Other errors - show the actual error instead of hiding it
        import traceback
        error_details = traceback.format_exc()
        return render_template('seqrun_samples.html', 
                             seqrun={'sequencing_run_id': seqrun_id, 'samples': []}, 
                             samples=[], 
                             error=f"Error: {str(e)}<br><pre>{error_details}</pre>")

@bp.route('/seqruns/<seqrun_id>/information')
@login_required
def seqrun_information(seqrun_id):
    """Display information/overview page for a specific sequencing run"""
    try:
        # URL decode the seqrun_id in case there are encoded characters
        decoded_seqrun_id = urllib.parse.unquote(seqrun_id)

        # First try to get seqrun data directly from backend API
        try:
            seqrun = get_seqrun_from_backend(decoded_seqrun_id)
            if seqrun:
                print(f"✅ Successfully got seqrun data from backend API")
                analysis_base_path = get_analysis_path(seqrun)

                return render_template('seqrun_information.html', 
                                     seqrun=seqrun, 
                                     analysis_base_path=analysis_base_path)
        except Exception as api_error:
            print(f"⚠️ Backend API call failed: {api_error}")

        # Fallback: Build seqrun data from samples (like seqrun_samples does)
        print(f"🔄 Falling back to samples-based seqrun discovery for: {decoded_seqrun_id}")
        all_samples = get_samples_from_backend()

        # Try both original and decoded IDs
        seqrun = get_seqrun_by_id(all_samples, seqrun_id)
        if seqrun is None and decoded_seqrun_id != seqrun_id:
            seqrun = get_seqrun_by_id(all_samples, decoded_seqrun_id)

        if seqrun:
            analysis_base_path = get_analysis_path(seqrun)

            return render_template('seqrun_information.html', 
                                 seqrun=seqrun, 
                                 analysis_base_path=analysis_base_path)

        # If we get here, seqrun truly not found
        return render_template('seqrun_information.html', seqrun=None)

    except Exception as e:
        # If everything fails, still render the template but with empty seqrun
        print(f"❌ Error loading seqrun data for information: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('seqrun_information.html', seqrun=None)


@bp.route('/seqruns/<seqrun_id>/files/<file_type>')
@login_required
def seqrun_pipeline_file(seqrun_id, file_type):
    """Serve pipeline HTML files wrapped in Eyrie template for proper favicon and branding"""
    try:
        # URL decode the seqrun_id in case there are encoded characters
        decoded_seqrun_id = urllib.parse.unquote(seqrun_id)

        # Get seqrun data to determine file paths
        try:
            seqrun = get_seqrun_from_backend(decoded_seqrun_id)
        except Exception as api_error:
            # Fallback: Build seqrun data from samples
            print(f"⚠️ Backend API call failed, using samples fallback: {api_error}")
            all_samples = get_samples_from_backend()
            seqrun = get_seqrun_by_id(all_samples, decoded_seqrun_id)
            if not seqrun:
                seqrun = get_seqrun_by_id(all_samples, seqrun_id)

        if not seqrun or not seqrun.get('pipeline_files'):
            return render_template('seqrun_pipeline_file.html',
                                 seqrun_id=decoded_seqrun_id,
                                 file_type=file_type,
                                 error='Pipeline files not available for this sequencing run')

        # Map file types to file paths
        file_path_map = {
            'execution-report': seqrun['pipeline_files'].get('execution_report'),
            'execution-timeline': seqrun['pipeline_files'].get('execution_timeline'), 
            'pipeline-dag': seqrun['pipeline_files'].get('pipeline_dag')
        }

        file_path = file_path_map.get(file_type)
        if not file_path:
            return render_template('seqrun_pipeline_file.html',
                                 seqrun_id=decoded_seqrun_id,
                                 file_type=file_type, 
                                 error=f'File type "{file_type}" not found')

        # Construct full file path using analysis_base_path
        analysis_base_path = get_analysis_path(seqrun)
        full_file_path = f"{analysis_base_path}/{file_path}"

        return serve_analysis_file(full_file_path)

    except Exception as e:
        print(f"❌ Error serving pipeline file: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('seqrun_pipeline_file.html',
                             seqrun_id=seqrun_id,
                             file_type=file_type,
                             error=f'Error loading file: {str(e)}')


@bp.route('/seqruns/<seqrun_id>/quality-control')
@login_required
def seqrun_quality_control(seqrun_id):
    """Display quality control page for a specific sequencing run"""
    try:
        # URL decode the seqrun_id in case there are encoded characters
        decoded_seqrun_id = urllib.parse.unquote(seqrun_id)

        # First try to get seqrun data directly from backend API
        try:
            seqrun = get_seqrun_from_backend(decoded_seqrun_id)
            if seqrun:
                print(f"✅ Successfully got seqrun data from backend API")

                # Get all QC analyses data
                qc_overview_data = get_qc_overview_from_backend(decoded_seqrun_id)
                read_quality_data = get_read_quality_from_backend(decoded_seqrun_id)
                taxonomic_diversity_data = get_taxonomic_diversity_from_backend(decoded_seqrun_id)
                outlier_detection_data = get_outlier_detection_from_backend(decoded_seqrun_id)
                positive_control_data = get_positive_control_validation_from_backend(decoded_seqrun_id)
                contamination_data = get_contamination_data_for_seqrun(decoded_seqrun_id)

                # Generate plot configurations
                contamination_plot_config = generate_contamination_plot_config(contamination_data)
                read_quality_plot_config = generate_read_quality_plot_config(read_quality_data)

                return render_template('seqrun_quality_control.html', 
                                     seqrun=seqrun,
                                     qc_overview_data=qc_overview_data,
                                     read_quality_data=read_quality_data,
                                     taxonomic_diversity_data=taxonomic_diversity_data,
                                     outlier_detection_data=outlier_detection_data,
                                     positive_control_data=positive_control_data,
                                     contamination_data=contamination_data,
                                     contamination_plot_config=contamination_plot_config,
                                     read_quality_plot_config=read_quality_plot_config)
        except Exception as api_error:
            print(f"⚠️ Backend API call failed: {api_error}")

        # Fallback: Build seqrun data from samples (like seqrun_samples does)
        print(f"🔄 Falling back to samples-based seqrun discovery for: {decoded_seqrun_id}")
        all_samples = get_samples_from_backend()

        # Try both original and decoded IDs
        seqrun = get_seqrun_by_id(all_samples, seqrun_id)
        if seqrun is None and decoded_seqrun_id != seqrun_id:
            seqrun = get_seqrun_by_id(all_samples, decoded_seqrun_id)

        if seqrun:
            # Get all QC analyses data (fallback)
            qc_overview_data = get_qc_overview_from_backend(decoded_seqrun_id)
            read_quality_data = get_read_quality_from_backend(decoded_seqrun_id)
            taxonomic_diversity_data = get_taxonomic_diversity_from_backend(decoded_seqrun_id)
            outlier_detection_data = get_outlier_detection_from_backend(decoded_seqrun_id)
            positive_control_data = get_positive_control_validation_from_backend(decoded_seqrun_id)
            contamination_data = get_contamination_data_for_seqrun(decoded_seqrun_id)

            # Generate plot configurations
            contamination_plot_config = generate_contamination_plot_config(contamination_data)
            read_quality_plot_config = generate_read_quality_plot_config(read_quality_data)

            return render_template('seqrun_quality_control.html', 
                                 seqrun=seqrun,
                                 qc_overview_data=qc_overview_data,
                                 read_quality_data=read_quality_data,
                                 taxonomic_diversity_data=taxonomic_diversity_data,
                                 outlier_detection_data=outlier_detection_data,
                                 positive_control_data=positive_control_data,
                                 contamination_data=contamination_data,
                                 contamination_plot_config=contamination_plot_config,
                                 read_quality_plot_config=read_quality_plot_config)

        # If we get here, seqrun truly not found
        return render_template('seqrun_quality_control.html', seqrun=None)

    except Exception as e:
        # If everything fails, still render the template but with empty seqrun
        print(f"❌ Error loading seqrun data for quality control: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('seqrun_quality_control.html', seqrun=None)


@bp.route('/seqruns/<seqrun_id>/flag-contamination', methods=['GET'])
@login_required
def flag_contamination(seqrun_id):
    """Handle form submission to flag species as contamination"""

    try:
        species_name = request.args.get('species_name')
        if not species_name:
            flash('Species name is required', 'error')
            return redirect(url_for('seqruns.seqrun_quality_control', seqrun_id=seqrun_id))

        # URL decode the seqrun_id
        decoded_seqrun_id = urllib.parse.unquote(seqrun_id)

        # Call backend API to flag the contamination
        try:

            # Get backend URL (similar to other API calls)
            backend_url = settings.internal_backend_url

            # Get session token
            session_token = session.get('backend_token')
            if not session_token:
                flash('Authentication required', 'error')
                return redirect(url_for('seqruns.seqrun_quality_control', seqrun_id=seqrun_id))

            # Make API call to flag contamination
            headers = {
                'Authorization': f'Bearer {session_token}'
            }

            params = {'species_name': species_name}

            url = f"{backend_url}/api/seqruns/{decoded_seqrun_id}/flag-contamination"
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                result = response.json()
                flash(f"Successfully flagged '{species_name}' as contamination in {result.get('flagged_samples', 0)} sample(s)", 'success')
            else:
                flash(f"Failed to flag contamination: {response.status_code}", 'error')

        except Exception as api_error:
            flash(f"Error flagging contamination: {str(api_error)}", 'error')

        return redirect(url_for('seqruns.seqrun_quality_control', seqrun_id=seqrun_id))

    except Exception as e:
        flash(f"Error processing request: {str(e)}", 'error')
        return redirect(url_for('seqruns.seqrun_quality_control', seqrun_id=seqrun_id))
