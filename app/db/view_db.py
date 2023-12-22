#-----------------------------------------------------------------------
# view_db.py
# For testing purposes - returns all content in the database 
#-----------------------------------------------------------------------
import sys
# if running runserver.py from the app folder, need relative imports
try:
    import db_annotations as db_ann
except:
    import db.db_annotations as db_ann

try:
    import db_images as db_img
except:
    import db.db_images as db_img

try:
    import db_categories as db_cat
except:
    import db.db_categories as db_cat

try:
    import db_user as db_user
except:
    import db.db_user as db_user

try:
    import db_dataset as db_set
except:
    import db.db_dataset as db_set

#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)
    
    print("Users")
    users = db_user.get_all_users()
    for user in users:
        print(str("id "+str(user)) 
              +" : "+ str(users[user]))
    print('#----------------------------------------------------------')

    print("Datasets")
    sets = db_set.get_all_sets()
    for set in sets:
        print(str("id "+str(set)) 
              +" : "+ str(sets[set]))
    print('#----------------------------------------------------------')

    print("Images")
    images = db_img.get_all_images()
    for img in images:
        print(str("id "+str(img.get_image_id())) 
              +" : "+ str(img.to_tuple()))
    print('#----------------------------------------------------------')

    print("Categories")
    categories = db_cat.get_all_categories()
    for cat in categories:
        print(str(cat) +" : "+ str(categories[cat]))
    print('#----------------------------------------------------------')
    
    print("Annotations")
    annotations, _ = db_ann.get_all_annotations()
    for ann in annotations:
        print(str(ann) +" : "+ str(annotations[ann]))
#-----------------------------------------------------------------------
if __name__ == '__main__':
    main()
    