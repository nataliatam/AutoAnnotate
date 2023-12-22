#-----------------------------------------------------------------------
# db_annotations.py
# Accesses the database based on annotation events
#-----------------------------------------------------------------------
## Note for when in a sqlalchemy session, only if needed: 
    # the following lines will clear the info in all of the tables 
        # database.Base.metadata.drop_all(engine)
        # database.Base.metadata.create_all(engine)
#-----------------------------------------------------------------------

import os
import sys
import sqlalchemy
import sqlalchemy.orm
import dotenv
import distinctipy
import numpy as np
import json

# if running runserver.py from the app folder, need relative imports
try: 
    import database as db
except:
    import db.database as db
try:
    import table_objects.annotation as ann_mod
except:
    import db.table_objects.annotation as ann_mod
try:
    import db_categories as db_cat
except:
    import db.db_categories as db_cat

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')
engine = sqlalchemy.create_engine(_DATABASE_URL)
#-----------------------------------------------------------------------
def save_annotation(new_image_id, new_category_name, seg_coords,
                    bound_coords, new_area, new_iscrowd,
                    new_isbbox, new_color):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            session.begin()     # Start a transaction

            cat = session.query(db.Category).filter(
                db.Category.category_name == new_category_name).one_or_none()

            if cat is None:
                new_cat = db.Category(category_name=new_category_name)
                session.add(new_cat)
                session.flush()  # Flush to get the new category ID
                category_id = new_cat.category_id
            else:
                category_id = cat.category_id

            new_ann = db.Annotation(
                image_id=new_image_id,
                category_id=category_id,
                segmentation_coordinates=seg_coords,
                bounding_box_coordinates=bound_coords,
                area=new_area, iscrowd=new_iscrowd,
                isbbox=new_isbbox, color=new_color)

            session.add(new_ann)
            session.commit()  # Commit the transaction

            ann_id = new_ann.annotation_id
            return ann_id
    except Exception as ex:
        print(ex, file=sys.stderr)
        session.rollback()  # Rollback in case of error

def save_kmeans_annotation(new_image_id, new_category_id, seg_coords,
                    bound_coords, new_area, new_iscrowd,
                    new_isbbox, new_color):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            session.begin()
            new_ann = db.Annotation(
                image_id=new_image_id,
                category_id=new_category_id,
                segmentation_coordinates=seg_coords,
                bounding_box_coordinates=bound_coords,
                area=new_area, iscrowd=new_iscrowd,
                isbbox=new_isbbox, color=new_color)
            session.add(new_ann)
            session.commit()  # Commit the transaction

            ann_id = new_ann.annotation_id
            return ann_id
    except Exception as ex:
        print(ex, file=sys.stderr)
        session.rollback()  # Rollback in case of error


# Return annotations for image id, given image ID for user exporting
## in dictionary with format {annotation_id : annotation tuple}
def get_img_annotations(image_id):
    annotations = []
    # fetches based on mage id
    try:
        with sqlalchemy.orm.Session(engine) as session:
            fetch_all_img_ann = session.query(db.Annotation
                            ).filter(
                                db.Annotation.image_id == int(image_id))
            all_img_ann = fetch_all_img_ann.all()
            for row in all_img_ann:
                # row.segmentation_coordinates = {"x":...,"y":...}
                # convert to [x,y,x,y...] 
                formatted_coords = []
                for coord in row.segmentation_coordinates:
                    formatted_coords.append(coord["x"])
                    formatted_coords.append(coord["y"])

                annotation = dict()
                annotation["id"] = row.annotation_id
                annotation["image_id"] = row.image_id
                annotation["category_id"] = row.category_id
                annotation["segmentation"] = [formatted_coords]
                annotation["area"] = row.area
                annotation["bbox"] = row.bounding_box_coordinates
                annotation["iscrowd"] = row.iscrowd
                annotation["color"] = row.color
                annotations.append(annotation)
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, f"Failed to fetch image {image_id} annotations : {ex}"
    
    return True, annotations

## Returns all annotations for all images in the database
## Returns a dictionary with format {annotation_id : annotation tuple}
def get_all_annotations():
    all_annotations = {}
    # fetches all annotations in the database
    try:
        with sqlalchemy.orm.Session(engine) as session:
            fetch_all_img_ann = session.query(db.Annotation)
            all_img_ann = fetch_all_img_ann.all()
            num_images = len(all_img_ann)
            for row in all_img_ann:
                ann = ann_mod.Annotation(row.annotation_id,
                             row.image_id, row.category_id,
                             row.segmentation_coordinates, 
                             row.bounding_box_coordinates, row.area,
                             row.iscrowd, row.isbbox, row.color)
                
                # current seeg_coords format: [[{'x':...,'y':...},{'x':...,'y':...},...],[{'x':...,'y':...},{'x':...,'y':...},...],[...]]
                # make new seg_coords format: [x,y,x,y,...] 

                # polygons = row.segmentation_coordinates
                # ann = {'id':row.annotation_id,
                #        "image_id":row.image_id,
                #        "category_id":row.category_id,
                #        # "dataset_id":dataset_id, TODO: get dataset_id from image_id
                #        "segmentation":row.segmentation_coordinates,
                #        }
                all_annotations[row.annotation_id] = ann.to_tuple()
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, f"Please contact system admin. Failed to get all annotations: {ex}"
    
    return all_annotations, num_images

