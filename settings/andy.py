from pathlib import Path

from django.dispatch import receiver
from django.utils.autoreload import autoreload_started, file_changed

from .common import *  # noqa

from django_browser_reload import views as browser_reload_views

# DEBUG = False
DEBUG = True

if 'django_browser_reload.middleware.BrowserReloadMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.append('django_browser_reload.middleware.BrowserReloadMiddleware')

# django-browser-reload watches the full static root by default. That includes
# django-compressor output under assets/CACHE, which would otherwise trigger
# endless reloads whenever compressed assets are generated.
autoreload_started.disconnect(dispatch_uid='browser_reload')
file_changed.disconnect(dispatch_uid='browser_reload')


@receiver(autoreload_started, dispatch_uid='browser_reload')
def watch_browser_reload_sources(sender, **kwargs):
    for directory in browser_reload_views.django_template_directories():
        sender.watch_dir(directory, '**/*')

    for directory in browser_reload_views.jinja_template_directories():
        sender.watch_dir(directory, '**/*')

    assets_root = Path(STATICFILES_DIRS[0])
    for child in assets_root.iterdir():
        if child.name == 'CACHE' or not child.is_dir():
            continue
        sender.watch_dir(child, '**/*')


@receiver(file_changed, dispatch_uid='browser_reload')
def trigger_browser_reload(*, file_path, **kwargs):
    if 'assets/CACHE' in str(file_path):
        return True

    file_parents = file_path.parents

    for template_dir in browser_reload_views.django_template_directories():
        if template_dir in file_parents:
            browser_reload_views.trigger_reload_soon()
            return True

    for template_dir in browser_reload_views.jinja_template_directories():
        if template_dir in file_parents:
            browser_reload_views.trigger_reload_soon()
            return True

    assets_root = Path(STATICFILES_DIRS[0])
    for directory in assets_root.iterdir():
        if directory.name == 'CACHE' or not directory.is_dir():
            continue
        if directory in file_parents:
            browser_reload_views.trigger_reload_soon()
            return True

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
