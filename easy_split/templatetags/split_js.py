from django import template
from django.template.loader import render_to_string

register = template.Library()

def split_js(values):
    js_string = render_to_string("split_js.html", {} )
    return js_string

register.filter(split_js)