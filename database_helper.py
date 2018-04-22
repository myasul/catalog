# Imports for CRUD functionality
from sqlalchemy import create_engine, asc, func, select, MetaData, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# Imports to implement nested JSON
import pandas
from functools import partial, wraps
import json

# Connect to the database and create a database session
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine
metadata = MetaData(bind=engine)
metadata.reflect()
tables = metadata.tables
category_table = tables['categories']
item_table = tables['items']
read = partial(pandas.read_sql, con=engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Helper functions to fetch data from the catalog database
def get_latest_items(limit=10):
    try:
        return session.query(Item).order_by(
            Item.date_created.desc()).limit(limit)
    except exc.SQLAlchemyError:
        return None


def get_item(item_id, category_id=None):
    try:
        if category_id is None:
            return session.query(Item).filter_by(id=item_id, ).one()
        else:
            return session.query(Item).filter_by(
                id=item_id, category_id=category_id).one()
    except exc.SQLAlchemyError:
        return None


def get_category(category_id):
    try:
        return session.query(Category).filter_by(id=category_id).one()
    except exc.SQLAlchemyError:
        return None


def get_all_items(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        return session.query(Item).filter_by(category_id=category.id).all()
    except exc.SQLAlchemyError:
        return None


def get_item_count(category_id):
    try:
        count = session.query(func.count(
            Item.id).label('count')).filter_by(category_id=category_id).one()
        return count[0]
    except exc.SQLAlchemyError:
        return 0


def get_all_categories():
    return session.query(Category).order_by(asc(Category.name))


def get_all_categories_JSON():

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
    try:
        new_user = User(
            name=login_session['username'],
            email=login_session['email'],
            image=login_session['image'])
        session.add(new_user)
        session.commit()
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        return user.id
    except exc.SQLAlchemyError:
        return None


def get_userid(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except exc.SQLAlchemyError:
        return None