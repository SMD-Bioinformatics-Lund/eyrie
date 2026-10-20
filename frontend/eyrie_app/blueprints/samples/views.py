from urllib.parse import urlencode

from flask import Blueprint, Response, abort, redirect, render_template, request, jsonify, url_for
from werkzeug.exceptions import HTTPException
from ...auth import get_current_user, jwt_required
from ...utils.sample_filters import CATEGORIES, QC_STATUSES, filter_options, filter_samples
from ...eyrie import get_samples_from_backend, get_sample_from_backend, update_sample_qc, update_sample_comment, update_sample_category, update_sample_species_flags, create_sample

bp = Blueprint('samples', __name__, url_prefix='', template_folder='templates')

EXPORT_ID_FIELDS = ['lims_id', 'sample_id', 'sample_name']
EXPORT_COLUMNS = ['sample_id', 'parameter_name', 'parameter_value', 'comment']


def render_samples_page():
    try:
        samples = get_samples_from_backend(view='table')
        return render_template('samples.html', samples=filter_samples(samples, request.args),
                               filter_options=filter_options(samples))
    except HTTPException:
        raise  # Let Flask handle HTTP errors (401, 403, etc.)
    except Exception as e:
        # If backend is unavailable, show page with error message
        return render_template('samples.html', samples=[], filter_options=filter_options([]), error=str(e))


@bp.route("/")
@jwt_required
def root():
    """Redirect to samples page"""
    return render_samples_page()

@bp.route("/samples")
@jwt_required
def samples_page():
    """Display samples page"""
    return render_samples_page()


def back_to_table(message):
    next_url = request.form.get('next', '')
    if not next_url.startswith('/') or next_url.startswith('//'):
        next_url = url_for('samples.samples_page')
    separator = '&' if '?' in next_url else '?'
    return redirect(f"{next_url}{separator}{urlencode({'message': message})}")


def sample_count(sample_ids):
    return f"{len(sample_ids)} sample{'' if len(sample_ids) == 1 else 's'}"


def selected_sample_ids():
    return request.form.getlist('sample_ids')


def tsv_value(value):
    return ' '.join(str(value or '').split())


def export_rows(sample, id_field):
    sample_id = sample.get(id_field)
    comments = sample.get('comments') if isinstance(sample.get('comments'), dict) else {}
    qc_comments = '; '.join(c.get('comment', '') for c in comments.get('qc') or [])
    yield [sample_id, 'qc_status', sample.get('qc'), qc_comments]
    yield [sample_id, 'top_hits', ', '.join(sample.get('flagged_top_hits') or []), '']
    yield [sample_id, 'contaminants', ', '.join(sample.get('flagged_contaminants') or []), '']


@bp.route("/samples/export", methods=['POST'])
@jwt_required
def export_samples():
    """Export QC status, top hits and contaminants of the selected samples as TSV"""
    id_field = request.form.get('id_field', 'lims_id')
    if id_field not in EXPORT_ID_FIELDS:
        abort(400)
    selected = set(selected_sample_ids())
    if not selected:
        return back_to_table('No samples selected')
    samples = [s for s in get_samples_from_backend(view='table') if s.get('sample_id') in selected]
    rows = [EXPORT_COLUMNS] + [row for sample in samples for row in export_rows(sample, id_field)]
    tsv = ''.join('\t'.join(tsv_value(value) for value in row) + '\n' for row in rows)
    return Response(tsv, mimetype='text/tab-separated-values',
                    headers={'Content-Disposition': 'attachment; filename=samples.tsv'})


@bp.route("/samples/qc", methods=['POST'])
@jwt_required
def set_samples_qc():
    """Set the QC status of the selected samples"""
    qc = request.form.get('qc')
    if qc not in QC_STATUSES:
        abort(400)
    sample_ids = selected_sample_ids()
    if not sample_ids:
        return back_to_table('No samples selected')
    comment = request.form.get('qc_comment', '').strip() or None
    for sample_id in sample_ids:
        update_sample_qc(sample_id, {'qc': qc, 'comment': comment})
    return back_to_table(f'QC set to {qc} for {sample_count(sample_ids)}')


@bp.route("/samples/category", methods=['POST'])
@jwt_required
def update_samples_category():
    """Update the category of the selected samples (admin only)"""
    user = get_current_user()
    if not user or user.role != 'admin':
        abort(403)
    category = request.form.get('category')
    if category not in CATEGORIES:
        abort(400)
    sample_ids = selected_sample_ids()
    if not sample_ids:
        return back_to_table('No samples selected')
    for sample_id in sample_ids:
        update_sample_category(sample_id, category)
    return back_to_table(f'Category set to {category} for {sample_count(sample_ids)}')


# API Endpoints
@bp.route("/api/samples", methods=['GET'])
@jwt_required
def get_samples_api():
    """Get samples from backend API"""
    try:
        data = get_samples_from_backend()
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples", methods=['POST'])
@jwt_required
def create_sample_api():
    """Create a new sample"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        result = create_sample(data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>", methods=['GET'])
@jwt_required
def get_sample_api(sample_id):
    """Get specific sample from backend API"""
    try:
        data = get_sample_from_backend(sample_id)
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>/qc", methods=['PUT'])
@jwt_required
def update_qc_api(sample_id):
    """Update sample QC status"""
    try:
        data = request.get_json()
        result = update_sample_qc(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>/comment", methods=['PUT'])
@jwt_required
def update_comment_api(sample_id):
    """Update sample comment"""
    try:
        data = request.get_json()
        result = update_sample_comment(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/api/samples/<sample_id>/species-flags", methods=['PUT'])
@jwt_required
def update_species_flags_api(sample_id):
    """Update sample species flags"""
    try:
        data = request.get_json()
        result = update_sample_species_flags(sample_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': 'Backend authentication required'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
