"""
MA Truck Charging Site Selection Dashboard
Full GeoPandas version with authentication
"""
import os
import logging
from flask import Flask, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from dash import Dash
import dash_bootstrap_components as dbc

# Import auth components
from auth import auth, login_manager

# Import database components
from db import engine, Base
import models  # registers User model

# Import Dash components
from layout import create_layout
from callbacks import register_callbacks

# Import data loader (this will precompute scores on first import)
from data_loader import get_selector

# ==========================
# LOGGING CONFIGURATION
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================
# DATABASE INITIALIZATION
# ==========================
logger.info("Initializing database...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables created/verified")

# ==========================
# FLASK SERVER SETUP
# ==========================
server = Flask(__name__)
server.secret_key = os.environ.get("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")

# Initialize Flask-Login
login_manager.init_app(server)
login_manager.login_view = 'auth.login'  # Redirect to login page when not authenticated

# Register Flask auth blueprint
server.register_blueprint(auth)

logger.info("Flask server initialized with authentication")

# ==========================
# FLASK ROUTES
# ==========================

@server.route("/")
@server.route("/home")
def index():
    """Redirect root to dashboard or login"""
    if current_user.is_authenticated:
        return redirect("/dash/")
    return redirect(url_for('auth.login'))

@server.route("/health")
def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "app": "MA Truck Charging Site Selector"}, 200

# ==========================
# DASH APP SETUP
# ==========================
logger.info("Initializing Dash application...")

app = Dash(
    __name__,
    server=server,
    url_base_pathname="/dash/",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="MA Truck Charging Site Selector",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Set the layout
app.layout = create_layout()

# Register all callbacks
register_callbacks(app)

logger.info("Dash application initialized")

# ==========================
# PROTECT DASH APP WITH LOGIN
# ==========================

@server.before_request
def check_login():
    """
    Protect all /dash/ routes with authentication.
    This runs before every request to check if user is authenticated.
    """
    # List of paths that don't require authentication
    public_paths = [
        '/login',
        '/register',
        '/logout',
        '/health',
        '/static/',  # Allow static files
        '/_dash',    # Allow Dash internal requests after auth check
    ]
   
    # Check if the current path requires authentication
    if request.path.startswith('/dash/'):
        if not current_user.is_authenticated:
            logger.warning(f"Unauthenticated access attempt to {request.path}")
            return redirect(url_for('auth.login', next=request.path))
   
    # Allow all other requests to continue
    return None

logger.info("Authentication protection applied to /dash/ routes")

# ==========================
# PRELOAD DATA ON STARTUP
# ==========================
logger.info("=" * 70)
logger.info("PRELOADING TRUCK CHARGING SITE SELECTOR")
logger.info("=" * 70)

try:
    # This triggers the data loading and score computation
    # The get_selector() function caches the result
    selector = get_selector()
   
    logger.info("✓ Selector preloaded successfully")
    logger.info(f"✓ Data loaded with {len(selector.gdf)} census tracts")
    logger.info("✓ Initial composite scores calculated")
    logger.info("=" * 70)
    logger.info("APPLICATION READY")
    logger.info("=" * 70)
   
except Exception as e:
    logger.error("=" * 70)
    logger.error("FAILED TO PRELOAD SELECTOR")
    logger.error(f"Error: {e}", exc_info=True)
    logger.error("=" * 70)
    logger.error("Application may not function correctly")
    logger.error("Please check your data file path and selector.py implementation")

# ==========================
# RUN SERVER
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_ENV") == "development"
   
    logger.info(f"Starting server on port {port} (debug={debug})")
   
    server.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
