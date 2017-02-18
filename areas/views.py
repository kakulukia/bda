from django.views.generic import DetailView, ListView

from areas.models import AreaBio


class AreaBioView(DetailView):
    model = AreaBio
    template_name = 'graph.pug'
    context_object_name = 'bio'

    def get_context_data(self, **kwargs):
        context = super(AreaBioView, self).get_context_data(**kwargs)
        return context


class BioListView(ListView):
    queryset = AreaBio.data.published()
    context_object_name = 'book_list'
    template_name = 'area_list.pug'
