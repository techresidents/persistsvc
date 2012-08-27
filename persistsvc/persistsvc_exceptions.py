


class DuplicatePersistJobException(Exception):
    """ Duplicate Persist Job Exception class"""
    pass

class DuplicateTagIdException(Exception):
    """ Duplicate TagID Exception class """
    def __init__(self, tag_id):
        self.id = tag_id

class InvalidChatMinuteException(Exception):
    """ Indicates that the ChatMinuteHandler returned
    an invalid ChatMinute object.
    """
    pass

class NoActiveChatMinuteException(Exception):
    """ Exception to indicate there was no active chat minute
        when one was required.
    """
    pass

class TagIdDoesNotExistException(Exception):
    pass

class TopicIdDoesNotExistException(Exception):
    pass

