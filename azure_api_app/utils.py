# rest_framework
from rest_framework.response import Response
from rest_framework import status


def handle_exceptions(is_status=False):

    def decorator(view_func):
        def wrapped_view(*args, **kwargs):
            try:
                return view_func(*args, **kwargs)
            except Exception as e:
                if is_status:
                    return False
                
                response = {
                    "status": "error",
                    "message": "Something went wrong..!",
                    "error": str(e),
                }
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return wrapped_view
    
    return decorator