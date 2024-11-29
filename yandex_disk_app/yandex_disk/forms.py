from django import forms


class PublicLinkForm(forms.Form):
    public_link = forms.URLField(label='Публичная ссылка', max_length=500)
