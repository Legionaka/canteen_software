from flask import Blueprint, render_template, request, redirect, url_for
from utils import login_required, role_required
from models import db, MenuItem

student_bp = Blueprint('student', __name__)