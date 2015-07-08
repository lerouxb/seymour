from django import forms
from django.conf import settings
from django.template import Library, Node, TemplateSyntaxError, resolve_variable
from django.template.loader import get_template
from django.template import Context 


register = Library()

def do_formfield(parser, token):
    """
    {% formfield fieldwrapper %}
    """
    args = token.contents.split()
    if len(args) != 2:
        raise TemplateSyntaxError, u"'formfield' requires 'field' (got %r)" % args
    
    return FormfieldNode(args[1])

class FormfieldNode(Node):
    def __init__(self, field):        
        self.field = field        
    
    def render(self, context):
        field = resolve_variable(self.field, context)
                                    
        if isinstance(field.field, forms.BooleanField):
            field.is_checkbox = True
        else:
            field.is_checkbox = False
        
        template = get_template('field.html')
        return template.render(Context({
            'field': field 
        }))

register.tag('formfield', do_formfield)
