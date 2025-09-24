from flask import Blueprint, send_file

bp = Blueprint('login', __name__, url_prefix='')

@bp.route("/login")
def login_page():
    return send_file('blueprints/login/templates/index.html')