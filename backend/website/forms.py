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


class InvoiceCreateForm(forms.Form):
    client_name = forms.CharField(
        max_length=200,
        label="Client",
        widget=forms.TextInput(attrs={"class": "mx-input", "placeholder": "Nom du client", "autocomplete": "organization"}),
    )
    client_phone = forms.CharField(
        required=False,
        max_length=20,
        label="Téléphone",
        widget=forms.TextInput(attrs={"class": "mx-input", "placeholder": "+228 …", "autocomplete": "tel"}),
    )
    amount = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=1,
        label="Montant (FCFA)",
        widget=forms.NumberInput(attrs={"class": "mx-input", "min": "1", "step": "1"}),
    )
    issue_date = forms.DateField(
        label="Date d'émission",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"class": "mx-input", "type": "date"}),
    )
    due_date = forms.DateField(
        label="Échéance",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"class": "mx-input", "type": "date"}),
    )
