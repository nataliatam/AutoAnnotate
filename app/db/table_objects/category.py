#-----------------------------------------------------------------------
# category.py
# identifies features of a category 
#-----------------------------------------------------------------------

class Category:
    def __init__(self, category_id, category_name):
        self._category_id = category_id
        self._category_name = category_name
    
    def get_category_id (self):
        return self._category_id
    
    def get_category_name (self):
        return self._category_name
    
    def to_tuple (self):
        return (self._category_id, self._category_name)
    
class Category_with_ann:
    def __init__(self, category_id, category_name, annotations, r,g,b):
        self._category_id = category_id
        self._category_name = category_name
        self._annotations = annotations
        self._r = r # R of RGB
        self._g = g # G of RGB
        self._b = b # B of RGB
    
    def get_category_id (self):
        return self._category_id
    
    def get_category_name (self):
        return self._category_name
    
    def get_annotations (self):
        return self._annotations

    def get_r (self):
        return self._r
    
    def get_g (self):
        return self._g
    
    def get_b (self):
        return self._b
    
#-----------------------------------------------------------------------

def _test():
    category = Category(category_id = 17, category_name = 'category a')
    print(category.get_category_id())
    print(category.get_category_name())
    print(category.to_tuple())

if __name__ == '__main__':
    _test()
