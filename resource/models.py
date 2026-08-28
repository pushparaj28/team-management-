from django.conf import settings
from django.db import models
from django.urls import reverse


class Resource(models.Model):

    CATEGORY_CHOICES = [
        ("documents", "Documents"),
        ("technical", "Technical"),
        ("design", "Design"),
        ("links", "Links"),
        ("media", "Media"),
        ("others", "Others"),
    ]

    title = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES
    )

    file = models.FileField(
        upload_to="resources/%Y/%m/",
        blank=True,
        null=True
    )

    external_url = models.URLField(
        blank=True
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources_uploaded"
    )

    views = models.PositiveIntegerField(
        default=0
    )

    downloads = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "resource:detail",
            args=[self.pk]
        )

    @property
    def category_label(self):
        return dict(
            self.CATEGORY_CHOICES
        ).get(
            self.category,
            self.category.title()
        )

    @property
    def extension(self):

        if self.file:
            name = self.file.name.lower()

            if "." in name:
                return name.rsplit(".", 1)[-1]

        if self.external_url:
            return "link"

        return "file"

    @property
    def icon_type(self):

        ext = self.extension

        if ext == "pdf":
            return "pdf"

        if ext in {
            "sql",
            "py",
            "js",
            "json",
            "html",
            "css",
            "zip",
        }:
            return "technical"

        if ext in {
            "png",
            "jpg",
            "jpeg",
            "webp",
            "svg",
            "fig",
        }:
            return "design"

        if ext in {
            "xlsx",
            "xls",
            "csv",
            "doc",
            "docx",
        }:
            return "document"

        if ext in {
            "mp4",
            "mov",
            "avi",
            "webm",
            "mp3",
            "wav",
        }:
            return "media"

        if self.external_url:
            return "link"

        return "file"


class Bookmark(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "resource"],
                name="unique_user_resource_bookmark"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.resource}"


class Comment(models.Model):

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resource_comments"
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.resource.title}"