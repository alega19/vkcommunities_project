from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, render
from django.db.models import F
from django.contrib.auth.decorators import login_required

from .models import Community, CommunityHistory, Post
from .forms import CommunitySearchForm, PostSearchForm


COMMUNITY_PAGE_SIZE = 50
COMMUNITY_LIST_MAX = 10 * COMMUNITY_PAGE_SIZE

POST_PAGE_SIZE = 20
POST_LIST_MAX = 10 * POST_PAGE_SIZE


@require_GET
@login_required
def community_list(req):
    form = CommunitySearchForm(req.GET)
    if form.is_valid():
        params = form.cleaned_data
    else:
        params = {
            'verified': None,
            'ctype': None,
            'age_limit': None,
            'followers_min': None,
            'followers_max': None,
            'views_per_post_min': None,
            'views_per_post_max': None,
            'likes_per_view_min': None,
            'likes_per_view_max': None,
            'sort_by': 'followers',
            'inverse': True,
        }
        form = CommunitySearchForm(initial=params)
    qs = Community.available.filter_ignoring_nonetype(
        verified=params['verified'],
        ctype=params['ctype'],
        age_limit=params['age_limit'],
        followers__gte=params['followers_min'],
        followers__lte=params['followers_max'],
        views_per_post__gte=params['views_per_post_min'],
        views_per_post__lte=params['views_per_post_max'],
        likes_per_view__gte=params['likes_per_view_min'],
        likes_per_view__lte=params['likes_per_view_max'],
    ).exclude_nulls(
        params['sort_by']
    ).sort_by(params['sort_by'], params['inverse'])
    communities = qs[:COMMUNITY_LIST_MAX]
    paginator = Paginator(communities, COMMUNITY_PAGE_SIZE)
    page_num = req.GET.get('p', 1)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404()
    return render(req, 'communities/community_list.html', {'page': page, 'form': form})


@require_GET
@login_required
def community_detail(req, community_id):
    community_id = int(community_id)
    community = get_object_or_404(Community, pk=community_id)
    followers_history = list(CommunityHistory.objects.filter(
        community=community,
    ).values(
        x=F('checked_at'),
        y=F('followers'),
    ))
    return render(req, 'communities/community_detail.html', {
        'community': community,
        'followers_history': followers_history
    })


@require_GET
@login_required
def post_list(req):
    form = PostSearchForm(req.GET)
    if form.is_valid():
        params = form.cleaned_data
    else:
        params = {
            'community_id': None,
            'search': None,
            'marked_as_ads': None,
            'has_links': None,
            'date_min': None,
            'date_max': None,
            'views_min': None,
            'views_max': None,
            'likes_per_view_min': None,
            'likes_per_view_max': None,
            'sort_by': 'published_at',
            'inverse': True,
        }
        form = PostSearchForm(initial=params)
    qs = Post.objects.with_likes_per_view().select_related(
        'community'
    ).filter_ignoring_nonetype(
        community_id=params['community_id'],
        marked_as_ads=params['marked_as_ads'],
        published_at__gte=params['date_min'],
        published_at__lte=params['date_max'],
        views__gte=params['views_min'],
        views__lte=params['views_max'],
        post_likes_per_view__gte=params['likes_per_view_min'],
        post_likes_per_view__lte=params['likes_per_view_max'],
    ).search(params['search'])
    if params['has_links'] is True:
        qs = qs.exclude(links=0)
    elif params['has_links'] is False:
        qs = qs.filter(links=0)
    qs = qs.exclude_nulls(params['sort_by']).sort_by(params['sort_by'], params['inverse'])
    posts = list(qs[:POST_LIST_MAX])
    paginator = Paginator(posts, POST_PAGE_SIZE)
    page_num = req.GET.get('p', 1)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        raise Http404()
    return render(req, 'communities/post_list.html', {'page': page, 'form': form})
