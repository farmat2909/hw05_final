from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Страница об авторе."""
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Странице о технологиях."""
    template_name = 'about/tech.html'
