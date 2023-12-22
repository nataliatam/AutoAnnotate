#-----------------------------------------------------------------------
# db_user.py
# Accesses the database based on events reagrding users
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
    import table_objects.user as user_mod
except:
    import db.table_objects.user as user_mod
try: 
    import gen_table_ids as gen_id
except:
    import db.gen_table_ids as gen_id
try: 
    import db_dataset as db_set
except:
    import db.db_dataset as db_set

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqla.create_engine(_DATABASE_URL)

#-----------------------------------------------------------------------
# takes in the users email, and checks if it already exists in the 
# user database. If it does then return that existing id. If not, 
# then generate the new id, save the user, and then return the new id.
def save_user(email):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            user = session.query(db.User).filter(
                db.User.username == email).one_or_none()
            # if empty, then the category does not exists, 
            # and we would want to save it 
            if user is None: 
                ## if properly able to save the dataset id, save the user
                new_user = db.User(username = email)
                session.add(new_user)
                session.commit()
                user_id = new_user.user_id
                # we would also want to save the user's dataset
                saved_set = db_set.save_dataset(dataset_name = email, user_id= user_id)
                if not saved_set:
                    return False, "Failed to save user's dataset properly "
                return True, user_id
            if user is not None:
                user_id = user.user_id
                has_dataset_id = db_set.get_dataset_id(user_id)
                if isinstance(has_dataset_id, bool):
                    return False, "Failed to save user's dataset properly "
                return True, user_id
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, "Failed to save user, your work will not be saved "
#-----------------------------------------------------------------------
# Helper functions for local testing  
## get all users that have logged in for viewing purposes
def get_all_users():
    all = {}
    try:
        with sqlalchemy.orm.Session(engine) as session:
            fetch = session.query(db.User)
            all_users = fetch.all()
            for row in all_users:
                ann = user_mod.User(row.user_id,
                             row.username)
                all[row.user_id] = ann.to_tuple()
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)
    
    return all

## get the username of a user
def get_username(user_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            query = session.query(db.User).filter(
                db.User.user_id == user_id)
            user = query.one_or_none()
            username = user.username
        engine.dispose()
        return username
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

# checking if categories were saved by getting all categories in the table 
def see_test_set():
    sets = {}
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the datasets
            fetched = session.query(db.User).all()
            for row in fetched:
                if row:
                    set = user_mod.User(row.user_id, 
                            row.username)
                    sets[row.user_id] = set.to_tuple()
                else:
                    print("users not found in the database.")  
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
                fetched = session.query(db.User).filter(
                    db.User.user_id == id).one_or_none()
                if fetched:
                    session.delete(fetched)
                    # Commit the session to apply the deletion
                    session.commit()
                    print("User with id " + str(id)
                            +" User successfully.")
                else:
                    print("User with id " + str(id)
                            +" not found.")
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

def print_tests(tests):
    print(tests)
    for row in tests:
        print('User found!')
        print('User ID: ', tests[row][0])
        print('User Name: ', tests[row][1])
        print('\n')
#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)

    print('Users in table: ')
    all = get_all_users()
    print_tests(all)
    print('#----------------------------------------------------------')
    print('Test datasets saved:')
    ## creates categories to test in the database
    test_cat_ids = []
    test_cat_ids.append(save_user(email = 'user 1 email'))
    test_cat_ids.append(save_user(email = 'user 0 email'))
    test_cat_ids.append(save_user(email = 'user 2 email'))
    test_cat_ids.append(save_user(email = 'user 2 email'))

    test_cats = see_test_set()
    print_tests(test_cats)
    print('#----------------------------------------------------------')
    print("getting username")
    for id in test_cat_ids: 
        print(f"set id with  user id {id} : ",get_username(id))
    print('#----------------------------------------------------------')
    test_delete(test_cats)
    print('#----------------------------------------------------------')
    ## double checking everything is deleted
    print('Categories in the database after deleting:')
    all = get_all_users()
    print_tests(all)
    
#-----------------------------------------------------------------------
if __name__ == '__main__':
    main()
    