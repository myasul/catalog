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


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
