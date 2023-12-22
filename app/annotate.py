''' Run the surver for the web-based Annotate application '''
# !/usr/bin/env python
#-----------------------------------------------------------------------
# annotate.py
#-----------------------------------------------------------------------
# import packages
import flask
from flask import Flask
import shapely
import json
import distinctipy
import dotenv
import auth
from flask import request
from flask import jsonify
import prefill_utils
import sys
# tables:
import db.db_annotations as db_annon
import db.db_images as db_img
import db.db_dataset as db_set
import db.db_user as db_user
import db.db_categories as db_cat

import cloudinary_util
import numpy as np 
from db.db_images import filter_imgs
from db.db_annotations import get_annotations
import wget
from db.table_objects.category import Category_with_ann
# relative imports not working for some reason,
# copied all db files over to app for now 
# from ..db.db_annotations import save_annotation, get_all_annotations
from db.db_annotations import save_annotation, get_all_annotations

#-----------------------------------------------------------------------
# Cloudinary features (for testing upload and get)
# Configure Cloudinary
cloudinary_util.configure_cloudinary()
#-----------------------------------------------------------------------
app = flask.Flask(__name__, template_folder='templates')
print("Flask app is executed")
dotenv.load_dotenv()
# app.secret_key = os.environ['APP_SECRET_KEY']
app.secret_key = 'AutoAnnotate'
#-----------------------------------------------------------------------
# This list will temporarily store annotations in memory, 
# we need to store annotations in a database
annotations = []

# determine new session
# is_new_session = {'record':True}
#-----------------------------------------------------------------------
# Routes for authentication.
@app.route('/login', methods=['GET'])
def login():
    return auth.login()
@app.route('/login/callback', methods=['GET'])
def callback():
    return auth.callback()
@app.route('/logoutapp', methods=['GET'])
def logoutapp():
    return auth.logoutapp()
#-----------------------------------------------------------------------
@app.route('/')
def index():
 
    # if is_new_session['record']: 
    #     is_new_session['record'] = False
    #     auth.login()
    auth.authenticate()
    user_email = flask.session.get('email', 'No user logged in')
    html_code = flask.render_template('display.html', user_email=user_email)
    response = flask.make_response(html_code)
    return response
#-----------------------------------------------------------------------
def get_user_set_id():
    try:
        user_email = flask.session.get('email')  # Get user ID from session
        ## want to save user if new or do just get the postgres id of the 
        # data already in the database - also saves dataset
        user_success, user_id = db_user.save_user(user_email)
        if user_success:
            dataset_id = db_set.get_dataset_id(user_id)
            if isinstance(dataset_id, bool):
                raise Exception("Please contact System Admin: Login in not properly saved in database")
            return True, dataset_id
        else: return False, "Please contact System Admin: " + str(user_id)
    except Exception as ex:
        ## the following exception deal with database corruptions 
        # specifically, for if user information is deleted
        print("Warning: ",ex)
        user_email = flask.session.get('email')
        ## want to save user if new or just get the postgres id if the 
        # data already in the database - also saves dataset
        user_success, user_id = db_user.save_user(user_email)
        if user_success: 
            dataset_id = db_set.get_dataset_id(user_id)
            if isinstance(dataset_id, bool):
                return False,  "Please contact System Admin: failed to get dataset id"
            print(f"Update: Saved {user_email} with user id {user_id} and dataset id {dataset_id}")
            return True, dataset_id
        else: return False,  "Please contact System Admin: " + str(user_id)

#-----------------------------------------------------------------------
# Routes for UPLOAD images, which included uploading to Cloudinary
@app.route('/upload_image', methods=['POST'])
def upload_image():
    auth.authenticate()
    set_success, dataset_id = get_user_set_id()
    if not set_success: raise Exception(dataset_id)
    # Receive data from the client, including the image path and image ID
    data = request.get_json()
    image_data = data['data']
    image_filename = data['image_filename']
    # image_id = db_img.gen_img_id()
    # print("uploading image id", image_id)
    try:
        exit_status, output = db_img.save_new_img(image_data = image_data,
                            new_dataset_id=dataset_id, new_annotated=False,
                            new_img_filename=image_filename)
        if exit_status == 0: # success
            image_id = output
            print("image id in server: ",image_id)
            # Send a response to the client
            return flask.jsonify({"message": "Image uploaded successfully", 
                                "imageID": image_id}), 200
        else: # upload failed
            return flask.jsonify({"message": output}), 500 
    except Exception as ex:
        # Handle errors
        app.logger.error(f"System uploading error: {str(ex)}")
        return flask.jsonify({"message": f" Please contact system admin..System uploading error: {str(ex)}"}), 500 
    
