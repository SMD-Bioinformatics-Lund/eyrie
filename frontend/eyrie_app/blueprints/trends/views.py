"""Views for trends analysis."""

from flask import Blueprint, render_template
from flask_login import login_required

trends_bp = Blueprint('trends', __name__, 
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='')


@trends_bp.route('/trends')
@login_required
def index():
    """Display trends dashboard."""
    return render_template('trends.html')
