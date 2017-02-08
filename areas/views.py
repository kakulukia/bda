from django.views.generic import DetailView

from areas.models import AreaBio


class AreaBioView(DetailView):
    model = AreaBio
    template_name = 'area_bio.html'
    context_object_name = 'bio'

    def get_context_data(self, **kwargs):
        context = super(AreaBioView, self).get_context_data(**kwargs)
        return context