# return all annotations of the given image for drawing on canvas
def get_annotations(image_id):
    polygons, category_names, category_ids, ann_ids = [], [], [], []
    # fetches all annotations in the database
    try:
        with sqlalchemy.orm.Session(engine) as session:
            anns = session.query(db.Annotation).filter(db.Annotation.image_id == image_id).all()
            for ann in anns:
                polygons.append(ann.segmentation_coordinates)
                got_name, cat_name = db_cat.get_cat_name(ann.category_id)
                if got_name:
                    category_names.append(cat_name)
                else: raise Exception(f"failed to get category {ann.category_id} name")
                category_ids.append(ann.category_id)
                ann_ids.append(ann.annotation_id)
        engine.dispose()
        # A list of (r,g,b) colors that are visually distinct to each other 
        # (r,g,b) values are floats between 0 and 1.

            # A list of (r,g,b) colors that are visually distinct to each other 
        # (r,g,b) values are floats between 0 and 1.
        category_set = list(set(category_names))
        cat_colors = dict()
        color_set = np.array(distinctipy.get_colors(len(category_set))) * 255
        color_set = color_set.astype(int).tolist()
        for i in range(len(category_set)):
            cat_colors[category_set[i]] = color_set[i]
        colors = []
        for cat in category_names: 
            colors.append(cat_colors[cat])
        return True, [polygons, category_names, category_ids, cat_colors, colors, ann_ids]
    except Exception as ex:
        return False, f"Failed to get annotation and category data for image {image_id}: {ex}"

