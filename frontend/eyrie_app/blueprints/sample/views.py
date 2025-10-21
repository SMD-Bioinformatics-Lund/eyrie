from flask import Blueprint, render_template
from ...auth.decorators import login_required

bp = Blueprint('sample', __name__, url_prefix='', template_folder='templates')

@bp.route("/sample/<sample_id>")
@login_required
def sample(sample_id, current_user=None):
    return render_template('sample.html', sample_id=sample_id, current_user=current_user)

@bp.route("/sample/<sample_id>/classification")
@login_required
def sample_classification(sample_id, current_user=None):
    return render_template('sample_classification.html', sample_id=sample_id, current_user=current_user)

@bp.route("/sample/<sample_id>/nanoplot")
@login_required
def sample_nanoplot(sample_id, current_user=None):
    return render_template('sample_nanoplot.html', sample_id=sample_id, current_user=current_user)
