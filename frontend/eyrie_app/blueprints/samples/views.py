from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('samples', __name__, url_prefix='', template_folder='templates')

@bp.route("/")
@login_required
def root():
    return render_template('samples.html')

@bp.route("/samples")
@login_required
def samples_page():
    return render_template('samples.html')
