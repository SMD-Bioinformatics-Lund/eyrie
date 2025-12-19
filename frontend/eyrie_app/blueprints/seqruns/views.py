from flask import Blueprint, render_template, request, jsonify, url_for, redirect, send_file
from flask_login import login_required, current_user
import os
import glob
import re
import urllib.parse
from collections import defaultdict
from datetime import datetime
from ...eyrie import get_samples_from_backend

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
        'run_date': None,
        'created_date': None
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
            
        # Set metadata from first sample or most recent
        if not seqrun_data['run_date'] or sample.get('sequencing_run_date'):
            seqrun_data['run_date'] = sample.get('sequencing_run_date')
            
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

def parse_datetime_from_filename(filename):
    """Extract datetime from filename with format YYYY-MM-DD_HH-MM-SS"""
    match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', filename)
    if match:
        datetime_str = match.group(1)
        return datetime.strptime(datetime_str, '%Y-%m-%d_%H-%M-%S')
    return datetime.min

def get_latest_file_by_pattern(pipeline_path, pattern):
    """Get the latest file matching the pattern based on datetime in filename"""
    files = glob.glob(os.path.join(pipeline_path, pattern))
    if not files:
        return None
    
    # Sort by datetime extracted from filename
    files.sort(key=parse_datetime_from_filename, reverse=True)
    return files[0]

def get_pipeline_path(seqrun_id):
    """Get the pipeline_info path for a sequencing run"""
    # Base path from the analysis-files directory structure
    base_path = "/app/analysis-files/results"
    pipeline_path = os.path.join(base_path, seqrun_id, "pipeline_info")
    
    if not os.path.exists(pipeline_path):
        return None
    return pipeline_path

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
        # Get all samples and find the specific sequencing run
        samples = get_samples_from_backend()
        seqrun = get_seqrun_by_id(samples, seqrun_id)
        
        if seqrun is None:
            return redirect(url_for('seqruns.seqruns_page'))
            
        return render_template('seqrun_information.html', seqrun=seqrun)
    except ValueError as e:
        # Authentication error
        return render_template('seqrun_information.html', seqrun=None, error='Backend authentication required')
    except Exception as e:
        # Other errors
        return redirect(url_for('seqruns.seqruns_page'))

@bp.route('/seqrun/<seqrun_id>/execution-report')
@login_required
def seqrun_execution_report(seqrun_id):
    """Serve the latest execution report HTML"""
    try:
        pipeline_path = get_pipeline_path(seqrun_id)
        if not pipeline_path:
            return "Pipeline info not found for this sequencing run", 404
            
        report_file = get_latest_file_by_pattern(pipeline_path, "execution_report_*.html")
        if not report_file:
            return "Execution report not found", 404
            
        return send_file(report_file, mimetype='text/html')
    except Exception as e:
        return f"Error: {str(e)}", 500

@bp.route('/seqrun/<seqrun_id>/execution-timeline')
@login_required
def seqrun_execution_timeline(seqrun_id):
    """Serve the latest execution timeline HTML"""
    try:
        pipeline_path = get_pipeline_path(seqrun_id)
        if not pipeline_path:
            return "Pipeline info not found for this sequencing run", 404
            
        timeline_file = get_latest_file_by_pattern(pipeline_path, "execution_timeline_*.html")
        if not timeline_file:
            return "Execution timeline not found", 404
            
        return send_file(timeline_file, mimetype='text/html')
    except Exception as e:
        return f"Error: {str(e)}", 500

@bp.route('/seqrun/<seqrun_id>/execution-trace')
@login_required
def seqrun_execution_trace(seqrun_id):
    """Serve the latest execution trace as parsed text"""
    try:
        pipeline_path = get_pipeline_path(seqrun_id)
        if not pipeline_path:
            return "Pipeline info not found for this sequencing run", 404
            
        trace_file = get_latest_file_by_pattern(pipeline_path, "execution_trace_*.txt")
        if not trace_file:
            return "Execution trace not found", 404
            
        return send_file(trace_file, mimetype='text/plain')
    except Exception as e:
        return f"Error: {str(e)}", 500

@bp.route('/seqrun/<seqrun_id>/params')
@login_required
def seqrun_params(seqrun_id):
    """Serve the latest params JSON"""
    try:
        pipeline_path = get_pipeline_path(seqrun_id)
        if not pipeline_path:
            return jsonify({"error": "Pipeline info not found for this sequencing run"}), 404
            
        params_file = get_latest_file_by_pattern(pipeline_path, "params_*.json")
        if not params_file:
            return jsonify({"error": "Parameters file not found"}), 404
            
        return send_file(params_file, mimetype='application/json')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/seqrun/<seqrun_id>/software-versions')
@login_required
def seqrun_software_versions(seqrun_id):
    """Serve the software versions YAML"""
    try:
        pipeline_path = get_pipeline_path(seqrun_id)
        if not pipeline_path:
            return "Pipeline info not found for this sequencing run", 404
            
        versions_file = os.path.join(pipeline_path, "software_versions.yml")
        if not os.path.exists(versions_file):
            return "Software versions file not found", 404
            
        return send_file(versions_file, mimetype='text/plain')
    except Exception as e:
        return f"Error: {str(e)}", 500