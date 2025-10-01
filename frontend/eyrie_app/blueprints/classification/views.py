from flask import Blueprint, render_template

bp = Blueprint('classification', __name__, 
               url_prefix='/classification',
               template_folder='templates')

@bp.route('/')
def classification():
    """Classification view with Krona plot and contamination table"""
    return render_template('classification.html')
