import re

from django.template.defaultfilters import capfirst


def guess_name(email):
    name = re.sub('@.*', '', email)
    name = re.sub('\..*', '', name)
    name = capfirst(name)
    return name
