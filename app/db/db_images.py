#-----------------------------------------------------------------------
# db_images.py
# Accesses the database based on events reagrding images
#-----------------------------------------------------------------------

import os
import sys
import sqlalchemy as sqla
from sqlalchemy import text
import sqlalchemy.orm
import dotenv
import cloudinary_util
try: 
    import database as db
except:
    import db.database as db
try:
    import table_objects.image as img_mod
except:
    import db.table_objects.image as img_mod
try: 
    import gen_table_ids as gen_id
except:
    import db.gen_table_ids as gen_id

try:
    import db_annotations as db_anns
except:
    import db.db_annotations as db_anns

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqla.create_engine(_DATABASE_URL)

#-----------------------------------------------------------------------
# Save image given basic image then stores it given the prev. made id
def save_new_img(image_data, new_dataset_id,
                  new_img_filename, new_annotated):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # saving
            new_img = db.Image(
                dataset_id = new_dataset_id,
                image_path = None,
                image_filename = new_img_filename,
                annotated=new_annotated)
            session.add(new_img)
            session.commit()
            cloudinary_url = cloudinary_util.upload_image_to_cloudinary(image_data, new_img.image_id)
            if cloudinary_url:
                update_img_meta(new_img.image_id, new_image_path=cloudinary_url)
                engine.dispose()
                return [0, new_img.image_id]
            else: # fail to save to cloudinary 
                delete_img(new_img.image_id)
                engine.dispose()
                return [1, "Failed to save image to database. Please contact system adminstrator"]
    
    except Exception as ex:
        print(f"Error: {ex}", file=sys.stderr)
        return [1, "Image upload fail: Please contact system adminstrator."]

# Updates the image path and/or whether it was annotated 
def update_img_meta(image_id, new_image_path=None,new_annotated=None):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            ## finds the image that was previously saved
            saved_image = session.query(db.Image).filter(
                db.Image.image_id == image_id).first()
            # update the fields of the image in the db
            if saved_image:
                if new_image_path:
                    saved_image.image_path = new_image_path
                if new_annotated:
                    saved_image.annotated = new_annotated
                session.commit()
            else: 
                raise Exception('Failed updating image data')
        engine.dispose()
        return True
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False

