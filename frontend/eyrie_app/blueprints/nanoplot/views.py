from flask import Blueprint, render_template

bp = Blueprint('nanoplot', __name__, 
               url_prefix='/nanoplot',
               template_folder='templates')

@bp.route('/')
def nanoplot():
    """Nanoplot view with button panel and side-by-side comparison"""
    return render_template('nanoplot.html')
