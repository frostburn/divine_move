from django import template

register = template.Library()

@register.filter(name='add_class')
def addclass(value, arg):
    return value.as_widget(attrs={'class': arg})
