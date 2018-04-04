#!usr/bin/env python3

# Imports for Client-Server functionality
from flask import Flask, render_template, request, redirect, jsonify, url_for

# Imports for CRUD functionality
from sqlalchemy import create_engine, asc, func, literal_column, select, MetaData
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# Imports for OAuth2 functionality
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import make_response, session as log_session
import requests

# Imports to implement nested JSON
import pandas
import functools
import json

app = Flask(__name__)

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
    frame = get_all_categories()
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


# Show all categories
@app.route('/')
@app.route('/categories')
@app.route('/categories/')
def show_categories():
    categories = get_all_categories()
    return render_template('categories.html', categories=categories)


# Create a new category
@app.route('/categories/create/', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        new_category = Category(name=request.form['category-name'], user_id=1)
        session.add(new_category)
        session.commit()
        return redirect(url_for('show_categories'))
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
            return redirect(url_for('show_categories'))
    else:
        return render_template('edit_category.html', category=category_to_edit)


# Delete a category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    category_to_delete = get_category(category_id)
    if request.method == 'POST':
        session.delete(category_to_delete)
        session.commit()
        return redirect(url_for('show_categories'))
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


# Helper functions to fetch data from the database
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

    # TODO - implement JSON API using session.query
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

    category_items = (select([
        item_table.c.category_id,
        json_agg(item_table).label('items')
    ]).select_from(item_table).group_by(
        item_table.c.category_id)).cte('category_items')
    query = (select([category_table.c.name, category_items]).select_from(
        category_table.join(category_items)))
    return read(query)


def json_agg(table):
    return func.json_agg(literal_column('"' + table.name + '"'))


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
