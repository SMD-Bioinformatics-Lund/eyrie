from flask import Blueprint, render_template
from ...auth.decorators import admin_required_view

bp = Blueprint('admin', __name__, url_prefix='', template_folder='templates')

@bp.route("/admin")
@admin_required_view
def admin_page(current_user=None):
    return render_template('dashboard.html', current_user=current_user)