#-----------------------------------------------------------------------
# Route for getting list of images currently stored in database
@app.route('/get_image_list', methods=['GET'])
def get_image_list():
    auth.authenticate()  # This will redirect if the user is not logged in
    set_success, dataset_id = get_user_set_id()
    if not set_success: 
        # send descriptive error message, output[0], to stderr
        print(f"{sys.argv[0]}: {dataset_id}", file=sys.stderr)
        # display generic server error,  output[1]
        html_code = flask.render_template("imagelist_error.html",
                                        error = dataset_id)
        response = flask.make_response(html_code)
        return response
    else:
        filename = flask.request.args.get("filename")
        image_id = flask.request.args.get("image_id")
        
        # real code for getting list of images from database 
        exit_status, output = filter_imgs(filename, dataset_id, image_id)
        if exit_status == 0: # no error
            # image_ids = []
            # for image in output:
            #     image_ids.append(image.get_image_id())
            # print(f"\nimage_ids: {image_ids}\n", file=sys.stderr)
            html_code = flask.render_template("imagelist.html",
                                            allImages = output)
            response = flask.make_response(html_code)
            return response # flask.jsonify(response, len(output))
        else: 
            # send descriptive error message, output[0], to stderr
            print(f"{sys.argv[0]}: {output[0]}", file=sys.stderr)
            # display generic server error,  output[1]
            html_code = flask.render_template("imagelist_error.html",
                                            error = output[1])
            response = flask.make_response(html_code)
            return response


#-----------------------------------------------------------------------
# Route for getting the url of the given image
@app.route('/get_image_url', methods=['GET'])
def get_image_url():
    auth.authenticate()  # This will redirect if the user is not logged in
    set_success, dataset_id = get_user_set_id()
    if not set_success: 
        print(f"{sys.argv[0]}: {dataset_id}", file=sys.stderr)
        return json.dumps({"image_found":False, 
                           "message": dataset_id})

    filename = None
    image_id = flask.request.args.get("image_id")
    
    # real code for getting list of images from database 
    exit_status, output = filter_imgs(filename, dataset_id, image_id)
    if exit_status == 0 and len(output) > 0: # no error
        return json.dumps({"image_found":True, 
                           "image_url": output[0].get_image_path()})
    else: # error or user does not have this image
        # send descriptive error message, output[0], to stderr
        print(f"{sys.argv[0]}: {output}", file=sys.stderr)
        return json.dumps({"image_found":False, 
                           "message": "Image not found. Redirecting you to dashboard. Please contact the system administrator if you think this is a mistake."})
#-----------------------------------------------------------------------
# Route for deleting an image when prompted
@app.route('/delete_image', methods=['GET'])
def delete_image():
    image_id = flask.request.args.get("image_id")
    print("deleteing image "+image_id, file=sys.stderr)
    try:
        # Delete image from database
        db_success, img_msg = db_img.delete_img(image_id) 
        if db_success:
            # If successful, delete corresponding data from Cloudinary
            deleted_URL, cloud_msg = cloudinary_util.delete_image_from_cloudinary(image_id)
            if deleted_URL:
                print(cloud_msg)
                return flask.jsonify({"message": img_msg}), 200
            else:
                return flask.jsonify({"message":f"Please Contact System Admim., Failed to delete image {image_id} from database: " + str(cloud_msg)}), 500
        else: 
            return flask.jsonify({"message":  f"Please Contact System Admim., Failed to delete image {image_id}: " + str(img_msg)}), 500
    except Exception as ex:
        print(ex)
        return flask.jsonify({"message":  f"Please Contact System Admim., Failed to delete image {image_id}"}), 500
