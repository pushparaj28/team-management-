from django.urls import path

from . import views


app_name = "resource"


urlpatterns = [

    # ========================================================
    # RESOURCE
    # ========================================================

    path(
        "",
        views.resource_list,
        name="list"
    ),

    path(
        "add/",
        views.resource_create,
        name="create"
    ),

    path(
        "<int:pk>/",
        views.resource_detail,
        name="detail"
    ),

    path(
        "<int:pk>/edit/",
        views.resource_edit,
        name="edit"
    ),

    path(
        "<int:pk>/delete/",
        views.resource_delete,
        name="delete"
    ),

    path(
        "<int:pk>/download/",
        views.resource_download,
        name="download"
    ),

    # ========================================================
    # BOOKMARK
    # ========================================================

    path(
        "<int:pk>/bookmark/",
        views.toggle_bookmark,
        name="bookmark"
    ),

    # ========================================================
    # COMMENTS
    # ========================================================

    path(
        "<int:pk>/comments/",
        views.resource_comments,
        name="comments"
    ),

    path(
        "<int:pk>/comments/add/",
        views.add_comment,
        name="add_comment"
    ),

    path(
        "comment/<int:pk>/delete/",
        views.delete_comment,
        name="delete_comment"
    ),

    # ========================================================
    # TEMPORARY RESOURCE ACCESS
    # ========================================================

    # Admin / Manager -> Employee ko access dena
    path(
        "access/grant/",
        views.grant_resource_access,
        name="grant_access"
    ),

    # Admin / Manager -> Access revoke
    path(
        "access/<int:access_id>/revoke/",
        views.revoke_resource_access,
        name="revoke_access"
    ),

    # Admin / Manager -> Access list
    path("access/list/", views.resource_access_list, name="access_list"),
    
    # report
    
     path("", views.resource_list, name="list"),

    path("create/", views.resource_create, name="create"),

    # REPORT
    path("reports/", views.work_report, name="reports"),

    path("<int:pk>/", views.resource_detail, name="detail"),

    path("<int:pk>/edit/", views.resource_edit, name="edit"),

    path("<int:pk>/delete/", views.resource_delete, name="delete"),
]