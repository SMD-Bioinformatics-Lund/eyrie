from flask import Blueprint, send_file

bp = Blueprint('sample', __name__, url_prefix='')

@bp.route("/sample/<sample_id>")
def sample_detail(sample_id):
    return send_file('blueprints/sample/templates/detail.html')