#-----------------------------------------------------------------------
# Route for deleting all images
@app.route('/delete_all_images', methods=['GET'])
def delete_all_images():
    ## get user's images only 
    auth.authenticate()
    try:
        set_success, dataset_id = get_user_set_id()
        if not set_success: raise Exception(dataset_id)
        success, all_images = db_img.get_all_images_with_error(dataset_id)
        if success == 0:
            image_ids = []
            for image in all_images:
                # (public id for cloudinary is str(image_id))!!
                image_ids.append(str(image.get_image_id()))
            images_deleted = []
            # Delete image from Cloudinary 
            for id in image_ids:
                # If successful, delete corresponding data from PostgreSQL
                img_success, img_msg = db_img.delete_img(id) 
                if img_success:
                    deleted_URL, cloud_msg = cloudinary_util.delete_image_from_cloudinary(id)
                    if deleted_URL:
                        print(f"Image {id} fully deleted")
                        images_deleted.append(id)
                    else: 
                        raise Exception(f"Please Contact System Admim.,Failed to delete image with id {id} : {cloud_msg}")
                else: 
                    raise Exception(f"Please Contact System Admin., Failed to delete image with id {id} : {img_msg}")
            return flask.jsonify({'num_images': len(images_deleted),
                                'images_deleted': images_deleted}), 200
        else: raise Exception(f"Failed to get all images")
    except Exception as ex:
        print(ex)
        return flask.jsonify({"message": f"Failed to delete all. Please contact system adminstrator"}), 500
    
#-----------------------------------------------------------------------
# Route for getting saved annotations give image id 
@app.route('/load_annotations', methods=['GET'])
def load_annotations():
    image_id = flask.request.args.get("image_id")
    print(f"Load annotations for image id {image_id}")
    try:
        # real code for getting list of images from database 
        success, ann_data = get_annotations(image_id)
        if success:
            polygons, category_names, category_ids, cat_colors, colors, ann_ids = \
                ann_data[0], ann_data[1], ann_data[2], ann_data[3], ann_data[4], ann_data[5], 
            print("Loaded annotations ",ann_ids)
            # current polygon format: [[{'x':...,'y':...},{'x':...,'y':...},...],[{'x':...,'y':...},{'x':...,'y':...},...],[...]]
            # make new polygon format: x_coords=[x,x,x,...] and y_coords=[y,y,y,...] with polygon sizes [1,2,3,...]
            # annotation_ids should have the same length as polygon_sizes
            x_coords, y_coords, polygon_sizes = [], [], []

            polygon_data = {
                'x_coords' : {}, 
                'y_coords' : {}, 
                'polygon_sizes' : {}, 
                'ann_ids': ann_ids
            }

            for i in range(len(polygons)):
                num_points = 0
                ann_id = ann_ids[i]
                for coord in polygons[i]:
                    x_coords.append(coord['x'])
                    y_coords.append(coord['y'])
                    num_points += 1
                    try:
                        polygon_data['x_coords'][ann_id].append(coord['x'])
                        polygon_data['y_coords'][ann_id].append(coord['y'])
                    except:
                        polygon_data['x_coords'][ann_id] = [coord['x']]
                        polygon_data['y_coords'][ann_id] = [coord['y']]
                polygon_sizes.append(num_points)
                polygon_data['polygon_sizes'][ann_id] = num_points

            annotation_data = {
                'x_coords' : x_coords, 
                'y_coords' : y_coords, 
                'polygon_sizes' : polygon_sizes, 
                'colors' : colors, # [(R,G,B),(R,G,B),(R,G,B),...]
                'ann_ids': ann_ids
            }    

            cat_ann = {}
            cat_name = {}
            # print(f"before: cat_ann: {cat_ann}")

            # collect the annotations and name under each category 
            for i in range(len(ann_ids)):
                try: 
                    cat_ann[category_ids[i]].append(ann_ids[i])
                except Exception as ex:
                    cat_ann[category_ids[i]] = [ann_ids[i]]
                    cat_name[category_ids[i]] = category_names[i]

            # create category objects for value retrieval in html
            cats = []
            unique_cat_ids = list(set(category_ids))
            for i in range(len(unique_cat_ids)):
                cat_id = unique_cat_ids[i]
                r,g,b = cat_colors[cat_name[cat_id]]
                cats.append(Category_with_ann(cat_id, 
                                            cat_name[cat_id],
                                            cat_ann[cat_id],
                                            r=r,
                                            g=g,
                                            b=b))

            categories_html = flask.render_template("categories.html",
                                                    allCat = cats)
            
            # create a list of annotations (html) for each category 
            annotation_htmls = {}
            for i in range(len(unique_cat_ids)):
                cat_id = unique_cat_ids[i]
                html = flask.render_template("annotations.html",
                                            cat_id = cat_id,
                                            cat_name = cat_name[cat_id],
                                            allAnn = cat_ann[cat_id])
                annotation_htmls[cat_id] = html

            no_annotations_html = flask.render_template("no_annotations.html")
            
            dict = {'categories_html' : categories_html,
                    'cat_IDs' : category_ids,
                    'annotation_data' : annotation_data,
                    'annotation_htmls': annotation_htmls,
                    'no_annotations_html': no_annotations_html,
                    'polygon_data' : polygon_data,
                    'annotation_id_per_cat' : cat_ann}
            return flask.jsonify(dict)
        else: 
            raise Exception(ann_data)
    except Exception as ex:
        return flask.jsonify({"message": f"Failed to load annotations. Please contact system adminstrator : {ex}"}), 500
