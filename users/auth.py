from rest_framework.renderers import JSONRenderer

class CustomResponse(JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):

        status_code = renderer_context['response'].status_code

        if str(status_code)=='401':
            status_message = "Unauthorized"
        elif not str(status_code).startswith('2'):
            status_message = "Error"
        else:
            status_message = "Success"
        try:
            response = {
                "session": {
                    "refresh":data.get("access",None),
                    "token": data.get("token",None),
                    "validity": 1,
                    "specialMessage": None
                },
                "data": data.get("data",None),
                "status": {
                    "code": status_code,
                    "status": status_message,
                    "message": data.get("message",None)
                }
            }
        except AttributeError:
            response = data

        return super(CustomResponse, self).render(response, accepted_media_type, renderer_context)

