#-----------------------------------------------------------------------
# dataset.py
# identifies features of a dataset 
#-----------------------------------------------------------------------

class Dataset:
    def __init__(self, dataset_id, dataset_names, user_id):
        self._dataset_id = dataset_id
        self._dataset_names = dataset_names
        self._user_id = user_id
    
    def get_dataset_id (self):
        return self._dataset_id
    
    def get_dataset_names (self):
        return self._dataset_names
    
    def get_user_id (self):
        return self._user_id    
    
    def to_tuple (self):
        return (self._dataset_id, self._dataset_names, self._user_id)

#-----------------------------------------------------------------------

def _test():
    dataset = Dataset(dataset_id = 20, dataset_names = 'data 1',
                 user_id = 4)
    print(dataset.get_dataset_id())
    print(dataset.get_dataset_names())
    print(dataset.get_user_id())
    print(dataset.to_tuple())

if __name__ == '__main__':
    _test()
