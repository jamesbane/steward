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
            if not provider_id or not group_id:
                raise forms.ValidationError("Provider Id and Group Id is required")
        else:
            raise forms.ValidationError("Invalid provider type")
        return cleaned_data


class CallParkPickupForm(TypedProviderGroupForm):
    park = forms.BooleanField(label="Call Park", required=False, initial=True)
    retrieve = forms.BooleanField(label="Call Retrieve", required=False, initial=True)

    def clean(self):
        cleaned_data = super(CallParkPickupForm, self).clean()
        cleaned_data['park'] = str(cleaned_data.get("park", False))
        cleaned_data['retrieve'] = str(cleaned_data.get("retrieve", False))
        return cleaned_data

class ProviderGroupForm(forms.Form):
    provider_id = forms.CharField(label='Provider Id', max_length=256, required=True)
    group_id = forms.CharField(label='Group Id', max_length=256, required=False)


class SystemProviderGroupForm(forms.Form):
    ACTION_TYPE_CHOICE_SYSTEM = 'System'
    ACTION_TYPE_CHOICE_PROVIDER = 'Provider/Group'
    ACTION_TYPE_CHOICES = (
        ('', '----'),
        (ACTION_TYPE_CHOICE_SYSTEM, ACTION_TYPE_CHOICE_SYSTEM),
        (ACTION_TYPE_CHOICE_PROVIDER, ACTION_TYPE_CHOICE_PROVIDER),
    )
    action_type = forms.ChoiceField(label='Type', choices=ACTION_TYPE_CHOICES, required=True)
    provider_id = forms.CharField(label='Provider Id', max_length=256, required=False)
    group_id = forms.CharField(label='Group Id', max_length=256, required=False)

    javascript = static('tools/system_provider_group_form.js')


class TagReportForm(SystemProviderGroupForm):
    tag_names = forms.CharField(label='Tag Names', max_length=256, required=True)


class TagRemovalForm(TypedProviderGroupForm):
    tag_names = forms.CharField(label='Tag Names', max_length=256, required=True)


class TrunkUserAuditForm(forms.Form):
    fixup = forms.BooleanField(label="Fixup", required=False, initial=False)

    def clean(self):
        cleaned_data = super(TrunkUserAuditForm, self).clean()
        cleaned_data['fixup'] = str(cleaned_data.get("fixup", False))
        return cleaned_data


class EmptyForm(forms.Form):
    pass