# Function to delete an annotation given its ID
def delete_annotation(annotation_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Fetch the annotation to be deleted
            annotation_to_delete = session.query(db.Annotation).filter(
                db.Annotation.annotation_id == annotation_id).one_or_none()

            if annotation_to_delete is not None:
                session.delete(annotation_to_delete)
                session.commit()
                return True, "success deleting annotation"
            else:
                raise Exception(f"failed to find annotation {annotation_id}")
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, ex

# deletes the annotations of a given image, using the iamge id
def delete_img_annotations(image_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Perform bulk deletion of annotations for the given image
            annotations_to_delete = session.query(db.Annotation).filter(
                db.Annotation.image_id == image_id)
            deleted_count = annotations_to_delete.delete(
                synchronize_session=False)
            session.commit()
            if deleted_count > 0:
                print(f"{deleted_count} annotations deleted for image ID {image_id}.")
                return True, "success"
            else:
                print(f"No annotations found for image ID {image_id}.")
                return True, "success"
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False, ex
    
def delete_anns_for_cat(img_id, cat_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            # Perform bulk deletion of annotations for the given category and image
            annotations_to_delete = session.query(db.Annotation).filter(
                db.Annotation.image_id == img_id,
                db.Annotation.category_id == cat_id)
            deleted_count = annotations_to_delete.delete(synchronize_session=False)
            # Commit the changes
            session.commit()

            if deleted_count > 0:
                print(f"{deleted_count} annotations deleted for image ID {img_id} and category ID {cat_id}.")
                return True
            else:
                print(f"No annotations found for image ID {img_id} and category ID {cat_id}.")
                raise Exception()
    except Exception as ex:
        print(f"An error occurred: {ex}")
        return False
#-----------------------------------------------------------------------
# Helper functions for local testing  
# Get the annotation made from tests out the database
def help_delete_img_anns(session, test_anns):
    for ann in test_anns:
        fetch_ann = session.query(db.Annotation).filter(
            db.Annotation.annotation_id == ann._annotation_id)
        test_annotation =  fetch_ann.first()
        if test_annotation:
            # Mark the annotation for deletion
            ann_id = ann._annotation_id
            session.delete(test_annotation)
            # Commit the session to apply the deletion
            session.commit()
            print("Annotation with id " + str(ann_id)
                    +" deleted successfully.")
        else:
            print("Annotation not found.")
def delete_test_ann(test_anns):
    # gets all annotations created from testing, then deletes them 
    try:
        with sqlalchemy.orm.Session(engine) as session:
            for id in test_anns:
                help_delete_img_anns(session, test_anns[id])
            session.execute(sqlalchemy.text("ALTER SEQUENCE " 
                    +"annotations_annotation_id_seq RESTART WITH 1;"))
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

# testing saving annotations into the database, returning a 
def test_save_ann(img_id):
    try:
        with sqlalchemy.orm.Session(engine) as session:
            all_anns = {}
            for id in img_id:
                # Fetch all of the annotations
                test_table = session.query(
                    db.Annotation).filter(
                    db.Annotation.image_id == id).all()
                test_annotations = []
                for row in test_table:
                    if row:
                        annotation = ann_mod.Annotation(
                                row.annotation_id,
                                row.image_id, row.category_id,
                                row.segmentation_coordinates, 
                                row.bounding_box_coordinates, row.area,
                                row.iscrowd, row.isbbox, row.color)
                        test_annotations.append(annotation)
                    else:
                        print("annotation not found in the database.")  
                all_anns[id] = test_annotations
        engine.dispose()
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

    return all_anns

# test exporting the annotations for a single image
def test_expt_img_ann(img_ids):
    for id in img_ids:
        print("image id: ", id)
        annotations = get_img_annotations(id)
        for ann in annotations:
            print(str(ann) +" : "+ str(annotations[ann]))

# test exporting all existing annotations 
def test_expt_all_ann():
    all_annotations,_ = get_all_annotations()
    for ann in all_annotations: 
        print(str(ann) +" : "+str(all_annotations[ann]))

#-----------------------------------------------------------------------
def main():
    if len(sys.argv) != 1:
        print('Usage: python ' + sys.argv[0], file=sys.stderr)
        sys.exit(1)
    # creates annotations to test in the database, printing it out
    # testing image ids are negative values
    save_annotation(new_image_id = -1, new_category_name= "name 1", 
                seg_coords = [(1,2),(3,4)], 
                bound_coords = [(5,6),(7,8)],
                new_area = 4, new_iscrowd = True, new_isbbox = True,
                    new_color = 'Green')
    save_annotation(new_image_id = -1, new_category_name= "name 2", 
                seg_coords = [(0,-1),(-2,-3)], 
                bound_coords = [(4,8),(2,4)],
                new_area = 2, new_iscrowd = True, new_isbbox = True,
                    new_color = 'Blue')
    # showing the annotation database
    test_annotations = test_save_ann(img_id = [-1])
    for id in test_annotations:
        for ann in test_annotations[id]:
            print("Annotation found in the database!")
            print("Annotation ID:", str(ann._annotation_id))
            print("Image ID:", str(ann._image_id))
            print("Category ID:", ann._category_id)
            print("Segmentation Coordinates:", 
                ann._segmentation_coordinates)
            print("Bounding Box Coordinates:", 
                ann._bounding_box_coordinates)
            print("Area:", ann._area)
            print("IsCrowd:", ann._iscrowd)
            print("IsBox:", ann._isbbox)
            print("Color:", ann._color)
            print('\n')

    delete_test_ann(test_annotations)

    print('#----------------------------------------------------------')
    ## testing if they export correctly 
    img_id = [-2,-2, -3]
    save_annotation(new_image_id = img_id[0], new_category_name= "name 1", 
                seg_coords = [(1,2),(3,4)], 
                bound_coords = [(5,6),(7,8)],
                new_area = 4, new_iscrowd = True, new_isbbox = True,
                    new_color = 'Green')
    save_annotation(new_image_id = img_id[2], new_category_name= "name 2", 
                seg_coords = [(0,-1),(-2,-3)], 
                bound_coords = [(4,8),(2,4)],
                new_area = 2, new_iscrowd = True, new_isbbox = True,
                    new_color = 'Blue')
    save_annotation(new_image_id = img_id[1], new_category_name= "name 1", 
            seg_coords = [(9,8),(-7,-6)], 
            bound_coords = [(5,4),(3,4)],
            new_area = 9, new_iscrowd = True, new_isbbox = True,
                new_color = 'Red')
    save_annotation(new_image_id = img_id[0], new_category_name= "name 2", 
        seg_coords = [(9,8),(-7,-6)], 
        bound_coords = [(5,4),(3,4)],
        new_area = 9, new_iscrowd = True, new_isbbox = True,
            new_color = 'Red')
    
    print('Exporting by Image ID: ')
    test_expt_img_ann(img_id)
    print('Exporting All Annotations: ')
    test_expt_all_ann()
    test_annotations = test_save_ann(img_id)
    delete_test_ann(test_annotations)
    print('Exporting All Annotations: ')
    test_expt_all_ann()
    print('if clear, all test annotations have been deleted')

    # works but commented out to ensure it does not accidentally delete 
    # a real image's annotations
    # print('-------------------------')
    # print('image annotation 0')
    # annotations = get_img_annotations(0)
    # for ann in annotations:
    #     print(ann)
    # delete_img_annotations(0)
    # print('image annotation 0 after deleting')
    # annotations = get_img_annotations(0)
    # for ann in annotations:
    #     print(ann)
    
    
#-----------------------------------------------------------------------
if __name__ == '__main__':
    # main()
    # print(get_annotations(47))
    print(get_img_annotations(26))