from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic import TemplateView
from rest_framework.viewsets import ModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.authtoken.models import Token

from areas.models import AreaBio, BioEntry
from areas.serializers import AreaBioSerializer, EntrySerializer


class AreaBioView(TemplateView):
    template_name = 'detail.pug'

    def get(self, request, *args, **kwags):

        user = request.user
        # import ipdb; ipdb.set_trace()
        if user.is_anonymous:
            user = User.objects.get(username__exact='andy')
        context = {
            'token': Token.objects.get_or_create(user=user)[0].key
        }
        print(context)

        return self.render_to_response(context)


class BioListView(ListView):
    queryset = AreaBio.objects.all()
    context_object_name = 'book_list'
    template_name = 'area_list.pug'


def add_bio(request):

    bio_uuid = request.session.get('bio_id')
    if not bio_uuid or True:
        bio = AreaBio()
        bio.save()
        request.session['bio_uuid'] = str(bio.uuid)
        bio_uuid = request.session.get('bio_uuid')

    bio = AreaBio.objects.get(uuid=bio_uuid)

    return redirect(reverse('detail', args=[bio.id]))


class AreaBioViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = AreaBio.objects.all()
    serializer_class = AreaBioSerializer


class BioEntryViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = BioEntry.objects.all()
    serializer_class = EntrySerializer


