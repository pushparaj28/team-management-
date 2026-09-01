from django.urls import path

from . import views


app_name = "resource"


urlpatterns = [


    # Resource List
    path( "", views.resource_list,name="list"),

    # Add Resource
    path( "add/", views.resource_create, name="create"),

    # Resource Detail
    path("<int:pk>/",views.resource_detail,name="detail"),

    # Edit Resource
    path("<int:pk>/edit/",views.resource_edit,name="edit"),

    # Delete Resource
    path( "<int:pk>/delete/", views.resource_delete, name="delete" ),

    # Download Resource
    path( "<int:pk>/download/", views.resource_download,name="download"),

    # Bookmark
    path("<int:pk>/bookmark/", views.toggle_bookmark,  name="bookmark"),

    # Comments
    path( "<int:pk>/comments/", views.resource_comments, name="comments"),

    # Add Comment
    path("<int:pk>/comments/add/", views.add_comment, name="add_comment" ),

    # Delete Comment
    path( "comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),
]