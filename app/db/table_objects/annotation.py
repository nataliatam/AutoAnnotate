#-----------------------------------------------------------------------
# annotation.py
# identifies features of an annotation 
#-----------------------------------------------------------------------

class Annotation:
    def __init__(self, annotation_id, image_id, category_id,
                 segmentation_coordinates, bounding_box_coordinates,
                 area, iscrowd, isbbox, color):
        self._annotation_id = annotation_id
        self._image_id = image_id
        self._category_id = category_id
        self._segmentation_coordinates = segmentation_coordinates
        self._bounding_box_coordinates = bounding_box_coordinates
        self._area = area
        self._iscrowd = iscrowd
        self._isbbox = isbbox
        self._color = color
    
    def get_annotation_id (self):
        return self._annotation_id
    
    def get_image_id (self):
        return self._image_id
    
    def get_category_id (self):
        return self._category_id
    
    def get_segmentation_coordinates (self):
        return self._segmentation_coordinates
    
    def get_bounding_box_coordinates (self):
        return self._bounding_box_coordinates                                
    
    def get_area (self):
        return self._area
    
    def get_iscrowd (self):
        return self._iscrowd
    
    def get_isbbox (self):
        return self._isbbox
    
    def get_color (self):
        return self._color
    
    def to_tuple (self):
        return (self._annotation_id, self._image_id ,self._category_id,
                self._segmentation_coordinates, 
                self._bounding_box_coordinates, self._area,
                self._iscrowd, self._isbbox, self._color)

#-----------------------------------------------------------------------

def _test():
    annotation = Annotation(annotation_id = 1, image_id = 2, 
                            category_id = 3,
                 segmentation_coordinates = [1,2], 
                 bounding_box_coordinates = [3,4],
                 area = 2.56, iscrowd = True, isbbox = True, 
                 color = 'green')
    print(annotation.get_annotation_id())
    print(annotation.get_image_id())
    print(annotation.get_category_id())
    print(annotation.get_segmentation_coordinates())
    print(annotation.get_bounding_box_coordinates())
    print(annotation.get_area())
    print(annotation.get_iscrowd())
    print(annotation.get_isbbox())
    print(annotation.get_color())
    print(annotation.to_tuple())

if __name__ == '__main__':
    _test()
