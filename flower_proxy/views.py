from django.http import HttpResponse, Http404


def index(req):
    user = req.user
    if user.is_authenticated and user.is_staff:
        resp = HttpResponse()
        path = req.get_full_path()
        new_path = path.replace('flower', 'internal-flower', 1)
        resp['X-Accel-Redirect'] = new_path
        return resp
    raise Http404()
