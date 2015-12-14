"""This module includes most of the routes for the app.

It includes endpoints for viewing and modifying the catalog.
"""

import httplib2
import requests
import json

from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import jsonify
from flask import session

from catalog import app
from catalog import db
from database_setup import Base, User, Category, Item



@app.route("/hello/")
def hello():
    output = "<html>"
    output += "<body>"
    output += "<p>Hello World!</p>"
    output += "<p>Welcome to the item catalog web app :)</p>"
    output += "<p><a href = " + url_for("view_catalog") + ">View catalog</a></p>"
    output += "</body>"
    output += "</html>"
    return output


################################################################################
# View catalog
################################################################################

@app.route("/")
@app.route("/catalog/")
def view_catalog():
    """Catalog homepage."""
    categories = db.query(Category).all()
    items = db.query(Item).all()
    return render_template("catalog.html", categories = categories, items = items)


@app.route("/catalog/category/<int:category_id>/")
def view_category(category_id):
    """View a specific category."""
    category = db.query(Category).filter_by(id = category_id).one()
    items = db.query(Item).filter_by(category_id = category.id)
    return render_template("category.html", category = category, items = items)


@app.route("/catalog/item/<int:item_id>/")
def view_item(item_id):
    """View a specific item."""
    item = db.query(Item).filter_by(id = item_id).one()
    return render_template("item.html", item = item)


################################################################################
# Create/edit/delete items
################################################################################

@app.route("/catalog/item/new/", methods = ['GET', 'POST'])
def new_item():
    """Create new item."""
    if request.method != 'POST':
        categories = db.query(Category).order_by(Category.name).all() # sort alphabetically
        return render_template('new_item.html', categories = categories)

    # get image file
    form_file = request.files['image']
    img_filename = None
    if form_file:
        filename = secure_filename(form_file.filename)
        filename = generate_unique_filename(filename)
        form_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_filename = filename

    # create item
    new_item = Item(
        name = request.form['name'],
        description = request.form['description'],
        category_id = request.form['category_id'],
        image = img_filename,
        user_id = session['user_id'])
    db.add(new_item)
    db.commit()

    return redirect(url_for('view_item', item_id = new_item.id))

@app.route("/catalog/item/<int:item_id>/edit/", methods = ['GET', 'POST'])
def edit_item(item_id):
    """Edit an item."""
    item = db.query(Item).filter_by(id = item_id).one()
    if request.method != 'POST':
        categories = db.query(Category).order_by(Category.name).all() # sort alphabetically
        return render_template('edit_item.html', item = item, categories = categories)

    # get image file
    form_file = request.files['image']
    img_filename = None
    if form_file:
        filename = secure_filename(form_file.filename)
        filename = generate_unique_filename(filename)
        form_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_filename = filename

    # edit item
    item.name = request.form['name']
    item.description = request.form['description']
    item.category_id = request.form['category_id']
    # only replace image if new image is uploaded
    if img_filename:
        item.image = img_filename
    db.add(item)
    db.commit()

    return redirect(url_for('view_item', item_id = item.id))

@app.route("/catalog/item/<int:item_id>/delete/", methods = ['GET', 'POST'])
def delete_item(item_id):
    """Delete an item."""
    item = db.query(Item).filter_by(id = item_id).one()
    if request.method != 'POST':
        categories = db.query(Category).order_by(Category.name).all() # sort alphabetically
        return render_template('delete_item.html', item = item, categories = categories)
    db.delete(item)
    db.commit()
    return redirect(url_for('view_catalog'))


################################################################################
# Image upload
################################################################################

import os
import datetime
import string
import random
import uuid
from werkzeug import secure_filename
from flask import send_from_directory

app_dir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(app_dir, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def generate_random_string():
    """Generate a random string with alphabetic characters and digits."""
    alpha = string.ascii_lowercase + string.ascii_uppercase + string.digits
    rand_str = "".join(random.choice(alpha) for x in xrange(32))
    return rand_str

def generate_unique_filename(original_filename):
    """Generate a unique name for a file.

    The current implementation does not actually guarantee uniqueness,
    but the probability of generating the same name twice is very low.

    The generated file names include the date and time, and a random UUID.

    Args:
      original_filename: the original name of the file.
    Returns:
      A file name with the same extension as the original file, and
      which is almost surely unique.
    """
    # keep file extension, in lower case
    ext = os.path.splitext(original_filename)[1].strip().lower()

    # current date and time
    date_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # generate random uuid
    uuid_hex = uuid.uuid4().hex

    filename = "_".join([date_time, uuid_hex, ext])
    return filename

@app.route("/upload/", methods = ['GET', 'POST'])
def upload():
    """Upload an image file."""
    if request.method != 'POST':
        return render_template('upload.html')
    form_file = request.files['image']
    if form_file:
        filename = secure_filename(form_file.filename)
        filename = generate_unique_filename(filename)
        form_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('view_image', filename = filename))


@app.route("/image/<string:filename>/")
def view_image(filename):
    """View uploaded image."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_image_url(filename):
    """Get URL for an image file.

    If no file is specified, returns a URL for a place holder image.

    Note that this method does not check if the file actually exists.
    """
    if filename:
        return url_for("view_image", filename = filename)
    else:
        return "https://placehold.it/300x300.png?text=No+image"

################################################################################

# Expose utility functions to templates
# http://flask.pocoo.org/docs/0.10/templating/
@app.context_processor
def utility_processor():
    return dict(get_image_url = get_image_url)

################################################################################