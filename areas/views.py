import re

from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.utils.html import simple_email_re
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.views.generic import TemplateView
from rest_framework.decorators import detail_route, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.authtoken.models import Token

from areas.models import AreaBio, BioEntry
from areas.serializers import AreaBioSerializer, EntrySerializer


class AreaBioView(TemplateView):
    template_name = 'detail.pug'

    def get(self, request, pk, *args, **kwargs):

        bio = AreaBio.objects.get(id=pk)
        user = request.user
        # import ipdb; ipdb.set_trace()
        if user.is_anonymous:
            user = User.objects.get(username__exact='andy')
        context = {
            'token': Token.objects.get_or_create(user=user)[0].key,
            'bio': bio
        }

        return self.render_to_response(context)


class BioListView(ListView):
    queryset = AreaBio.objects.published()
    template_name = 'area_list.pug'


def add_bio(request):

    bio_uuid = request.session.get('bio_id')
    if not bio_uuid or True:
        bio = AreaBio()
        bio.save()
        request.session['bio_uuid'] = str(bio.uuid)
        bio_uuid = request.session.get('bio_uuid')

    bio = AreaBio.objects.get(uuid=bio_uuid)

    return redirect(reverse('edit-graph', args=[bio.id]))


class AreaBioViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = AreaBio.objects.all()
    serializer_class = AreaBioSerializer

    def get_queryset(self):
        queryset = AreaBio.objects.all()
        params = self.request.query_params
        if 'minAge' in params and 'maxAge' in params:
            maxAge = params['maxAge']
            if maxAge == 100:
                maxAge = 130
            queryset = queryset.filter(age__range=(params['minAge'], maxAge))
        return queryset

    @detail_route(methods=['get'])
    def compare(self, request, pk=None):
        range_param = int(request.query_params['range'])
        myself = self.get_object()
        range_tuple = (max(0, myself.age - range_param), myself.age + range_param)
        query = AreaBio.objects.filter(age__range=range_tuple).exclude(id=pk)
        return Response(AreaBioSerializer(query[:3], many=True).data)


class BioEntryViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = BioEntry.objects.all()
    serializer_class = EntrySerializer


def get_graph(request, pk, bare=False, original= False, list_display=False):
    template_name = 'partials/naked_graph.pug' if bare else 'partials/full_graph.pug'
    if list_display:
        template_name = 'partials/naked_graph_with_name.pug'
    context = {
        'graph': get_object_or_404(AreaBio.objects.all(), pk=pk),
        'original': original,
    }
    return render(request, template_name, context)


@csrf_exempt
def publish_graph(request, pk):

    if not request.method == 'POST':
        return HttpResponse(status=400)

    graph = get_object_or_404(AreaBio, pk=pk)
    graph.published = True
    graph.save()
    return HttpResponse()


@csrf_exempt
def send_graph(request, pk):

    if not request.method == 'POST':
        return HttpResponse(status=400)

    graph = get_object_or_404(AreaBio, pk=pk)

    # check email
    email = request.POST['email']
    if not simple_email_re.match(email):
        return HttpResponse(status=400)

    graph.send_to(email)
    return HttpResponse()

class PostedGraphView(View):
    template_name = 'done.pug'

    @staticmethod
    def post(request):
        context = {'graph': AreaBio.objects.get(uuid=request.POST['graph_uuid'])}
        return render(request, 'done.pug', context=context)
