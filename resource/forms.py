from django import forms

from .models import Resource, Comment


class ResourceForm(forms.ModelForm):

    class Meta:
        model = Resource

        fields = [
            "title",
            "description",
            "category",
            "file",
            "external_url",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g. Project Requirements.pdf",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 5,
                    "placeholder": "Write a short description...",
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-input",
                }
            ),

            "file": forms.ClearableFileInput(
                attrs={
                    "class": "file-input",
                }
            ),

            "external_url": forms.URLInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "https://example.com",
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        file = cleaned_data.get("file")
        external_url = cleaned_data.get("external_url")

        if not file and not external_url:

            if not self.instance.pk or not self.instance.file:

                raise forms.ValidationError(
                    "Please upload a file or provide an external URL."
                )

        return cleaned_data


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment

        fields = [
            "content",
        ]

        widgets = {

            "content": forms.Textarea(
                attrs={
                    "class": "comment-input",
                    "rows": 3,
                    "placeholder": "Write a comment...",
                }
            )
        }

        labels = {
            "content": "Comment",
        }