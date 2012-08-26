
class DuplicatePersistJobException(Exception):
    """ Duplicate Persist Job Exception class"""
    pass

class DuplicateTagIdException(Exception):
    """ Duplicate TagID Exception class """
    def __init__(self, tag_id):
        self.id = tag_id

class TagIdDoesNotExistException(Exception):
    pass

class TopicIdDoesNotExistException(Exception):
    pass

class NoActiveChatMinuteException(Exception):
    """ Exception to indicate there was no active chat minute
        when one was required.
    """
    pass