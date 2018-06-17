from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, render

from .models import Community
from .forms import CommunitySearchForm


PAGE_SIZE = 50
LIST_MAX = 10 * PAGE_SIZE


@require_GET
def list_(req):
    form = CommunitySearchForm(req.GET)
    if not form.is_valid():
        raise Http404()
    sort_field = form.cleaned_data.pop('sort_field')
    inverse = form.cleaned_data.pop('inverse')
    qs = Community.search.sort_by(sort_field, inverse).filter(**form.cleaned_data)
    paginator = Paginator(qs[:LIST_MAX], PAGE_SIZE)
    page_num = req.GET.get('p', 1)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404()
    return render(req, 'communities/list.html', {'page': page, 'form': form})


@require_GET
def detail(req, community_id):
    community_id = int(community_id)
    raise Http404()
