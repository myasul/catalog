#!usr/bin/env python3

# Imports for Client-Server functionality
from flask import Flask, render_template, request, redirect, jsonify, url_for

# Imports for CRUD functionality
from sqlalchemy import create_engine, asc, func, select, MetaData, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# Imports for OAuth2 functionality
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import make_response, session as login_session
import random
import string
import requests

# Imports to implement nested JSON
import pandas
import functools
import json

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secret_google.json',
                            'r').read())['web']['client_id']

# Connect to the database and create a database session
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine
metadata = MetaData(bind=engine)
metadata.reflect()
tables = metadata.tables
category_table = tables['categories']
item_table = tables['items']
read = functools.partial(pandas.read_sql, con=engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON APIs to view Category information
# TODO
@app.route('/api/categories/')
def show_all_categories_JSON():
    all_categories = {}
    frame = get_all_categories_JSON()
    all_categories['Categories'] = frame.to_dict('records')
    return jsonify(all_categories)


@app.route('/api/categories/<int:category_id>/')
def show_category_items_JSON(category_id):
    items = get_all_items(category_id)
    return jsonify(Category_Items=[item.serialize for item in items])


@app.route('/api/categories/<int:category_id>/<int:item_id>')
def show_category_item_JSON():
    item = get_item(category_id, item_id)
    return jsonify(Category_Item[item.serialize])


# Create anti-forgery token
@app.route("/login")
def generate_token():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return login_session['state']


# TODO - REFACTOR!
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
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

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
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_access_token:
        response = make_response(json.dumps("User is already connected."), 200)
        response.headers['Content-type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    result = requests.get(userinfo_url, params=params)
    data = result.json()

    login_session['username'] = data['name']
    login_session['image'] = data['picture']
    login_session['email'] = data['email']

    # Check if user already exists. If not, add it in the database
    user_id = get_userid(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

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
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['image']
        del login_session['user_id']
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Show all categories
@app.route('/')
@app.route('/categories')
@app.route('/categories/')
@app.route('/categories/<int:category_id>')
def show_main(category_id=0):
    categories = get_all_categories()
    category = None
    items = None
    category_name = "dummy name"

    if category_id == 0:
        items = get_latest_items()
    else:
        category = get_category(category_id)
        category_name = category.name
    return render_template(
        'categories.html',
        categories=categories,
        items=items,
        category_id=category_id,
        category_name=category_name,
        logged_in=is_logged_in())


# Create a new category
@app.route('/categories/create/', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        new_category = Category(name=request.form['category-name'], user_id=1)
        session.add(new_category)
        session.commit()
        return redirect(url_for('show_main'))
    else:
        return render_template('create_category.html')


# Edit a category
@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    category_to_edit = get_category(category_id)
    if request.method == 'POST':
        if request.form['category-name']:
            category_to_edit.name = request.form['category-name']
            session.add(category_to_edit)
            session.commit()
            return redirect(url_for('show_main'))
    else:
        return render_template('edit_category.html', category=category_to_edit)


# Delete a category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    category_to_delete = get_category(category_id)
    if request.method == 'POST':
        session.delete(category_to_delete)
        session.commit()
        return redirect(url_for('show_main'))
    else:
        return render_template(
            'delete_category.html', category=category_to_delete)


# Show category items
@app.route('/categories/<int:category_id>/items/')
def show_category_item_list(category_id):
    all_items = get_all_items(category_id)
    return render_template(
        'category_item_list.html',
        category_items=all_items,
        category_id=category_id)


# Show a specific item
@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/',
    methods=['GET', 'POST'])
def show_category_item(category_id, item_id):
    item = get_item(category_id, item_id)
    return render_template(
        'category_item.html', category_id=category_id, item=item)


# Create a specific item
@app.route(
    '/categories/<int:category_id>/items/create/', methods=['GET', 'POST'])
def create_category_item(category_id):
    if request.method == 'POST':
        if request.form['item-name'] and request.form['item-description']:
            new_item = Item(
                name=request.form['item-name'],
                description=request.form['item-description'],
                category_id=category_id,
                user_id=1)
            session.add(new_item)
            session.commit()
            return redirect(
                url_for('show_category_item_list', category_id=category_id))
    else:
        return render_template(
            'create_category_item.html', category_id=category_id)


# Edit category item
@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/edit/',
    methods=['GET', 'POST'])
def edit_category_item(category_id, item_id):
    item = get_item(category_id, item_id)
    if request.method == 'POST':
        if request.form['item-name']:
            item.name = request.form['item-name']
        if request.form['item-description']:
            item.description = request.form['item-description']
        session.add(item)
        session.commit()
        return redirect(
            url_for(
                'show_category_item', category_id=category_id,
                item_id=item.id))
    else:
        return render_template(
            'edit_category_item.html', item=item, category_id=category_id)


# Delete category item
@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/delete/',
    methods=['GET', 'POST'])
def delete_category_item(category_id, item_id):
    item = get_item(category_id, item_id)
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(
            url_for('show_category_item_list', category_id=category_id))
    else:
        return render_template(
            'delete_category_item.html', category_id=category_id, item=item)


def is_logged_in():
    user = login_session.get("username", "")
    if user:
        return True
    return False


# TODO - Check if you can make a separate file for the helper functions
# Helper functions to fetch data from the database
def get_latest_items(limit=10):
    return session.query(Item).order_by(Item.date_created.desc()).limit(limit)


def get_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return session.query(Item).filter_by(
        id=item_id, category_id=category_id, user_id=1).one()


def get_category(category_id):
    return session.query(Category).filter_by(id=category_id).one()


def get_all_items(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return session.query(Item).filter_by(
        category_id=category.id, user_id=1).all()


def get_all_categories():
    return session.query(Category).order_by(asc(Category.name))


def get_all_categories_JSON():

    # TODO
    # - implement JSON API using session.query
    # - make sure that only selected columns are displayed
    #all_items = session.query(Item.category_id,
    #                          json_agg(Item).label('items')).group_by(
    #                              Item.category_id).cte(name="all_items")
    #
    #all_categories = session.query(Category, all_items).filter(
    #    Category.id == all_items.c.category_id).cte(name="all_categories")
    #
    #all_categories_2 = session.query(all_categories).options(
    #    Load(all_categories).load_only("id", "name"),
    #    Load(all_items).defer("category_id"))

    query = (select([
        category_table.c.id, category_table.c.name,
        func.json_agg(
            func.json_build_object('id', item_table.c.id, 'name',
                                   item_table.c.name, 'description',
                                   item_table.c.description, 'image',
                                   item_table.c.image)).label('items')
    ]).select_from(category_table.outerjoin(item_table)).group_by(
        category_table.c.id))

    return read(query)


def create_user(login_session):
    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        image=login_session['image'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_userid(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except exc.SQLAlchemyError:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.config['JSON_SORT_KEYS'] = False
    app.run(host='0.0.0.0', port=5000)
