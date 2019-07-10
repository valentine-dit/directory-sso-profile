from django.forms import TextInput


class PostcodeInput(TextInput):
    template_name = 'enrolment/widgets/postcode.html'
