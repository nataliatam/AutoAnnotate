#-----------------------------------------------------------------------
# db_category.py
# Accesses the database based on events reagrding categories
#-----------------------------------------------------------------------

import os
import sys
import sqlalchemy as sqla
import sqlalchemy.orm
import dotenv

try: 
    import database as db
except:
    import db.database as db
try:
    import table_objects.category as cat_mod
except:
    import db.table_objects.category as cat_mod
try: 
    import gen_table_ids as gen_id
except:
    import db.gen_table_ids as gen_id

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqla.create_engine(_DATABASE_URL)

#-----------------------------------------------------------------------
# takes in the category name, and checks if it already exists in the 
# category database. If it does then return that existing id. If not, 
# then generate the new id, save the category, and then return the new id.
def save_cat(new_category_name):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            cat = session.query(db.Category).filter(
                db.Category.category_name == new_category_name).one_or_none()
            # if empty, then the category does not exists, 
            # and we would want to save it 
            if cat is None: 
                # new_cat_id = gen_cat_id()
                new_cat = db.Category(
                    category_name = new_category_name)
                session.add(new_cat)
                #print(new_cat.image_id)
                session.commit()
                return True, new_cat.category_id
            if cat is not None:
                return True, cat.category_id
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, ex

def get_cat_name(cat_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            query = session.query(db.Category).filter(
                db.Category.category_id == cat_id)
            cat = query.one_or_none()
        engine.dispose()
        return True,cat.category_name
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, ex

#-----------------------------------------------------------------------
# Helper functions for local testing  

# obtains all the categories currently in the db
def get_all_categories():
    categories = {}
    # fetches all categories in the database
    try:
        with sqlalchemy.orm.Session(engine) as session:
            query = session.query(db.Category)
            all = query.all()
            for row in all:
                cat = cat_mod.Category(row.category_id,
                             row.category_name)
                categories[row.category_id] = cat.to_tuple()
        engine.dispose()

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)
    
    return categories

# checking if categories were saved by getting all categories in the table 
def see_test_cats():
    categories = {}
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the categories
            fetched_cats = session.query(db.Category).all()
            for row in fetched_cats:
                if row:
                    cat = cat_mod.Category(row.category_id, 
                            row.category_name)
                    categories[row.category_id] = cat.to_tuple()
                else:
                    print("categories not found in the database.")  
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

    return categories

def test_delete(test_cats):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the categories
            for cat_id in test_cats:
                fetch_cat = session.query(db.Category).filter(
                    db.Category.category_id == cat_id).first()
                if fetch_cat:
                    session.delete(fetch_cat)
                    # Commit the session to apply the deletion
                    session.commit()
                    print("Category with id " + str(cat_id)
                            +" deleted successfully.")
                else:
                    print("Category with id " + str(cat_id)
                            +" not found.")
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

def print_tests(test_cats):
    print(test_cats)
    for cat in test_cats:
        print('Category found!')
        print('Category ID: ', test_cats[cat][0])
        print('Category Name: ', test_cats[cat][1])
        print('\n')
#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)

    print('Categories in table: ')
    all_cats = get_all_categories()
    print_tests(all_cats)
    print('#----------------------------------------------------------')
    print('Test categories saved:')
    ## creates categories to test in the database
    test_cat_ids = []
    test_cat_ids.append(save_cat(new_category_name='cat 1'))
    test_cat_ids.append(save_cat(new_category_name='cat 2'))
    test_cat_ids.append(save_cat(new_category_name='cat 2'))

    test_cats = see_test_cats()
    print_tests(test_cats)
    print('#----------------------------------------------------------')
    print("getting cat names")
    for id in test_cat_ids: 
        print(f"cat name with id {id} : ",get_cat_name(id))
    print('#----------------------------------------------------------')
    test_delete(test_cats)
    print('#----------------------------------------------------------')
    ## double checking everything is deleted
    all_cats_check = get_all_categories()
    print('Categories in the database after deleting:')
    print_tests(all_cats_check) 
    
#-----------------------------------------------------------------------
if __name__ == '__main__':
    main()
    