#-----------------------------------------------------------------------
# Route for getting saved annotations give image id and category id
@app.route('/load_cat_annotations', methods=['GET'])
def load_cat_annotations():
    image_id = flask.request.args.get("image_id")
    cat_id = flask.request.args.get("cat_id")

    # # real code for getting list of images from database 
    # polygons, ann_ids = db_annon.get_cat_annotations(image_id, cat_id)
    # # current polygon format: [[{'x':...,'y':...},{'x':...,'y':...},...],[{'x':...,'y':...},{'x':...,'y':...},...],[...]]
    # # make new polygon format: x_coords=[x,x,x,...] and y_coords=[y,y,y,...] with polygon sizes [1,2,3,...]
    # # annotation_ids should have the same length as polygon_sizes
    # x_coords, y_coords, polygon_sizes = [], [], []
    # for polygon in polygons:
    #     num_points = 0
    #     for coord in polygon:
    #         x_coords.append(coord['x'])
    #         y_coords.append(coord['y'])
    #         num_points += 1
    #     polygon_sizes.append(num_points)
    # annotation_data = {
    #     'x_coords' : x_coords, 
    #     'y_coords' : y_coords, 
    #     'polygon_sizes' : polygon_sizes, 
    #     'ann_ids': ann_ids
    # }

    # placeholder value
    annotation_data = {
        'x_coords' : [1,2,3,3,4,5,6], 
        'y_coords' : [2,3,4,3,4,1,4], 
        'polygon_sizes' : [3,4], 
        'ann_ids': [1,2]
    }

    return flask.jsonify(annotation_data)

#-----------------------------------------------------------------------
# TODO: Route for deleting all annotations in a category
@app.route('/delete_category', methods=['POST'])
def delete_category():
    try:
        data = request.get_json()
        image_id = data['image_id']
        cat_id = data['category_id']
        success = db_annon.delete_anns_for_cat(image_id, cat_id) # TO BE IMPLEMENTED
        if success:
            return jsonify({"message": f"Annotations under category {cat_id} in image {image_id} removed successfully."}), 200
        else:
            raise Exception()
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"An error occurred in deleting annotations for category. {e}"}), 500
#-----------------------------------------------------------------------
# Routes for generating image id and sending to front end
# TODO see if we can delete - 
@app.route('/generate_id', methods=['GET'])
def generate_id():
    auth.authenticate()
    # call an image id through function made by Maria; for now, stand-in value
    # image_id = {-1}
    image_id = db_img.gen_img_id()
    return jsonify(image_id)
