from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "mx-input",
                "placeholder": "vous@entreprise.tg",
                "autofocus": True,
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "class": "mx-input",
                "placeholder": "Mot de passe",
                "autocomplete": "current-password",
            }
        ),
    )


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"class": "mx-input", "placeholder": "Votre nom"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "mx-input", "placeholder": "Email"}),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "mx-input", "rows": 5, "placeholder": "Votre message"}
        ),
    )


class EvidenceTextForm(forms.Form):
    text = forms.CharField(
        min_length=8,
        max_length=4000,
        label="SMS ou texte de preuve",
        widget=forms.Textarea(
            attrs={
                "class": "mx-input",
                "rows": 6,
                "placeholder": "Collez le SMS opérateur (Moov Money, T-Money, Flooz…)",
            }
        ),
    )


class AssistantForm(forms.Form):
    question = forms.CharField(
        min_length=3,
        max_length=500,
        widget=forms.TextInput(
            attrs={
                "class": "mx-input",
                "placeholder": "Quelle est ma trésorerie consolidée ?",
            }
        ),
    )
