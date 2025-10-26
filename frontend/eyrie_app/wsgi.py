"""Production WSGI entrypoint for gunicorn"""

import logging
import os
import threading

# Debug threading issues
original_Thread = threading.Thread
def debug_thread_creation(*args, **kwargs):
    import traceback
    print("=== THREAD CREATION DETECTED ===")
    print("Stack trace:")
    traceback.print_stack()
    print("Args:", args)
    print("Kwargs:", kwargs)
    print("=== END THREAD DEBUG ===")
    return original_Thread(*args, **kwargs)

threading.Thread = debug_thread_creation

from .app import create_app

# Create the Flask application instance
app = create_app()

# Configure logging for gunicorn
if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# For development only - gunicorn will handle this in production
if __name__ == "__main__":
    # Development server fallback (not used in production containers)
    debug_mode = os.environ.get('ENVIRONMENT', 'production') != 'production'
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=debug_mode, 
        use_reloader=False
    )
