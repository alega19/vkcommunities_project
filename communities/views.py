from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, render
from django.db.models import F, FloatField, Case, When, Q, ExpressionWrapper, Value
from django.db.models.functions import Cast

from .models import Community, CommunityHistory, Post
from .forms import CommunitySearchForm, PostSearchForm


PAGE_SIZE = 50
LIST_MAX = 10 * PAGE_SIZE

POST_PAGE_SIZE = 20
POST_LIST_MAX = 10 * POST_PAGE_SIZE


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


@require_GET
def post_list(req):
    form = PostSearchForm(req.GET)
    if form.is_valid():
        params = form.cleaned_data
    else:
        params = {
            'community_id': None,
            'date_min': None,
            'date_max': None,
            'marked_as_ads': None,
            'has_links': None,
            'sort_by': 'published_at',
            'inverse': True,
        }
        form = PostSearchForm(initial=params)
    qs = Post.objects.select_related(
        'community'
    ).filter_ignoring_nonetype(
        community_id=params['community_id'],
        published_at__gte=params['date_min'],
        published_at__lte=params['date_max'],
        marked_as_ads=params['marked_as_ads'],
    ).annotate(
        post_likes_per_view=Case(
            When(
                ~Q(views=0),
                then=Cast('likes', FloatField()) / Cast('views', FloatField())
            ),
            output_field=FloatField()
        )
    )
    if params['has_links'] is True:
        qs = qs.exclude(links=0)
    elif params['has_links'] is False:
        qs = qs.filter(links=0)
    qs = qs.exclude_nulls(params['sort_by']).sort_by(params['sort_by'], params['inverse'])
    paginator = Paginator(qs[:POST_LIST_MAX], POST_PAGE_SIZE)
    page_num = req.GET.get('p', 1)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404()
    return render(req, 'communities/post_list.html', {'page': page, 'form': form})
