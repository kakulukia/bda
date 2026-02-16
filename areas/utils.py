import re

from django.template.defaultfilters import capfirst


def guess_name(email):
    name = re.sub(r'@.*', '', email)
    name = re.sub(r'\..*', '', name)
    name = capfirst(name)
    return name
