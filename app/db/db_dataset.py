#-----------------------------------------------------------------------
# db_dataset.py
# Accesses the database based on events reagrding datasets
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
    import table_objects.dataset as set_mod
except:
    import db.table_objects.dataset as set_mod
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
## save a user's dataset
def save_dataset(dataset_name, user_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            new_set = db.Dataset(dataset_names = dataset_name,
                                  user_id = user_id)
            session.add(new_set)
            session.commit()
        engine.dispose()
        return True
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False

def get_dataset_id(user_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            query = session.query(db.Dataset).filter(
                db.Dataset.user_id == user_id)
            user = query.first()
            dataset_id = user.dataset_id
        engine.dispose()
        return dataset_id
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False

#-----------------------------------------------------------------------
# Helper functions for local testing  

# for checking the databse 
def get_all_sets():
    all = {}
    try:
        with sqlalchemy.orm.Session(engine) as session:
            fetch = session.query(db.Dataset)
            all_users = fetch.all()
            for row in all_users:
                ann = set_mod.Dataset(row.dataset_id,
                             row.dataset_names, row.user_id)
                all[row.dataset_id] = ann.to_tuple()
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)
    
    return all
# checking if categories were saved by getting all categories in the table 
def see_test_set():
    sets = {}
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the datasets
            fetched = session.query(db.Dataset).all()
            for row in fetched:
                if row:
                    set = set_mod.Dataset(row.dataset_id, 
                            row.dataset_names, row.user_id)
                    sets[row.dataset_id] = set.to_tuple()
                else:
                    print("datasets not found in the database.")  
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

    return sets

def test_delete(test_sets):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the categories
            for id in test_sets:
                fetched = session.query(db.Dataset).filter(
                    db.Dataset.dataset_id == id).one_or_none()
                if fetched:
                    session.delete(fetched)
                    # Commit the session to apply the deletion
                    session.commit()
                    print("Dataset with id " + str(id)
                            +" deleted successfully.")
                else:
                    print("Dataset with id " + str(id)
                            +" not found.")
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

def print_tests(tests):
    print(tests)
    for row in tests:
        print('Dataset found!')
        print('Dataset ID: ', tests[row][0])
        print('Dataset Name: ', tests[row][1])
        print('User ID: ', tests[row][2])
        print('\n')
#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)

    print('Datasets in table: ')
    all = get_all_sets()
    print_tests(all)
    print('#----------------------------------------------------------')
    print('Test datasets saved:')
    ## creates categories to test in the database
    test_cat_ids = []
    test_cat_ids.append(save_dataset(dataset_name = 'user 1 email', user_id = 1))
    test_cat_ids.append(save_dataset(dataset_name = 'user 0 email', user_id = 0))
    test_cat_ids.append(save_dataset(dataset_name = 'user 2 email', user_id = 2))

    test_cats = see_test_set()
    print_tests(test_cats)
    print('#----------------------------------------------------------')
    print("getting dataset id")
    user_ids = [1,0,2]
    for id in user_ids: 
        print(f"set id with  user id {id} : ",get_dataset_id(id))
    print('#----------------------------------------------------------')
    test_delete(test_cats)
    print('#----------------------------------------------------------')
    ## double checking everything is deleted
    print('Datasets in table after deleting: ')
    all = get_all_sets()
    print_tests(all)
    
#-----------------------------------------------------------------------
if __name__ == '__main__':
    main()
    