#-----------------------------------------------------------------------
# Route for getting number of images in database
@app.route('/get_image_ids', methods=['GET'])
def get_image_ids():
    auth.authenticate()
    try:
        set_success, dataset_id = get_user_set_id()
        if not set_success: 
            raise Exception(dataset_id)
        success, all_images = db_img.get_all_images_with_error(dataset_id)
        if success == 0:
            num_images = len(all_images)
            image_ids = []
            for image in all_images:
                image_ids.append(image.get_image_id())
            # print(f"\nimage_ids: {image_ids}\n", file=sys.stderr)
            return flask.jsonify({'num_images': num_images,
                                'image_ids': image_ids}), 200
        else: raise Exception(f"Failed to get all images, Please contact system adminstrator")
    except Exception as ex:
        return flask.jsonify({"message": f"{ex}"}), 500
#-----------------------------------------------------------------------
# Routes for new Annotation Page
@app.route('/annotations', methods=['GET'])
def annotation_page():
    # Retrieve the image with ID 'image_id'
    # and pass it to the 'index.html' template for annotation
    auth.authenticate()
    html_code = flask.render_template('index.html')
    response = flask.make_response(html_code)
    return response
#-----------------------------------------------------------------------
@app.route('/export_annotations', methods=['GET','POST'])
def export_annotations():
    # app = Flask(__name__)
    # app.json.sort_keys = False
    # TODO: dont let flask.jsonify resort the keys... 
    # but dict is not a sorted structure
    auth.authenticate()
    try:
        image_id = flask.request.get_json()['id']
        print("export clicked", file=sys.stderr)
        exported_dict = dict()
        success, annotations = db_annon.get_img_annotations(image_id)
        if success:
            exported_dict["annotations"] = annotations
            # fixing to Indu's format: 
            # return flask.json.dumps(exported_dict, indent = 2, sort_keys=False)
            # print(f"type(exported_dict): {type(exported_dict)}")
            return json.dumps(exported_dict, indent=2, default=int)
        else: raise Exception(f"Please Contact System Admin: {annotations}")
    except Exception as ex:
        return flask.jsonify({"message": f"{ex}"}), 500
#-----------------------------------------------------------------------
@app.route('/export_all_annotations', methods=['GET','POST'])
def export_all_annotations():
    auth.authenticate()
    print("export clicked", file=sys.stderr)
    try:
        annotations, num_images = db_annon.get_all_annotations()
        if isinstance(annotations, bool):
            raise Exception(num_images)
        dicti = {"annotations":annotations, "num_images":num_images}
        # print(f"type(dicti): {type(dicti)}")
        return json.dumps(dicti, indent=2, default=int)
    except Exception as ex:
        return flask.jsonify({"message": f"{ex}"}), 500
    
