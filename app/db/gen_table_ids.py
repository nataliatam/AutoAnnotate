#-----------------------------------------------------------------------
# gen_table_ids.py
# Creates a new id for tables
#-----------------------------------------------------------------------

import os
import sys
import sqlalchemy as sqla
import sqlalchemy.orm
import dotenv
from sqlalchemy import text

# if running runserver.py from the app folder, need relative imports
try: 
    import database as db
except:
    import db.database as db

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')

#-----------------------------------------------------------------------
# Creates a new ID based on fields already in the table
# inputs are a table object's id (ie. db.Image.image_id)
# returns a int 
def gen_new_id(table_id):
    try:
        print("generating new id")
        engine = sqla.create_engine(_DATABASE_URL)
        with sqlalchemy.orm.Session(engine) as session:
            with session.begin(): 
                # session.execute(text("LOCK TABLE images IN ACCESS EXCLUSIVE MODE"))
                max_id = session.query(sqla.func.max(table_id)).scalar() # .with_for_update() does not work with aggregate function sqla.func.max()
                ## generates a new id based on max id in the table
                if max_id == None: 
                    new_id = 0
                else: new_id = max_id + 1
        
    except Exception as ex:
        print(f"error generating id: {ex}", file=sys.stderr)
        sys.exit(1)
    finally:
        engine.dispose()
    return new_id

#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)
    ## local testing 
    print("Newest id's for:")
    print("User table ",gen_new_id(db.User.user_id))
    print("Dataset table ",gen_new_id(db.Dataset.dataset_id))
    print("Image table ",gen_new_id(db.Image.image_id))
    print("Annotation table ",gen_new_id(db.Annotation.annotation_id))
    print("Category table ",gen_new_id(db.Category.category_id))

#-----------------------------------------------------------------------
if __name__ == '__main__':
    main()
    