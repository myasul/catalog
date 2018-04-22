#!usr/bin/env python3

import os
import json
from functools import wraps
from collections import defaultdict

# Imports for Client-Server functionality
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

# Imports for CRUD functionality
from database_helper import *

# Imports for OAuth2 functionality
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import make_response, session as login_session
import random
import string
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secret_google.json',
                            'r').read())['web']['client_id']

# Upload folder location
UPLOAD_FOLDER = os.path.dirname('static/images/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DEFAULT_IMAGE = 'catalog.svg'


# Decorator for anonymous users trying to access restricted pages
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if is_logged_in():
            return f(*args, **kwargs)
        return redirect(url_for('show_main'))

    return wrap


# JSON APIs to view Category information
@app.route('/api/categories')
def show_all_categories_JSON():
    frame = get_all_categories_JSON()
    return jsonify(build_all_category_JSON(frame))


@app.route('/api/categories/<int:category_id>')
def show_category_items_JSON(category_id):
    return jsonify(build_category_JSON(category_id))


@app.route('/api/categories/<int:category_id>/<int:item_id>')
def show_category_item_JSON(category_id, item_id):
    return jsonify(build_category_JSON(category_id, item_id))


@app.route('/api/categories/authorized/<int:category_id>')
def show_authorization(category_id):
    return jsonify(is_authorized_to_modify_category(category_id))


@app.route('/api/categories/item_count/<int:category_id>')
def show_item_count(category_id):
    return jsonify(get_item_count(category_id))


# Create anti-forgery token
@app.route("/login")
def generate_token():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return login_session['state']


# Provide login functionality using Google's OAuth2
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        #Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'client_secret_google.json', scope='')
        oauth_flow.redirect_uri = 'http://localhost:5000'
        credentials = oauth_flow.step2_exchange(code)
        print("1")
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    response = validate_access_token(credentials)
    if response is not None:
        return response

    if is_connected(gplus_id):
        response = make_response(json.dumps("User is already connected."), 200)
        response.headers['Content-type'] = 'application/json'
        return response

    populate_login_session(credentials.access_token, gplus_id)

    response = make_response(json.dumps("User successfully logged in!"), 200)
    response.headers['Content-type'] = 'application/json'
    return response


# Logout user
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token', '')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    response = requests.post(
        'https://accounts.google.com/o/oauth2/revoke',
        params={'token': login_session.get('access_token', '')},
        headers={'content-type': 'application/x-www-form-urlencoded'})
    if response.status_code == 200:
        clear_login_session()
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Displays the home page
@app.route('/')
@app.route('/categories')
@app.route('/categories/')
@app.route('/categories/<int:category_id>')
def show_main(category_id=0):
    categories = get_all_categories()
    category = None
    items = None
    category_name = "dummy name"
    show_latest_items = True

    if category_id == 0:
        items = get_latest_items()
    else:
        category = get_category(category_id)
        category_name = category.name
        show_latest_items = False
    if login_session.get('username') is None:
        return render_template(
            'categories_anonymous.html',
            categories=categories,
            items=items,
            category_id=category_id,
            category_name=category_name,
            logged_in=is_logged_in(),
            show_latest_items=show_latest_items)
    return render_template(
        'categories.html',
        categories=categories,
        items=items,
        category_id=category_id,
        category_name=category_name,
        logged_in=is_logged_in(),
        show_latest_items=show_latest_items)


@app.route('/categories/create/', methods=['GET', 'POST'])
@login_required
def create_category():
    if request.method == 'POST':
        user_id = get_userid(login_session['email'])
        new_category = Category(
            name=request.form['category-name'], user_id=user_id)
        session.add(new_category)
        session.commit()
        return redirect(url_for('show_main'))
    else:
        return render_template('create_category.html', logged_in=True)


@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category_to_edit = get_category(category_id)
    if request.method == 'POST':
        if request.form['category-name']:
            category_to_edit.name = request.form['category-name']
            session.add(category_to_edit)
            session.commit()
            return redirect(url_for('show_main'))
    else:
        return render_template(
            'edit_category.html', category=category_to_edit, logged_in=True)


@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    category_to_delete = get_category(category_id)
    if request.method == 'POST':
        # Delete items under category first
        if get_item_count(category_id) > 0:
            items = get_all_items(category_id)
            for item in items:
                session.delete(item)
            session.commit()

        session.delete(category_to_delete)
        session.commit()
        return redirect(url_for('show_main'))
    else:
        return render_template(
            'delete_category.html',
            category=category_to_delete,
            logged_in=True)


# Displays a specific item
@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/',
    methods=['GET', 'POST'])
