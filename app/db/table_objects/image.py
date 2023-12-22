#-----------------------------------------------------------------------
# images.py
# identifies features of an image 
#-----------------------------------------------------------------------

class Image:
    def __init__(self, image_id, dataset_id, image_path,
                 image_filename, annotated):
        self._image_id = image_id
        self._dataset_id = dataset_id
        self._image_path = image_path
        self._image_filename = image_filename
        self._annotated = annotated
    
    def get_image_id (self):
        return self._image_id
    
    def get_dataset_id (self):
        return self._dataset_id
    
    def get_image_path (self):
        return self._image_path
    
    def get_image_filename (self):
        return self._image_filename
    
    def get_annotation_url(self):
        return f"/annotations?image_id={self._image_id}" # &image_url={self._image_path} <-- UNSAFE implementation
    
    def get_annotated (self):
        return self._annotated
    
    def get_annotated_string (self):
        if self._annotated:
            return "Yes"
        else:
            return "No"
    
    def to_tuple (self):
        return (self._image_id, self._dataset_id, self._image_path,
                 self._image_filename, self._annotated)

#-----------------------------------------------------------------------

def _test():
    image = Image(image_id=1, dataset_id=2, image_path = "/image",
                 image_filename = "image test", annotated = True)
    print(image.get_image_id())
    print(image.get_dataset_id())
    print(image.get_image_path())
    print(image.get_image_filename())
    print(image.get_annotated())
    print(image.to_tuple())

if __name__ == '__main__':
    _test()
