#!usr/bin/env python3

# Imports for Client-Server functionality
from flask import Flask, render_template, request, redirect, jsonify, url_for

# Imports for CRUD functionality
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# Imports for OAuth2 functionality
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import make_response, session as log_session
import requests

app = Flask(__name__)

# Connect to the database and create a database session
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Show all categories
@app.route('/')
@app.route('/categories')
@app.route('/categories/')
def show_categories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html', categories=categories)


# Create a new category
@app.route('/categories/create/', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        new_category = Category(name=request.form['name'], user_id=1)
        session.add(new_category)
        session.commit()
        return redirect(url_for('show_categories'))
    else:
        return render_template('create_category.html')


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    category_to_edit = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            category_to_edit.name = request.form['name']
            session.add(category_to_edit)
            session.commit()
            return redirect(url_for('show_categories'))
    else:
        return render_template('edit_category.html', category=category_to_edit)


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    category_to_delete = session.query(Category).filter_by(
        id=category_id).one()
    if request.method == 'POST':
        session.delete(category_to_delete)
        session.commit()
        return redirect(url_for('show_categories'))
    else:
        return render_template(
            'delete_category.html', category=category_to_delete)


# Show category items
@app.route('/category/<int:category_id>/items/')
def show_category_item_list(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    category_items = session.query(Item).filter_by(
        category_id=category.id, user_id=1).all()
    return render_template(
        'category_item_list.html',
        category_items=category_items,
        category_id=category_id)


# Show a specific item
@app.route(
    '/category/<int:category_id>/items/<int:item_id>/',
    methods=['GET', 'POST'])
def show_category_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(
        id=item_id, category_id=category_id, user_id=1).one()
    return render_template(
        'category_item.html', category_id=category_id, item=item)


# Edit category item
@app.route(
    '/category/<int:category_id>/items/<int:item_id>/edit/',
    methods=['GET', 'POST'])
def edit_category_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(
        id=item_id, category_id=category_id, user_id=1).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
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
    '/category/<int:category_id>/items/<int:item_id>/delete/',
    methods=['GET', 'POST'])
def delete_category_item(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(
        id=item_id, category_id=category_id, user_id=1).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(
            url_for('show_category_item_list', category_id=category_id))
    else:
        return render_template(
            'delete_category_item.html', category_id=category_id, item=item)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
