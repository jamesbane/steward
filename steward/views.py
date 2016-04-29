from django.core.urlresolvers import reverse
from django.views.generic.base import RedirectView
from django.core.exceptions import ObjectDoesNotExist

from steward.models import GroupDefaultView


class IndexRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        view_name = 'dashboard:empty'
        view_priority = 0
        for group in user.groups.all():
            try:
                group_view = GroupDefaultView.objects.get(group=group)
                if group_view.priority > view_priority:
                    view_name = group_view.view_name
                    view_priority = group_view.priority
            except ObjectDoesNotExist:
                pass
        return reverse(view_name)
