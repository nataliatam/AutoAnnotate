#-----------------------------------------------------------------------
# create.py
# creates the database 
# CAUTION: this will delete the current database to create a new one 
# maybe unneccesary 
#-----------------------------------------------------------------------
import os
import sys
import sqlalchemy
import sqlalchemy.orm
import dotenv
import database as db

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')

#-----------------------------------------------------------------------

def main():

    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)

    try:
        # setting echo = True helps with debugging
        engine = sqlalchemy.create_engine(_DATABASE_URL, echo=True)
        ## deletes prev database and creates a new one with set up
        db.Base.metadata.drop_all(engine)
        db.Base.metadata.create_all(engine)

        ## maybe TODO - confirm if we need to populate any data upon
        ##              creation of the database
        
        engine.dispose()

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

#-----------------------------------------------------------------------

if __name__ == '__main__':
    main()
