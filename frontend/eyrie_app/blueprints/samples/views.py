from flask import Blueprint, render_template, send_file

bp = Blueprint('samples', __name__, url_prefix='')

@bp.route("/")
def root():
    return send_file('blueprints/samples/templates/index.html')

@bp.route("/samples")
def samples_page():
    return send_file('blueprints/samples/templates/index.html')