## Exporting all images with error messages based on the user
def get_all_images_with_error(dataset_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the images
            fetched_images = session.query(
                db.Image).filter(db.Image.dataset_id == dataset_id).all()
            images = []
            for row in fetched_images:
                if row:
                    image = img_mod.Image(row.image_id, 
                            row.dataset_id, row.image_path,
                            row.image_filename, row.annotated)
                    images.append(image)
                else:
                    print("images not found in the database.") 
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        return 1, ex
    return 0,images # exit_status, output

## deletes image from postgres database given the id and its annotations
def delete_img(image_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch image
            fetch_img = session.query(db.Image).filter(
                db.Image.image_id == image_id).first()
            if fetch_img:
                # want to delete that image in Postgres db
                session.delete(fetch_img)
                # want to delete the annotations relating to that image 
                ann_delete_status = db_anns.delete_img_annotations(image_id)
                if ann_delete_status: 
                    print("Annotations deleted")
                else: 
                    print("Deleted no annotations")
                    # raise Exception(f"Deleted no annotations for image {image_id}, \
                    #                 if this is a mistake, please contact system admin.")
                # Commit the session to apply the deletion
                session.commit()
                print("Image with id " + str(image_id)
                        +" deleted successfully.")
            else:
                print("Image with id " + str(image_id)
                        +" not found.")
                raise Exception("Image with id " + str(image_id)
                        +" not found.")
        engine.dispose()
        success_msg = "Image with id " + str(image_id)+" deleted successfully."
        return True, success_msg
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, ex

# escape wildcard characters
def check_special_chars(str_input):
    '''Checks for special characters and puts '\' before them'''

    i = 0
    while i < len(str_input):
        if str_input[i] == '_' or str_input[i] =='%':
            str_input = str_input[:i] + '\\' + str_input[i:]
            i += 1 # skip the added character
        i += 1
    return str_input

# want to filter given properties of the table
def filter_imgs(filename, dataset_id, img_id = None):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the images
            fetched_images = session.query(
                db.Image).filter(db.Image.dataset_id == dataset_id)
            
            if img_id is not None: 
                fetched_images = \
                    fetched_images.filter(db.Image.image_id == img_id)
                
            if filename:
                fetched_images = \
                    fetched_images.filter(
                        db.Image.image_filename.ilike(
                            '%' + check_special_chars(filename) + '%'))
                
            filtered_imgs = fetched_images.all()
            images = []
            for row in filtered_imgs:
                if row:
                    image = img_mod.Image(row.image_id, 
                            row.dataset_id, row.image_path,
                            row.image_filename, row.annotated)
                    images.append(image)
        engine.dispose()
    except Exception as ex:
        return[1, [ex, ("A server error occurred. " +
                        "Please contact the system administrator.")]]
    return [0,images] # exit_status, output

#-----------------------------------------------------------------------
# Helper functions for local testing  
## Exporting all images, just in case 
def get_all_images():
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the images
            fetched_images = session.query(
                db.Image).all()
            test_images = []
            for row in fetched_images:
                if row:
                    image = img_mod.Image(row.image_id, 
                            row.dataset_id, row.image_path,
                            row.image_filename, row.annotated)
                    test_images.append(image)
                else:
                    print("images not found in the database.")  
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)
    return test_images

# checking if images were saved by getting all images in the table 
def see_test_img():
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch all of the images
            fetched_images = session.query(
                db.Image).filter(db.Image.dataset_id == -1).all()
            test_images = []
            for row in fetched_images:
                if row:
                    image = img_mod.Image(row.image_id, 
                            row.dataset_id, row.image_path,
                            row.image_filename, row.annotated)
                    test_images.append(image)
                else:
                    print("images not found in the database.")  
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

    return test_images

def test_delete(test_images):
    for img in test_images:
        delete_img(img._image_id)

def print_tests(test_images):
    print(test_images)
    for img in test_images:
        print('Image found!')
        print('Image ID: ', img._image_id)
        print('Dataset ID: ', img._dataset_id)
        print('Image Path: ', img._image_path)
        print('Imgae Filename: ',img._image_filename)
        print('Annotated: ',img._annotated)
        print('\n')
#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)

    print('Images in table: ')
    all_imgs = get_all_images()
    print_tests(all_imgs)
    print('----------------------')
    print('Test images saved:')
    ## creates images to test in the database
    test_ids = []
    test_ids.append(save_new_img(image_data = 'images',new_dataset_id = 0,
                 new_img_filename ='test 1', new_annotated = True))
    
    test_ids.append(save_new_img(image_data = 'images',new_dataset_id = 2,
                 new_img_filename ='an image test', new_annotated = False))
    
    test_ids.append(save_new_img(image_data = 'images',new_dataset_id = 3, 
                 new_img_filename ='an image test test', new_annotated = False))
    
    test_ids.append(save_new_img(image_data = 'images',new_dataset_id = 2, 
                 new_img_filename ='this is an image', new_annotated = False))

    test_images = see_test_img()
    print_tests(test_images)
    print('----------------------')
    print('Filtering by: ')
    filename = 'test'
    print('filter: ',filename)
    filtered = filter_imgs(filename, dataset_id=0)[1]
    print_tests(filtered)

    filename = ' image'
    print('filter: ',filename)
    filtered = filter_imgs(filename, dataset_id=2)[1]
    print_tests(filtered)

    filename = ''
    img_id = test_ids[0]
    print('filter: ',filename, img_id)
    filtered = filter_imgs(filename, 0,img_id)[1]
    print_tests(filtered)

    filename = ''
    img_id = test_ids[1]
    print('filter: ',filename, img_id)
    filtered = filter_imgs(filename, 2,img_id)[1]
    print_tests(filtered)

    filename = ''
    img_id =test_ids[2]
    print('filter: ',filename, img_id)
    filtered = filter_imgs(filename, 3,img_id)[1]
    print_tests(filtered)

    filename = 'image'
    img_id = test_ids[2]
    print('filter: ',filename, img_id)
    filtered = filter_imgs(filename, 3,img_id)[1]
    print_tests(filtered)

    filename = 'image'
    img_id = test_ids[0]
    print('filter: ',filename, img_id)
    filtered = filter_imgs(filename, 0,img_id)[1]
    print_tests(filtered)

    print('----------------------')
    test_delete(test_images)
    print('----------------------')
    ## double checking everything is deleted
    all_imgs = get_all_images()
    print('Images in the database after deleting:')
    print_tests(all_imgs)
    ## TODO: create a delete function to delete these test images 
    
#-----------------------------------------------------------------------
if __name__ == '__main__':
    main()
    