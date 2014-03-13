from .utils import WebUser

def set_experiment_user(target):
    '''Decorator for setting the WebUser for use with ab split testing
    assumes the first argument is the request object'''
    def wrapper(*args, **kwargs):
        request = args[0]
        WebUser(request).confirm_human()
        return target(*args, **kwargs)

    return wrapper
