import json

from flask import jsonify
from flask import session as login_session

from database_setup import User

from catalog import app
from catalog import db_session


################################################################################
# Users
################################################################################

def create_user(login_session):
    newUser = User(
        name = login_session['username'],
        email = login_session['email'],
        picture = login_session['picture'])
    db_session.add(newUser)
    db_session.commit()
    user = db_session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def get_user_id(email):
    try:
        user = db_session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def get_user_info(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return user

@app.route('/users/json/')
def users_json():
    users = db_session.query(User).all()
    return jsonify(users = [u.serialize for u in users])

################################################################################
