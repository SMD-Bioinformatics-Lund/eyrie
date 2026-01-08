from flask import Blueprint, render_template, request, jsonify, url_for, redirect
from flask_login import login_required, current_user
import urllib.parse
from collections import defaultdict
from ...eyrie import get_samples_from_backend, serve_analysis_file, get_seqrun_from_backend, get_analysis_path

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
                return render_template('seqrun_information.html', seqrun=seqrun, analysis_base_path=analysis_base_path)
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
            return render_template('seqrun_information.html', seqrun=seqrun, analysis_base_path=analysis_base_path)

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
