from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import (
    FileResponse,
    Http404,
    JsonResponse,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    ResourceForm,
)

from .models import (
    Bookmark,
    Comment,
    Resource,
)


def resource_list(request):

    category = request.GET.get(
        'category',
        'all'
    )

    search = request.GET.get(
        'q',
        ''
    ).strip()

    resources = Resource.objects.select_related(
        'uploaded_by'
    )

    # Category filter
    if category != 'all':

        resources = resources.filter(
            category=category
        )

    # Search
    if search:

        resources = resources.filter(

            Q(title__icontains=search)

            | Q(description__icontains=search)

            | Q(category__icontains=search)

            | Q(
                uploaded_by__username__icontains=search
            )
        )

    # My resources
    if (
        request.GET.get('mine') == '1'
        and request.user.is_authenticated
    ):

        resources = resources.filter(
            uploaded_by=request.user
        )

    # Bookmarks
    if (
        request.GET.get('bookmarks') == '1'
        and request.user.is_authenticated
    ):

        resources = resources.filter(
            bookmarks__user=request.user
        )

    # Recently added
    if request.GET.get('recent') == '1':

        resources = resources.order_by(
            '-created_at'
        )

    # Pagination
    paginator = Paginator(
        resources.distinct(),
        8
    )

    page_obj = paginator.get_page(
        request.GET.get('page')
    )

    # Bookmark IDs
    current_ids = [
        resource.id
        for resource in page_obj.object_list
    ]

    bookmarked_ids = set()

    if request.user.is_authenticated:

        bookmarked_ids = set(

            Bookmark.objects.filter(

                user=request.user,

                resource_id__in=current_ids

            ).values_list(
                'resource_id',
                flat=True
            )
        )

    # Categories
    categories = []

    for key, label in Resource.CATEGORY_CHOICES:

        categories.append({

            'key': key,

            'label': label,

            'count': Resource.objects.filter(
                category=key
            ).count()

        })

    context = {

        'resources':
            page_obj.object_list,

        'page_obj':
            page_obj,

        'categories':
            categories,

        'popular':
            Resource.objects.order_by(
                '-views',
                '-updated_at'
            )[:5],

        'recent':
            Resource.objects.order_by(
                '-created_at'
            )[:3],

        'selected_category':
            category,

        'search_query':
            search,

        'total_resources':
            Resource.objects.count(),

        'bookmarked_ids':
            bookmarked_ids,
    }

    return render(
        request,
        'resource_list.html',
        context
    )


def resource_detail(request, pk):

    resource = get_object_or_404(
        Resource.objects.select_related(
            'uploaded_by'
        ),
        pk=pk
    )

    # Increase view count
    Resource.objects.filter(
        pk=pk
    ).update(
        views=F('views') + 1
    )

    resource.refresh_from_db()

    is_bookmarked = False

    if request.user.is_authenticated:

        is_bookmarked = Bookmark.objects.filter(

            user=request.user,

            resource=resource

        ).exists()

    comment_form = None

    if request.user.is_authenticated:

        comment_form = CommentForm()

    context = {

        'resource':
            resource,

        'is_bookmarked':
            is_bookmarked,

        'comment_form':
            comment_form,

        'comments_count':
            resource.comments.count(),
    }

    return render(
        request,
        'resource_detail.html',
        context
    )

@login_required
def resource_create(request):

    if request.method == "POST":

        form = ResourceForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            resource = form.save(
                commit=False
            )

            resource.uploaded_by = request.user

            resource.save()

            messages.success(
                request,
                "Resource added successfully."
            )

            return redirect(
                "resource:detail",
                pk=resource.pk
            )

        else:
            print("FORM ERRORS:", form.errors)

    else:

        form = ResourceForm()

    return render(
        request,
        "resource_form.html",
        {
            "form": form,
            "page_title": "Add Resource",
            "submit_text": "Add Resource",
        }
    )
    
@login_required
def resource_edit(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    if (
        resource.uploaded_by_id != request.user.id
        and not request.user.is_staff
    ):

        messages.error(
            request,
            "You cannot edit this resource."
        )

        return redirect(
            "resource:list"
        )

    if request.method == "POST":

        form = ResourceForm(
            request.POST,
            request.FILES,
            instance=resource
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Resource updated successfully."
            )

            return redirect(
                "resource:detail",
                pk=resource.pk
            )

    else:

        form = ResourceForm(
            instance=resource
        )

    return render(
        request,
        "resource_form.html",
        {
            "form": form,
            "resource": resource,
            "page_title": "Edit Resource",
            "submit_text": "Save Changes",
        }
    )

@login_required
@require_POST
def resource_delete(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    if (
        resource.uploaded_by_id
        != request.user.id
        and not request.user.is_staff
    ):

        return JsonResponse({

            'ok':
                False,

            'message':
                'Permission denied.'

        }, status=403)

    resource.delete()

    return JsonResponse({
        'ok': True
    })


def resource_download(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # External URL
    if not resource.file:

        if resource.external_url:

            return redirect(
                resource.external_url
            )

        raise Http404(
            'No file or URL found.'
        )

    Resource.objects.filter(
        pk=pk
    ).update(
        downloads=F('downloads') + 1
    )

    return FileResponse(

        resource.file.open('rb'),

        as_attachment=True,

        filename=resource.file.name.split(
            '/'
        )[-1]
    )


@login_required
@require_POST
def toggle_bookmark(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    bookmark, created = (
        Bookmark.objects.get_or_create(

            user=request.user,

            resource=resource
        )
    )

    if not created:

        bookmark.delete()

    return JsonResponse({

        'ok':
            True,

        'bookmarked':
            created,

        'message':
            (
                'Added to bookmarks.'
                if created
                else
                'Removed from bookmarks.'
            )
    })


def resource_comments(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    comments = (
        resource.comments
        .select_related('user')
        .all()
    )

    comment_form = None

    if request.user.is_authenticated:

        comment_form = CommentForm()

    return render(

        request,

        'resource_comments.html',

        {
            'resource':
                resource,

            'comments':
                comments,

            'comment_form':
                comment_form,
        }
    )

@login_required
@require_POST
def add_comment(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    form = CommentForm(
        request.POST
    )

    if form.is_valid():

        comment = form.save(
            commit=False
        )

        comment.resource = resource

        comment.user = request.user

        comment.save()

        # AJAX response
        if request.headers.get(
            'X-Requested-With'
        ) == 'XMLHttpRequest':

            username = (
                request.user.get_full_name()
                or request.user.username
            )

            return JsonResponse({

                'ok': True,

                'comment': {

                    'id': comment.id,

                    'user': username,

                    # IMPORTANT: text नहीं, content
                    'content': comment.content,

                    'created_at': comment.created_at.strftime(
                        '%b %d, %Y %I:%M %p'
                    ),

                    'initial': username[0].upper(),

                }

            })

        # IMPORTANT: resources नहीं, resource
        return redirect(
            'resource:detail',
            pk=resource.pk
        )

    return JsonResponse({

        'ok': False,

        'errors': form.errors,

    }, status=400)

@login_required
@require_POST
def delete_comment(request, pk):

    comment = get_object_or_404(
        Comment,
        pk=pk
    )

    if (
        comment.user_id
        != request.user.id
        and not request.user.is_staff
    ):

        return JsonResponse({

            'ok':
                False,

            'message':
                'Permission denied.'

        }, status=403)

    comment.delete()

    return JsonResponse({
        'ok': True
    })