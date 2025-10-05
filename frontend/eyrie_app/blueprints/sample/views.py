from flask import Blueprint, render_template

bp = Blueprint('sample', __name__, url_prefix='', template_folder='templates')

@bp.route("/sample/<sample_id>")
def sample(sample_id):
    return render_template('sample.html', sample_id=sample_id)

@bp.route("/sample/<sample_id>/classification")
def sample_classification(sample_id):
    return render_template('sample_classification.html', sample_id=sample_id)

@bp.route("/sample/<sample_id>/nanoplot")
def sample_nanoplot(sample_id):
    return render_template('sample_nanoplot.html', sample_id=sample_id)
