import requests

from django.urls import reverse


def create_response(status_code=200, json_body={}, content=None):
    response = requests.Response()
    response.status_code = status_code
    response.json = lambda: json_body
    response._content = content
    return response


def submit_step_factory(client, url_name, view_name, view_class):
    step_names = iter([name for name, form in view_class.form_list])

    def submit_step(data, step_name=None):
        step_name = step_name or next(step_names)
        return client.post(
            reverse(url_name, kwargs={'step': step_name}),
            {
                view_name + '-current_step': step_name,
                **{step_name + '-' + key: value for key, value in data.items()}
            },
        )
    return submit_step
