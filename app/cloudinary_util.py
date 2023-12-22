import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary import CloudinaryImage

#-----------------------------------------------------------------------

def configure_cloudinary():
    # Configure Cloudinary
    cloudinary.config( 
    cloud_name = "dzwdvfcqp", 
    api_key = "833488988824539", 
    api_secret = "MuADlFrjAq6VVk1LELl5ChIr97k"
)
''' (For deployment to Render)
def configure_cloudinary():
    # Configure Cloudinary
    cloudinary.config( 
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
'''

#-----------------------------------------------------------------------

def upload_image_to_cloudinary(image_path, image_id):
    try:
        # Upload the image to Cloudinary
        response = cloudinary.uploader.upload(image_path, public_id=str(image_id))

        if 'public_id' in response:
            print("Image uploaded successfully.")
            print(f"Public ID: {response['public_id']}")
            return response['url']
        else:
            print("Image upload failed. Response:", response)
            return None
    except Exception as e:
        # Handle errors
        print(f"Error uploading image to Cloudinary: {str(e)}")
        return None

#-----------------------------------------------------------------------

def get_image_url_from_cloudinary(image_id):
    try:
        # Create a CloudinaryImage object with the public_id (image_id)
        image = CloudinaryImage(image_id)

        # Get the image's URL
        image_url = image.build_url()

        return image_url
    except Exception as e:
        # Handle errors
        print(f"Error getting image URL from Cloudinary: {str(e)}")
        return None
#-----------------------------------------------------------------------

def delete_image_from_cloudinary(image_id):
    try:
        # Delete the image from Cloudinary
        response = cloudinary.uploader.destroy(image_id)
        # print('destroyed',response)
        # print(response.get('result'))
        if response.get('result') == 'ok':
            print("Image deleted successfully.")
            return True, f"Image {image_id} deleted successfully."
        else:
            print(f"Image {image_id} deletion failed. Response: ", response)
            raise Exception(response)
    except Exception as e:
        # Handle errors
        err_msg = f"Image {image_id} deletion failed. Please contact system adminstrator."
        print(err_msg)
        return False, err_msg

