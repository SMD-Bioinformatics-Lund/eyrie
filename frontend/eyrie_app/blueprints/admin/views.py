from flask import Blueprint, send_file

bp = Blueprint('admin', __name__, url_prefix='')

@bp.route("/admin")
def admin_page():
    return send_file('blueprints/admin/templates/dashboard.html')