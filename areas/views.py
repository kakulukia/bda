from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic import TemplateView
from rest_framework.viewsets import ReadOnlyModelViewSet

from areas.models import AreaBio
from areas.serializers import AreaBioSerializer
from areas.svg import render_area_bio_svg


class AreaBioView(TemplateView):
    template_name = 'partials/full_graph.pug'

    def get(self, request, uuid, *args, **kwargs):

        graph = AreaBio.objects.get(uuid=uuid)
        graph._stretched = False
        graph.show_descriptions = True
        context = {
            'graph': graph
        }
        return self.render_to_response(context)


class AreaBioSiteView(TemplateView):
    template_name = 'view.pug'

    def get(self, request, uuid, *args, **kwargs):

        graph = AreaBio.objects.get(uuid=uuid)
        graph._stretched = False
        graph.show_descriptions = True
        context = {
            'graph': graph
        }
        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class BioListView(ListView):
    template_name = 'area_list.pug'

    def get_queryset(self):
        queryset = list(AreaBio.objects.complete()[:77])
        for bio in queryset:
            bio._stretched = True
            bio.bare = True
        return queryset

    def get_context_data(self, **kwargs):
        context = super(BioListView, self).get_context_data()

        cities = cache.get('cities')
        if not cities:
            unordered = AreaBio.objects.complete().order_by('country').values_list(
                'country', flat=True)
            from collections import Counter
            cities = [item for item, count in Counter(unordered).most_common()]
            if None in cities:
                cities.remove(None)
            cache.set('cities', cities, 60*60)

        context['cities'] = cities
        return context


class AreaBioViewSet(ReadOnlyModelViewSet):
    queryset = AreaBio.objects.all()
    serializer_class = AreaBioSerializer

    def get_queryset(self):
        queryset = AreaBio.objects.all()
        params = self.request.query_params
        if 'minAge' in params and 'maxAge' in params:
            queryset = AreaBio.objects.complete()
            maxAge = params['maxAge']
            if maxAge == 100:
                maxAge = 130
            queryset = queryset.filter(age__range=(params['minAge'], maxAge))

        if 'country' in params and params['country']:
            queryset = queryset.filter(country=params['country'])

        return queryset


def get_graph(request, pk, bare=False, original=False, list_display=False, stretched=True):
    template_name = 'partials/naked_graph.pug' if bare else 'partials/full_graph.pug'
    if list_display:
        template_name = 'partials/naked_graph_with_name.pug'
    bio = get_object_or_404(AreaBio.objects.all(), pk=pk)
    bio._stretched = stretched
    bio.bare = True if list_display else bare
    context = {
        'graph': bio,
        'original': original,
    }
    return render(request, template_name, context)


def export_graph_svg(request, uuid):
    graph = get_object_or_404(AreaBio.objects.all(), uuid=uuid)
    filename_slug = slugify(str(graph)) or 'wohnbiografie'
    filename = f'wohnbiografie-{filename_slug}-{graph.uuid}.svg'
    response = HttpResponse(
        render_area_bio_svg(graph),
        content_type='image/svg+xml; charset=utf-8',
    )
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