#-----------------------------------------------------------------------
# Route for Save Annotations
@app.route('/save_annotations', methods=['POST'])
def save_annotations():
    auth.authenticate()
    try:
        annotation_data = flask.request.get_json()
        #print(annotation_data, file=sys.stderr) # testing
        # Process the received annotation data (store it, associate it with an image, etc.)
        # For MVP, we'll just append the annotations to the corresponding image
        for annotation in annotations:
            if "image" in annotation and "image" in annotation_data:
                if annotation["image"] == annotation_data["image"]:
                    annotation["annotations"] = annotation_data["annotations"]
        # Calculate bounding box coordinates ([x, y, width, height])
        ## gets the last element, which is most recent datapoints
        points = annotation_data["seg_coords"] 
        # print(f"points: {points}")
        # [[{'x': x 'y': y},{'x': x, 'y': y},...]]
        x, y = [], []
        for point in points:
            x.append(point['x'])
            y.append(point['y'])
        x, y = np.array(x), np.array(y)
        
        min_x, max_x, min_y, max_y = x.min(), x.max(), y.min(), y.max()
        bbox = [min_x, min_y, max_x-min_x, max_y-min_y]
        #print(f"bbox:{bbox}", file=sys.stderr)
        # Calculate polygon area
        # taken from https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
        area = 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))
        #print(f"area:{area}", file=sys.stderr)
        # For prototype, simply save annotation_data
        try:
            ann_id = db_annon.save_annotation(annotation_data["new_image_id"],
                            annotation_data["new_category_name"],
                            annotation_data["seg_coords"],
                            bbox, # annotation_data["bound_coords"],
                            area, # annotation_data["new_area"],
                            annotation_data["new_iscrowd"],
                            annotation_data["new_isbbox"],
                            annotation_data["new_color"])
            # we would also want to update the image 
            # that it is saved to show as annotated
            # print("ann id ",annotation_data["new_image_id"])
            update_success = db_img.update_img_meta(annotation_data["new_image_id"], new_annotated =True)
            if update_success:
                return flask.jsonify({"message": "Annotations saved to database.", "annotationId": ann_id}), 200
            else: raise Exception("Failed to update image with this annotation: Please contact System Adminstrator")
        except Exception as ex:
            print(f"Error saving annotation: {ex}", file=sys.stderr)
            return flask.jsonify({"message": "Annotations failed to save.", "error": str(ex)}), 500
    except KeyError as key_error:
        print(f"KeyError: {key_error}", file=sys.stderr)
        return flask.jsonify({"message": "KeyError occurred, Missing required data.", "error": str(key_error)}), 400
    except Exception as ex:
        print(f"Exception: {ex}", file=sys.stderr)
        return flask.jsonify({"message": "An error occurred while saving annotations.", "error": str(ex)}), 500

@app.route('/get_or_create_category', methods=['POST'])
def get_or_create_category():
    try:
        category_name = flask.request.json['category_name']
        successful_cat, category_id = db_cat.save_cat(category_name)
        if successful_cat:
            return flask.jsonify({'categoryId': category_id}), 200
        else: raise Exception("failed to successfully save category")
    except Exception as ex:
        return flask.jsonify({"message": f"An error occurred while saving category {category_name}. Please contact system admin.",
                               "error": str(ex)}), 500

# Route for Save Annotations
@app.route('/save_kmeans_annotations', methods=['POST'])
def save_kmeans_annotations():
    auth.authenticate()
    try:
        annotation_data = flask.request.get_json()
        #print(annotation_data, file=sys.stderr) # testing
        # Process the received annotation data (store it, associate it with an image, etc.)
        # For MVP, we'll just append the annotations to the corresponding image
        for annotation in annotations:
            if "image" in annotation and "image" in annotation_data:
                if annotation["image"] == annotation_data["image"]:
                    annotation["annotations"] = annotation_data["annotations"]
        # Calculate bounding box coordinates ([x, y, width, height])
        ## gets the last element, which is most recent datapoints
        points = annotation_data["seg_coords"] 
        # print(f"points: {points}")
        # [[{'x': x 'y': y},{'x': x, 'y': y},...]]
        x, y = [], []
        for point in points:
            x.append(point['x'])
            y.append(point['y'])
        x, y = np.array(x), np.array(y)
        
        min_x, max_x, min_y, max_y = x.min(), x.max(), y.min(), y.max()
        bbox = [min_x, min_y, max_x-min_x, max_y-min_y]
        #print(f"bbox:{bbox}", file=sys.stderr)
        # Calculate polygon area
        # taken from https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
        area = 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))
        #print(f"area:{area}", file=sys.stderr)
        # For prototype, simply save annotation_data
        try:
            ann_id = db_annon.save_kmeans_annotation(annotation_data["new_image_id"],
                            annotation_data["category_id"],
                            annotation_data["seg_coords"],
                            bbox, # annotation_data["bound_coords"],
                            area, # annotation_data["new_area"],
                            annotation_data["new_iscrowd"],
                            annotation_data["new_isbbox"],
                            annotation_data["new_color"])
            # we would also want to update the image 
            # that it is saved to show as annotated
            # print("ann id ",annotation_data["new_image_id"])
            update_success = db_img.update_img_meta(annotation_data["new_image_id"], new_annotated =True)
            if update_success:
                return flask.jsonify({"message": "Annotations saved to database.", "annotationId": ann_id}), 200
            else: raise Exception("Failed to update image with this annotation: Please contact System Adminstrator")
        except Exception as ex:
            print(f"Error saving annotation: {ex}", file=sys.stderr)
            return flask.jsonify({"message": "Annotations failed to save.", "error": str(ex)}), 500
    except KeyError as key_error:
        print(f"KeyError: {key_error}", file=sys.stderr)
        return flask.jsonify({"message": "KeyError occurred, Missing required data.", "error": str(key_error)}), 400
    except Exception as ex:
        print(f"Exception: {ex}", file=sys.stderr)
        return flask.jsonify({"message": "An error occurred while saving annotations.", "error": str(ex)}), 500

