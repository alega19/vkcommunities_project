from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, render
from django.db.models import F

from .models import Community, CommunityHistory
from .forms import CommunitySearchForm


PAGE_SIZE = 50
LIST_MAX = 10 * PAGE_SIZE


@require_GET
def list_(req):
    form = CommunitySearchForm(req.GET)
    if form.is_valid():
        params = form.cleaned_data
    else:
        params = {
            'verified': None,
            'ctype': None,
            'age_limit': None,
            'sort_by': 'followers',
            'inverse': True,
        }
        form = CommunitySearchForm(initial=params)
    qs = Community.available.filter_ignoring_nonetype(
        verified=params['verified'],
        ctype=params['ctype'],
        age_limit=params['age_limit'],
    ).exclude_nulls(
        params['sort_by']
    ).sort_by(params['sort_by'], params['inverse'])
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
    community = get_object_or_404(Community, pk=community_id)
    history = list(CommunityHistory.objects.filter(
        community=community,
    ).values(
        x=F('checked_at'),
        y=F('followers'),
    ))
    return render(req, 'communities/detail.html', {'community': community, 'history': history})
