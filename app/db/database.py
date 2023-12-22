#-----------------------------------------------------------------------
# database.py
# Sets in the database schema into SQLAlchemy
#-----------------------------------------------------------------------
import os
import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy import Column

Base = sqlalchemy.orm.declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(sqla.Integer, primary_key=True)
    username = Column(sqla.String) 
    ## TODO will we need to store gmail info?  

class Dataset(Base):
    __tablename__ = 'datasets'
    dataset_id = Column(sqla.Integer, primary_key=True)
    dataset_names = Column(sqla.String)
    user_id = Column(sqla.Integer)

class Image (Base):
    __tablename__ = 'images'
    image_id = Column(sqla.Integer, primary_key=True)
    dataset_id = Column(sqla.Integer)
    image_path = Column(sqla.String)
    image_filename = Column(sqla.String)
    annotated = Column(sqla.Boolean, default=False)

# has fields: 
class Annotation(Base):
    __tablename__ = 'annotations'
    annotation_id = Column(sqla.Integer, primary_key=True)
    image_id = Column(sqla.Integer)
    category_id = Column(sqla.Integer)
    segmentation_coordinates = Column(sqla.PickleType)
    bounding_box_coordinates = Column(sqla.PickleType)
    area = Column(sqla.Float, nullable=True)
    iscrowd = Column(sqla.Boolean, default=False)
    isbbox = Column(sqla.Boolean, default=False)
    color = Column(sqla.String)

class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(sqla.Integer, primary_key=True)
    category_name = Column(sqla.String)