'''
@app.route('/save_annotations', methods=['POST'])
def save_annotations():
    auth.authenticate()
    try:
        annotation_data = flask.request.get_json()
        print(annotation_data, file=sys.stderr) # testing
        # Process the received annotation data (store it, associate it with an image, etc.)
        # For MVP, we'll just append the annotations to the corresponding image
        for annotation in annotations:
            if "image" in annotation and "image" in annotation_data:
                if annotation["image"] == annotation_data["image"]:
                    annotation["annotations"] = annotation_data["annotations"]
        # Calculate bounding box coordinates ([x, y, width, height])
        ## gets the last element, which is most recent datapoints
        points = annotation_data["seg_coords"] 
        print(f"points: {points}")
        # [[{'x': x 'y': y},{'x': x, 'y': y},...]]
        x, y = [], []
        for point in points:
            x.append(point['x'])
            y.append(point['y'])
        x, y = np.array(x), np.array(y)
        
        min_x, max_x, min_y, max_y = x.min(), x.max(), y.min(), y.max()
        bbox = [min_x, min_y, max_x-min_x, max_y-min_y]
        print(f"bbox:{bbox}", file=sys.stderr)
        # Calculate polygon area
        # taken from https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
        area = 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))
        print(f"area:{area}", file=sys.stderr)
        # For prototype, simply save annotation_data
        try:
            ann = db_annon.save_annotation(annotation_data["new_image_id"],
                            annotation_data["new_category_name"],
                            annotation_data["seg_coords"],
                            bbox, # annotation_data["bound_coords"],
                            area, # annotation_data["new_area"],
                            annotation_data["new_iscrowd"],
                            annotation_data["new_isbbox"],
                            annotation_data["new_color"])
            response = flask.jsonify({"message": "Annotations saved to database.", "annotationId": ann.annotation_id}), 200
        except Exception as ex:
            response = flask.jsonify({"message": f"Annotations failed to save. {ex}"}), 200
        return response
    except KeyError as key_error:
        response = flask.jsonify({"message": f"KeyError: {key_error}"}), 400  # Handle KeyError
        return response
    except Exception as ex:
        response = flask.jsonify({"message": f"Annotations failed to save. {ex}"}), 500
        return response
'''
#-----------------------------------------------------------------------
# Route for Undo
@app.route('/undo', methods=['POST'])
def undo_annotation():
    image_id = request.json['image_id']
    for annotation in annotations:
        if annotation['image'] == image_id and annotation['annotations']:
            annotation['annotations'].pop()
            return jsonify({"message": "Undo successful."})
    return jsonify({"message": "Undo failed."})
#-----------------------------------------------------------------------
# Route for Reset

@app.route('/delete-all-annotations', methods=['POST'])
def reset_canvas():
    image_id = request.json['image_id']
    try:
        # Call function to delete all annotations for the given image in the database
        success, msg = db_annon.delete_img_annotations(image_id)
        if success:
            return jsonify({"message": "All annotations for the image have been successfully deleted."}), 200
        else:
            raise Exception(msg)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"failed to delete annotations from database"}), 500
#-----------------------------------------------------------------------
# Route for Removing a Polygon
@app.route('/update_polygons', methods=['POST'])
def update_polygons():
    try:
        data = request.get_json()
        annotation_id = data['annotation_id']
        success, msg = db_annon.delete_annotation(annotation_id)
        if success:
            return jsonify({"message": "Annotation removed successfully."}), 200
        else:
            raise Exception(msg)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": f"An error occurred. Please contact system admin.: {e}"}), 500
