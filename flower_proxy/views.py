from django.http import HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


@require_http_methods(['GET', 'POST'])
@csrf_exempt
def index(req):
    user = req.user
    if not (user.is_authenticated and user.is_staff):
        raise Http404()

    if req.method == 'GET':
        internal_location = 'internal-flower'
    else:
        internal_location = 'internal-flower-post'
    resp = HttpResponse()
    path = req.get_full_path()
    new_path = path.replace('flower', internal_location, 1)
    resp['X-Accel-Redirect'] = new_path
    return resp
