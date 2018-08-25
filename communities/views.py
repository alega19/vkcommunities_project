from django.db.models import F
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Community, Post
from .forms import CommunitySearchForm, PostSearchForm


class CommunityListView(LoginRequiredMixin, ListView):
    template_name = 'communities/community_list.html'
    paginate_by = 50
    limit = 400
    page_kwarg = 'p'

    def get_queryset(self):
        self.form = CommunitySearchForm(self.request.GET)
        if self.form.is_valid():
            params = self.form.cleaned_data
        else:
            params = {'sort_by': 'followers', 'inverse': True}
            self.form = CommunitySearchForm(initial=params)
        qs = Community.available.filter_ignoring_nonetype(
            verified=params.get('verified'),
            ctype=params.get('ctype'),
            age_limit=params.get('age_limit'),
            followers__gte=params.get('followers_min'),
            followers__lte=params.get('followers_max'),
            views_per_post__gte=params.get('views_per_post_min'),
            views_per_post__lte=params.get('views_per_post_max'),
            likes_per_view__gte=params.get('likes_per_view_min'),
            likes_per_view__lte=params.get('likes_per_view_max'),
        ).exclude_nulls(
            params['sort_by']
        ).sort_by(params['sort_by'], params['inverse'])
        return list(qs[:self.limit])

    def get_context_data(self, **kwargs):
        return super().get_context_data(form=self.form)


class CommunityDetailView(LoginRequiredMixin, DetailView):
    model = Community

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['followers_history'] = list(self.object.communityhistory_set.order_by(
            'checked_at'
        ).values(
            x=F('checked_at'),
            y=F('followers'),
        ))
        return ctx


class PostListView(LoginRequiredMixin, ListView):
    template_name = 'communities/post_list.html'
    paginate_by = 20
    limit = 160
    page_kwarg = 'p'

    def get_queryset(self):
        self.form = PostSearchForm(self.request.GET)
        if self.form.is_valid():
            params = self.form.cleaned_data
        else:
            params = {'sort_by': 'published_at', 'inverse': True}
            self.form = PostSearchForm(initial=params)
        qs = Post.objects.with_likes_per_view().select_related(
            'community'
        ).filter_ignoring_nonetype(
            community_id=params.get('community_id'),
            marked_as_ads=params.get('marked_as_ads'),
            published_at__gte=params.get('date_min'),
            published_at__lte=params.get('date_max'),
            views__gte=params.get('views_min'),
            views__lte=params.get('views_max'),
            post_likes_per_view__gte=params.get('likes_per_view_min'),
            post_likes_per_view__lte=params.get('likes_per_view_max'),
        ).search(params.get('search'))
        if 'has_links' in params:
            qs = qs.exclude(links=0) if params['has_links'] else qs.filter(links=0)
        qs = qs.exclude_nulls(
            params['sort_by']
        ).sort_by(params['sort_by'], params['inverse'])
        return list(qs[:self.limit])

    def get_context_data(self, **kwargs):
        return super().get_context_data(form=self.form)
