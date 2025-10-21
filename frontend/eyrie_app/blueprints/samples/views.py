from flask import Blueprint, render_template, send_file
from ...auth.decorators import login_required

bp = Blueprint('samples', __name__, url_prefix='', template_folder='templates')

@bp.route("/")
@login_required
def root(current_user=None):
    return render_template('index.html', current_user=current_user)

@bp.route("/samples")
@login_required
def samples_page(current_user=None):
    return render_template('index.html', current_user=current_user)
