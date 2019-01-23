from directory_components.fields import DirectoryComponentsFieldMixin

from django import forms


class DateField(DirectoryComponentsFieldMixin, forms.DateField):
    pass
