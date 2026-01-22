"""
Authentication routes and logic
"""
from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from db import get_db, engine
from models import User, Base
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth = Blueprint("auth", __name__)

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Setup login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."


class UserModel(UserMixin):
    """Flask-Login user model"""
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        with get_db() as db:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                return UserModel(user.id, user.username)
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    return None


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Login route"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please provide both username and password", "error")
            return render_template("login.html")

        try:
            with get_db() as db:
                user = db.query(User).filter(User.username == username).first()

                if user and user.check_password(password):
                    user_obj = UserModel(user.id, user.username)
                    login_user(user_obj)
                   
                    logger.info(f"User logged in: {username}")
                   
                    # Redirect to next page or dashboard
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/'):
                        return redirect(next_page)
                   
                    # Redirect to dashboard after successful login
                    return redirect('/dash/')
                else:
                    flash("Invalid username or password", "error")
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash("An error occurred. Please try again.", "error")

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Registration route"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Validation
        if not username or not password:
            flash("Please provide both username and password", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("register.html")

        try:
            with get_db() as db:
                # Check if user exists
                existing = db.query(User).filter(User.username == username).first()
                if existing:
                    flash("Username already exists", "error")
                    return render_template("register.html")

                # Create new user
                new_user = User(username=username)
                new_user.set_password(password)
                db.add(new_user)
                db.commit()

                logger.info(f"New user registered: {username}")
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for("auth.login"))

        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash("An error occurred. Please try again.", "error")

    return render_template("register.html")


@auth.route("/logout")
@login_required
def logout():
    """Logout route"""
    username = getattr(current_user, 'username', 'Unknown')
    logout_user()
    logger.info(f"User logged out: {username}")
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))