from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, ButtonHolder, Submit
from django import forms

from areas.models import AreaBio, BioEntry


class AreaBioForm(forms.ModelForm):

    class Meta:
        model = AreaBio
        fields = ['name', 'age', 'country']

    def __init__(self, *args, **kwargs):
        super(AreaBioForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "area_bio"
        self.helper.layout = Layout(
            'name', 'age', 'country',
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button white')
            )
        )


class EntryForm(forms.ModelForm):

    class Meta:
        model = BioEntry
        fields = [
            'living_space',
            'number_of_people',
            'year_from',
            'year_to',
            'description',
        ]
