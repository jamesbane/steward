from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static


class TypedProviderGroupForm(forms.Form):
    PROVIDER_TYPE_CHOICE_ENTERPRISE = 'Enterprise'
    PROVIDER_TYPE_CHOICE_SERVICE_PROVIDER = 'Service Provider'
    PROVIDER_TYPE_CHOICES = (
        ('', '----'),
        (PROVIDER_TYPE_CHOICE_ENTERPRISE, PROVIDER_TYPE_CHOICE_ENTERPRISE),
        (PROVIDER_TYPE_CHOICE_SERVICE_PROVIDER, PROVIDER_TYPE_CHOICE_SERVICE_PROVIDER),
    )
    provider_type = forms.ChoiceField(label='Provider Type', choices=PROVIDER_TYPE_CHOICES, required=True)
    provider_id = forms.CharField(label='Provider Id', max_length=256, required=True)
    group_id = forms.CharField(label='Group Id', max_length=256, required=False)

    javascript = static('tools/provider_group_form.js')

    def clean(self):
        cleaned_data = super(TypedProviderGroupForm, self).clean()
        provider_type = cleaned_data.get("provider_type")
        provider_id = cleaned_data.get("provider_id")
        group_id = cleaned_data.get("group_id")

        if provider_type == self.PROVIDER_TYPE_CHOICE_ENTERPRISE:
            if not provider_id:
                raise forms.ValidationError("Provider Id is required")
        elif provider_type == self.PROVIDER_TYPE_CHOICE_SERVICE_PROVIDER:
            if not provider_id and group_id:
                raise forms.ValidationError("Provider Id and Group Id is required")
        else:
            raise forms.ValidationError("Invalid provider type")


class ProviderGroupForm(forms.Form):
    provider_id = forms.CharField(label='Provider Id', max_length=256, required=True)
    group_id = forms.CharField(label='Group Id', max_length=256, required=False)

class EmptyForm(forms.Form):
    pass
