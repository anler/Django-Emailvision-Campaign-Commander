from django.db import models
from django import forms

class StringListField(models.Field):
    """
    Save a list of strings in a CharField (or TextField) column.

    In the django model object the column is a list of strings.
    http://www.djangosnippets.org/snippets/1491/
    """
    __metaclass__=models.SubfieldBase

    SPLIT_CHAR=u'\v'

    def __init__(self, *args, **kwargs):
        self.internal_type=kwargs.pop('internal_type', 'CharField') # or TextField
        super(StringListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return value.split(self.SPLIT_CHAR)

    def get_internal_type(self):
        return self.internal_type

    def get_db_prep_lookup(self, lookup_type, value):
        # SQL WHERE
        raise NotImplementedError()

    def get_prep_value(self, value):
        return self.SPLIT_CHAR.join(value)

    def formfield(self, **kwargs):
        assert not kwargs, kwargs
        return forms.MultipleChoiceField(choices=self.choices)
