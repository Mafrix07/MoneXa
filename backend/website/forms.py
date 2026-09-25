from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control py-3",
                "placeholder": "gerant@monexa.tg",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-control py-3", "placeholder": "Mot de passe"}
        ),
    )


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control py-3", "placeholder": "Votre nom"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control py-3", "placeholder": "Email"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control py-3", "rows": 5, "placeholder": "Votre message"}
        ),
    )


class AssistantForm(forms.Form):
    question = forms.CharField(
        min_length=3,
        max_length=500,
        widget=forms.TextInput(
            attrs={
                "class": "form-control py-3",
                "placeholder": "Ex. Combien ai-je en T-Money ?",
            }
        ),
    )