def show_category_item(category_id, item_id):
    item = get_item(item_id)
    if login_session.get(
            'username') is None or not is_authorized_to_modify_item(item.id):
        return render_template(
            'category_item_anonymous.html',
            category_id=category_id,
            item=item,
            logged_in=is_logged_in())
    return render_template(
        'category_item.html',
        category_id=category_id,
        item=item,
        logged_in=is_logged_in())


@app.route(
    '/categories/<int:category_id>/items/create/', methods=['GET', 'POST'])
@login_required
def create_category_item(category_id):
    category = get_category(category_id)
    if request.method == 'POST':
        user_id = get_userid(login_session['email'])
        if request.form['item-name'] and request.form['item-description']:
            if 'item-image' in request.files:
                file = request.files['item-image']
                filename = file.filename
                f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(f)
            else:
                filename = DEFAULT_IMAGE

            new_item = Item(
                name=request.form['item-name'],
                description=request.form['item-description'],
                category_id=category_id,
                user_id=user_id,
                image=filename)
            session.add(new_item)
            session.commit()
            return redirect(url_for('show_main', category_id=category_id))
    else:
        return render_template(
            'create_category_item.html', category=category, logged_in=True)


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/edit/',
    methods=['GET', 'POST'])
@login_required
def edit_category_item(category_id, item_id):
    item = get_item(item_id)
    categories = get_all_categories()
    if request.method == 'POST':
        if request.form['item-name']:
            item.name = request.form['item-name']
        if request.form['item-description']:
            item.description = request.form['item-description']
        if request.form['item-category']:
            item.category_id = request.form['item-category']

        if 'item-image' in request.files:
            file = request.files['item-image']
            item.image = file.filename
            f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(f)

        session.add(item)
        session.commit()
        return redirect(
            url_for(
                'show_category_item',
                category_id=item.category_id,
                item_id=item.id))
    else:
        return render_template(
            'edit_category_item.html',
            item=item,
            category_id=category_id,
            categories=categories,
            logged_in=True)


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/delete/',
    methods=['GET', 'POST'])
@login_required
def delete_category_item(category_id, item_id):
    item = get_item(item_id)
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('show_main', category_id=category_id))
    else:
        return render_template(
            'delete_category_item.html',
            category_id=category_id,
            item=item,
            logged_in=True)


# Functions for building JSON API
def build_category_JSON(category_id, item_id=None):
    category = get_category(category_id)

    if category is not None:
        category_json = defaultdict(list)
        if item_id is None:
            items = get_all_items(category_id)
        else:
            items = get_item(category_id, item_id)

        if items is None:
            category_json[category.name].append("Item not found.")
        elif len(items) == 0:
            category_json[category.name]
        else:
            for item in items:
                category_json[category.name].append(item.serialize)
    else:
        category_json = "Category not found"
    return category_json


def build_all_category_JSON(frame):
    all_categories = {}
    all_categories['Categories'] = frame.to_dict('records')
    for category in all_categories['Categories']:
        item_count = len(category['items'])
        first_item = category['items'][0]
        if item_count == 1 and first_item['id'] == None:
            del category['items']

    return all_categories


# Functions for logging in using Google OAuth2


def is_connected(gplus_id):
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_access_token:
        return True
    return False


def is_logged_in():
    user = login_session.get("username", "")
    if user:
        return True
    return False


def populate_login_session(access_token, gplus_id):
    print("3")
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id
    user_details = get_google_user_details(access_token)

    login_session['username'] = user_details['name']
    login_session['image'] = user_details['picture']
    login_session['email'] = user_details['email']
    login_session['user_id'] = get_or_create_user(login_session)


def get_google_user_details(access_token):
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    result = requests.get(userinfo_url, params=params)
    return result.json()


def get_or_create_user(login_session):
    user_id = get_userid(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    return user_id


def clear_login_session():
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['image']
    del login_session['user_id']


def validate_access_token(credentials):
    response = None
    print("2")
    # Check that the access token is valid
    token_url = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
    params = {'access_token': credentials.access_token}
    content = requests.get(token_url, params=params)
    result = content.json()
    if result.get('error'):
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for the intended user
    if result['user_id'] != credentials.id_token['sub']:
        response = make_response(
            json.dumps("Token's user ID doesn't match giver user ID"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    return response


# Functions to validate authorization


def is_authorized_to_modify_category(category_id):
    category = get_category(category_id)
    logged_in_user_id = get_userid(login_session.get('email'))
    return category.user_id == logged_in_user_id


def is_authorized_to_modify_item(item_id):
    item = get_item(item_id)
    logged_in_user_id = get_userid(login_session.get('email'))
    return item.user_id == logged_in_user_id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.config['JSON_SORT_KEYS'] = False
    app.run(host='0.0.0.0', port=5000)