#-----------------------------------------------------------------------
# Route for Prefilled Annotations
# QUESTION: Do I have to convert all of the numpy arrays into lists?
@app.route('/prefill', methods=['POST'])
def annotation_page_prefilled():
    auth.authenticate()
    image_cloudinary_path = flask.request.get_json()['image_path']
    # image_cloudinary_path = "/Users/net02/Desktop/COS333/COS333_AutoAnnotate/labrador_r02104540.tif"
    num_suppixels = int(flask.request.get_json()['suppix_num'])
    k = int(flask.request.get_json()['k'])
    print(image_cloudinary_path, num_suppixels, k)
    exit_status, output = prefill_utils.prefill_pixels(image_cloudinary_path, num_suppixels, k)
    if exit_status == 0: # successful
        suppixel_coords, kmeans_labels, segments = output
        unique = np.unique(kmeans_labels)
        print(unique)
        colors = np.array(distinctipy.get_colors(k)) * 255
        colors_list = colors.astype(int).tolist()
        kmeans_labels_list = kmeans_labels.tolist()
        segments_list = segments.tolist()
        suppixel_coords_list = []
        for suppix in suppixel_coords:
            suppix = suppix.tolist()
            suppixel_coords_list.append(suppix)
        #print("suppixel_coords", type(suppixel_coords))
        #print("suppixel_coord", type(suppixel_coords_list[0]))
        #print("suppixel_coord[0]", suppixel_coords_list[0])
        data = {
            'success': True,
            'suppixel_coords' : suppixel_coords_list,
            'kmeans_labels' : kmeans_labels_list,
            'segments' : segments_list,
            'colors' : colors_list
        }
        return jsonify(data)
    else:
        data = {'success': False}
        return jsonify(data)
#-----------------------------------------------------------------------
# Route for Identifying Clicked Super Pixel
# QUESTION: should this method change the kmeans label list or should the front end change the label list
@app.route('/identify_superpixel', methods=['POST'])
def annotation_page_identify():
    auth.authenticate()
    suppixel_coords = (flask.request.get_json()['suppix_cords']) # TODO: must get this somehow
    point = (flask.request.get_json()['point']) # TODO: must get from the mouse click
    point1 = shapely.geometry.Point(point['x'], point['y'])
    index = -1
    for i, pixel in enumerate(suppixel_coords):
        polygon = shapely.geometry.Polygon(pixel)
        if point1.within(polygon):
            index = i
            break
    data = {'index' : index}
    return jsonify(data)
#-----------------------------------------------------------------------
# Route for Merging/"Unannotating" Super Pixels
# QUESTION: should this be called every time a pixel is "unannotated"
@app.route('/merge', methods=['POST'])
def annotation_page_merge():
    auth.authenticate()
    img_path = flask.request.get_json()['image_path']
    kmeans_labels = flask.request.get_json()['klabels']
    print("kmeans_labels before np array ",kmeans_labels)
    kmeans_labels = np.array(kmeans_labels)
    segments = flask.request.get_json()['segments']
    segments = np.array(segments)
    print("before kmeans merge called")
    filtered_coords, merged_kmeans_labels, merged_segments = prefill_utils.merge_superpixels(img_path, kmeans_labels, segments)
    print("after kmeans merge called")
    coords_list = []
    unique = np.unique(merged_kmeans_labels)
    print("unique ",unique)
    for suppix in filtered_coords:
        suppix = suppix.tolist()
        coords_list.append(suppix)
    print("merged_kmeans_labels ", merged_kmeans_labels)
    labels_list = merged_kmeans_labels.tolist()
    segments_list = merged_segments.tolist()
    colors = np.array(distinctipy.get_colors(len(coords_list))) * 255
    colors = colors.astype(int).tolist()
    data = {
        'suppixel_coords' : coords_list,
        'kmeans_labels' : labels_list,
        'segments' : segments_list,
        'colors' : colors
    }
    print("labels: ", labels_list)
    return jsonify(data)
# -----------------------------------------------------------------------