"""Views for trends analysis."""

from flask import Blueprint, render_template

trends_bp = Blueprint('trends', __name__, 
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/trends')


@trends_bp.route('/')
def index():
    """Display trends dashboard."""
    return render_template('trends.html')
