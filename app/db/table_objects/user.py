#-----------------------------------------------------------------------
# user.py
# identifies features of user 
#-----------------------------------------------------------------------

class User:
    def __init__(self, user_id, username):
        self._user_id = user_id
        self._username = username
    
    def get_user_id (self):
        return self._user_id
    
    def get_username (self):
        return self._username
    
    def to_tuple (self):
        return (self._user_id, self._username)

#-----------------------------------------------------------------------

def _test():
    user = User(user_id = 34, username = 'Indu')
    print(user.get_user_id())
    print(user.get_username())
    print(user.to_tuple())

if __name__ == '__main__':
    _test()
