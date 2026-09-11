from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
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
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    ResourceForm,
)

from .models import (
    Bookmark,
    Comment,
    Resource,
    ResourceAccess,
)


User = get_user_model()


# ============================================================
# PERMISSION HELPERS
# ============================================================


def is_admin_or_manager(user):
    """
    Admin / Manager ko permanent resource access.

    Ye multiple role systems support karta hai:
    1. Superuser
    2. Staff
    3. Django Groups: Admin / Manager
    4. Custom User role field
    """

    if not user.is_authenticated:
        return False

    # Django Superuser
    if user.is_superuser:
        return True

    # Django Staff
    if user.is_staff:
        return True

    # Django Groups
    group_names = set(
        user.groups.values_list(
            "name",
            flat=True
        )
    )

    normalized_groups = {
        str(name).strip().lower()
        for name in group_names
    }

    if normalized_groups.intersection({
        "admin",
        "administrator",
        "manager"
    }):
        return True

    # Custom User model role field
    role = getattr(
        user,
        "role",
        None
    )

    if role:

        role = str(role).strip().lower()

        if role in {
            "admin",
            "administrator",
            "manager"
        }:
            return True

    return False


def has_resource_access(
    user,
    resource_type
):
    """
    Check whether user can access
    Documents / Technical resources.
    """

    if not user.is_authenticated:
        return False

    # Admin / Manager = permanent access
    if is_admin_or_manager(user):
        return True

    # Employee = temporary access
    now = timezone.now()

    return ResourceAccess.objects.filter(
        user=user,
        resource_type=resource_type,
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).exists()


def can_access_resource(
    user,
    resource
):
    """
    General resource access checker.

    Documents + Technical:
        Admin / Manager OR temporary permission

    Other categories:
        Logged-in users can access.
    """

    if not user.is_authenticated:
        return False

    if resource.category in {
        "documents",
        "technical"
    }:

        return has_resource_access(
            user,
            resource.category
        )

    return True


# ============================================================
# RESOURCE LIST
# ============================================================


@login_required
def resource_list(request):

    category = request.GET.get(
        "category",
        "all"
    )

    search = request.GET.get(
        "q",
        ""
    ).strip()

    resources = Resource.objects.select_related(
        "uploaded_by"
    )

    # --------------------------------------------------------
    # ACCESS CONTROL
    # --------------------------------------------------------

    if not is_admin_or_manager(request.user):

        now = timezone.now()

        # Employee ke active temporary permissions
        temporary_categories = set(
            ResourceAccess.objects.filter(
                user=request.user,
                is_active=True,
                start_time__lte=now,
                end_time__gte=now,
            ).values_list(
                "resource_type",
                flat=True
            )
        )

        # Default:
        # Documents + Technical hidden

        allowed_query = ~Q(
            category__in=[
                "documents",
                "technical"
            ]
        )

        # Temporary Documents permission
        if "documents" in temporary_categories:

            allowed_query |= Q(
                category="documents"
            )

        # Temporary Technical permission
        if "technical" in temporary_categories:

            allowed_query |= Q(
                category="technical"
            )

        resources = resources.filter(
            allowed_query
        )

    # --------------------------------------------------------
    # CATEGORY FILTER
    # --------------------------------------------------------

    if category != "all":

        resources = resources.filter(
            category=category
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        resources = resources.filter(

            Q(title__icontains=search)

            | Q(
                description__icontains=search
            )

            | Q(
                category__icontains=search
            )

            | Q(
                uploaded_by__username__icontains=search
            )
        )

    # --------------------------------------------------------
    # MY RESOURCES
    # --------------------------------------------------------

    if (
        request.GET.get("mine") == "1"
        and request.user.is_authenticated
    ):

        resources = resources.filter(
            uploaded_by=request.user
        )

    # --------------------------------------------------------
    # BOOKMARKS
    # --------------------------------------------------------

    if (
        request.GET.get("bookmarks") == "1"
        and request.user.is_authenticated
    ):

        resources = resources.filter(
            bookmarks__user=request.user
        )

    # --------------------------------------------------------
    # RECENT
    # --------------------------------------------------------

    if request.GET.get("recent") == "1":

        resources = resources.order_by(
            "-created_at"
        )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    paginator = Paginator(
        resources.distinct(),
        8
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    # --------------------------------------------------------
    # BOOKMARK IDS
    # --------------------------------------------------------

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
                "resource_id",
                flat=True
            )
        )

    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    categories = []

    for key, label in Resource.CATEGORY_CHOICES:

        categories.append({

            "key": key,

            "label": label,

            "count": Resource.objects.filter(
                category=key
            ).count()

        })

    # --------------------------------------------------------
    # TEMPORARY ACCESS INFO
    # --------------------------------------------------------

    active_access = ResourceAccess.objects.filter(
        user=request.user,
        is_active=True,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    )

    context = {

        "resources":
            page_obj.object_list,

        "page_obj":
            page_obj,

        "categories":
            categories,

        "popular":
            Resource.objects.order_by(
                "-views",
                "-updated_at"
            )[:5],

        "recent":
            Resource.objects.order_by(
                "-created_at"
            )[:3],

        "selected_category":
            category,

        "search_query":
            search,

        "total_resources":
            Resource.objects.count(),

        "bookmarked_ids":
            bookmarked_ids,

        "is_admin_or_manager":
            is_admin_or_manager(request.user),

        "active_access":
            active_access,
    }

    return render(
        request,
        "resource_list.html",
        context
    )


# ============================================================
# RESOURCE DETAIL
# ============================================================


@login_required
def resource_detail(request, pk):

    resource = get_object_or_404(

        Resource.objects.select_related(
            "uploaded_by"
        ),

        pk=pk
    )

    # --------------------------------------------------------
    # ACCESS CHECK
    # --------------------------------------------------------

    if not can_access_resource(
        request.user,
        resource
    ):

        messages.error(
            request,
            "You don't have permission to access this resource."
        )

        return redirect(
            "resource:list"
        )

    # --------------------------------------------------------
    # INCREASE VIEW COUNT
    # --------------------------------------------------------

    Resource.objects.filter(
        pk=pk
    ).update(
        views=F("views") + 1
    )

    resource.refresh_from_db()

    # --------------------------------------------------------
    # BOOKMARK
    # --------------------------------------------------------

    is_bookmarked = Bookmark.objects.filter(

        user=request.user,

        resource=resource

    ).exists()

    # --------------------------------------------------------
    # COMMENT
    # --------------------------------------------------------

    comment_form = CommentForm()

    context = {

        "resource":
            resource,

        "is_bookmarked":
            is_bookmarked,

        "comment_form":
            comment_form,

        "comments_count":
            resource.comments.count(),

        "is_admin_or_manager":
            is_admin_or_manager(request.user),

        "has_access":
            can_access_resource(
                request.user,
                resource
            ),
    }

    return render(
        request,
        "resource_detail.html",
        context
    )


# ============================================================
# CREATE RESOURCE
# ============================================================


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

            # Documents / Technical
            # only Admin / Manager

            if resource.category in {
                "documents",
                "technical"
            }:

                if not is_admin_or_manager(
                    request.user
                ):

                    messages.error(
                        request,
                        (
                            "Only Admin or Manager can "
                            "create Documents or Technical resources."
                        )
                    )

                    return redirect(
                        "resource:list"
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

            print(
                "FORM ERRORS:",
                form.errors
            )

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


# ============================================================
# EDIT RESOURCE
# ============================================================


@login_required
def resource_edit(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # Documents / Technical
    # only Admin / Manager

    if resource.category in {
        "documents",
        "technical"
    }:

        if not is_admin_or_manager(
            request.user
        ):

            messages.error(
                request,
                (
                    "Only Admin or Manager can "
                    "edit this resource."
                )
            )

            return redirect(
                "resource:list"
            )

    # Other categories
    # Owner or Admin/Manager

    elif (
        resource.uploaded_by_id
        != request.user.id

        and not is_admin_or_manager(
            request.user
        )
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

            updated_resource = form.save(
                commit=False
            )

            # If category changed to
            # Documents / Technical
            # check permission again

            if updated_resource.category in {
                "documents",
                "technical"
            }:

                if not is_admin_or_manager(
                    request.user
                ):

                    messages.error(
                        request,
                        (
                            "Only Admin or Manager can "
                            "set Documents or Technical category."
                        )
                    )

                    return redirect(
                        "resource:list"
                    )

            updated_resource.save()

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


# ============================================================
# DELETE RESOURCE
# ============================================================


@login_required
@require_POST
def resource_delete(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # Documents / Technical
    # only Admin / Manager

    if resource.category in {
        "documents",
        "technical"
    }:

        if not is_admin_or_manager(
            request.user
        ):

            return JsonResponse({

                "ok":
                    False,

                "message":
                    "Only Admin or Manager can delete this resource."

            }, status=403)

    # Other resources
    elif (
        resource.uploaded_by_id
        != request.user.id

        and not is_admin_or_manager(
            request.user
        )
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Permission denied."

        }, status=403)

    resource.delete()

    return JsonResponse({
        "ok": True
    })


# ============================================================
# DOWNLOAD RESOURCE
# ============================================================


@login_required
def resource_download(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # --------------------------------------------------------
    # ACCESS CHECK
    # --------------------------------------------------------

    if not can_access_resource(
        request.user,
        resource
    ):

        messages.error(
            request,
            "You don't have permission to download this resource."
        )

        return redirect(
            "resource:list"
        )

    # --------------------------------------------------------
    # EXTERNAL URL
    # --------------------------------------------------------

    if not resource.file:

        if resource.external_url:

            return redirect(
                resource.external_url
            )

        raise Http404(
            "No file or URL found."
        )

    # --------------------------------------------------------
    # DOWNLOAD COUNT
    # --------------------------------------------------------

    Resource.objects.filter(
        pk=pk
    ).update(
        downloads=F("downloads") + 1
    )

    return FileResponse(

        resource.file.open("rb"),

        as_attachment=True,

        filename=resource.file.name.split(
            "/"
        )[-1]
    )


# ============================================================
# BOOKMARK
# ============================================================


@login_required
@require_POST
def toggle_bookmark(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # Restricted resource access
    if not can_access_resource(
        request.user,
        resource
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "You don't have permission."

        }, status=403)

    bookmark, created = (
        Bookmark.objects.get_or_create(

            user=request.user,

            resource=resource
        )
    )

    if not created:

        bookmark.delete()

    return JsonResponse({

        "ok":
            True,

        "bookmarked":
            created,

        "message":
            (
                "Added to bookmarks."
                if created
                else
                "Removed from bookmarks."
            )
    })


# ============================================================
# RESOURCE COMMENTS
# ============================================================


@login_required
def resource_comments(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # Access check
    if not can_access_resource(
        request.user,
        resource
    ):

        messages.error(
            request,
            "You don't have permission to access this resource."
        )

        return redirect(
            "resource:list"
        )

    comments = (
        resource.comments
        .select_related("user")
        .all()
    )

    comment_form = CommentForm()

    return render(

        request,

        "resource_comments.html",

        {
            "resource":
                resource,

            "comments":
                comments,

            "comment_form":
                comment_form,
        }
    )


# ============================================================
# ADD COMMENT
# ============================================================


@login_required
@require_POST
def add_comment(request, pk):

    resource = get_object_or_404(
        Resource,
        pk=pk
    )

    # Access check
    if not can_access_resource(
        request.user,
        resource
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "You don't have permission."

        }, status=403)

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
            "X-Requested-With"
        ) == "XMLHttpRequest":

            username = (
                request.user.get_full_name()
                or request.user.username
            )

            return JsonResponse({

                "ok":
                    True,

                "comment": {

                    "id":
                        comment.id,

                    "user":
                        username,

                    "content":
                        comment.content,

                    "created_at":
                        comment.created_at.strftime(
                            "%b %d, %Y %I:%M %p"
                        ),

                    "initial":
                        username[0].upper(),

                }

            })

        return redirect(
            "resource:detail",
            pk=resource.pk
        )

    return JsonResponse({

        "ok":
            False,

        "errors":
            form.errors,

    }, status=400)


# ============================================================
# DELETE COMMENT
# ============================================================


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

        and not is_admin_or_manager(
            request.user
        )
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Permission denied."

        }, status=403)

    comment.delete()

    return JsonResponse({
        "ok": True
    })


# ============================================================
# GRANT TEMPORARY ACCESS
# ============================================================


@login_required
@require_POST
def grant_resource_access(request):

    # Only Admin / Manager
    if not is_admin_or_manager(
        request.user
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Only Admin or Manager can grant access."

        }, status=403)

    user_id = request.POST.get(
        "user_id"
    )

    resource_type = request.POST.get(
        "resource_type"
    )

    hours = request.POST.get(
        "hours"
    )

    # --------------------------------------------------------
    # VALIDATE USER
    # --------------------------------------------------------

    if not user_id:

        return JsonResponse({

            "ok":
                False,

            "message":
                "Employee is required."

        }, status=400)

    employee = get_object_or_404(
        User,
        pk=user_id
    )

    # Admin/Manager ko employee permission
    # ke through manage karne ki zarurat nahi
    if is_admin_or_manager(
        employee
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Temporary access is only for employees."

        }, status=400)

    # --------------------------------------------------------
    # VALIDATE RESOURCE TYPE
    # --------------------------------------------------------

    if resource_type not in {
        "documents",
        "technical"
    }:

        return JsonResponse({

            "ok":
                False,

            "message":
                "Invalid resource type."

        }, status=400)

    # --------------------------------------------------------
    # VALIDATE HOURS
    # --------------------------------------------------------

    try:

        hours = float(hours)

        if hours <= 0:
            raise ValueError

    except (
        TypeError,
        ValueError
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Invalid access duration."

        }, status=400)

    # Optional maximum
    # Security ke liye 30 days se zyada nahi

    if hours > 24 * 30:

        return JsonResponse({

            "ok":
                False,

            "message":
                "Maximum access duration is 30 days."

        }, status=400)

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    start_time = timezone.now()

    end_time = (
        start_time
        + timedelta(
            hours=hours
        )
    )

    # --------------------------------------------------------
    # DEACTIVATE OLD ACTIVE ACCESS
    # --------------------------------------------------------

    ResourceAccess.objects.filter(

        user=employee,

        resource_type=resource_type,

        is_active=True,

        end_time__gte=start_time

    ).update(

        is_active=False

    )

    # --------------------------------------------------------
    # CREATE NEW ACCESS
    # --------------------------------------------------------

    access = ResourceAccess.objects.create(

        user=employee,

        resource_type=resource_type,

        granted_by=request.user,

        start_time=start_time,

        end_time=end_time,

        is_active=True

    )

    return JsonResponse({

        "ok":
            True,

        "message":
            (
                f"{employee} has been granted "
                f"{resource_type} access."
            ),

        "access_id":
            access.id,

        "employee":
            str(employee),

        "resource_type":
            resource_type,

        "start_time":
            start_time.strftime(
                "%d %b %Y %I:%M %p"
            ),

        "end_time":
            end_time.strftime(
                "%d %b %Y %I:%M %p"
            ),

        "duration_hours":
            hours

    })


# ============================================================
# REVOKE TEMPORARY ACCESS
# ============================================================


@login_required
@require_POST
def revoke_resource_access(
    request,
    access_id
):

    # Only Admin / Manager
    if not is_admin_or_manager(
        request.user
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Only Admin or Manager can revoke access."

        }, status=403)

    access = get_object_or_404(
        ResourceAccess,
        pk=access_id
    )

    access.is_active = False

    access.save(
        update_fields=[
            "is_active"
        ]
    )

    return JsonResponse({

        "ok":
            True,

        "message":
            "Access revoked successfully."

    })


# ============================================================
# ACTIVE ACCESS LIST
# ============================================================


@login_required
def resource_access_list(request):

    if not is_admin_or_manager(
        request.user
    ):

        return JsonResponse({

            "ok":
                False,

            "message":
                "Permission denied."

        }, status=403)

    accesses = (
        ResourceAccess.objects
        .select_related(
            "user",
            "granted_by"
        )
        .all()
    )

    now = timezone.now()

    data = []

    for access in accesses:

        data.append({

            "id":
                access.id,

            "user_id":
                access.user.id,

            "user":
                (
                    access.user.get_full_name()
                    or access.user.username
                ),

            "resource_type":
                access.resource_type,

            "resource_type_label":
                access.get_resource_type_display(),

            "granted_by":
                (
                    access.granted_by.get_full_name()
                    if access.granted_by
                    else "Unknown"
                ),

            "start_time":
                access.start_time.strftime(
                    "%d %b %Y %I:%M %p"
                ),

            "end_time":
                access.end_time.strftime(
                    "%d %b %Y %I:%M %p"
                ),

            "is_active":
                access.is_active,

            "is_valid":
                (
                    access.is_active
                    and access.start_time <= now
                    and access.end_time >= now
                ),

        })

    return JsonResponse({

        "ok":
            True,

        "accesses":
            data

    })
    
    
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from tasks.models import Task


def work_report(request):

    # =====================================
    # CURRENT DATE
    # =====================================

    today = timezone.now().date()

    # URL se filter type
    period = request.GET.get("period", "today")


    # =====================================
    # SELECT PERIOD
    # =====================================

    if period == "weekly":

        start_date = today - timedelta(days=today.weekday())
        end_date = today


    elif period == "monthly":

        start_date = today.replace(day=1)
        end_date = today


    elif period == "yearly":

        start_date = today.replace(month=1, day=1)
        end_date = today


    else:

        period = "today"

        start_date = today
        end_date = today


    # =====================================
    # TASKS FOR SELECTED PERIOD
    # =====================================

    tasks = Task.objects.filter(
        created_at__date__range=[
            start_date,
            end_date
        ]
    )


    # =====================================
    # TOTAL TASKS
    # =====================================

    total_tasks = tasks.count()


    # =====================================
    # COMPLETED TASKS
    # =====================================

    completed_tasks = tasks.filter(
        status="completed"
    ).count()


    # =====================================
    # PENDING TASKS
    # =====================================

    pending_tasks = tasks.exclude(
        status="completed"
    ).count()


    # =====================================
    # OVERDUE TASKS
    # =====================================

    overdue_tasks = Task.objects.filter(
        due_date__lt=today
    ).exclude(
        status="completed"
    ).count()


    # =====================================
    # PERFORMANCE %
    # =====================================

    if total_tasks > 0:

        performance = round(
            (completed_tasks / total_tasks) * 100,
            2
        )

    else:

        performance = 0


    # =====================================
    # EMPLOYEE PERFORMANCE
    # =====================================

    employees = User.objects.filter(
        is_active=True
    )


    employee_reports = []


    for employee in employees:


        employee_tasks = tasks.filter(
            assigned_to=employee
        )


        total = employee_tasks.count()


        completed = employee_tasks.filter(
            status="completed"
        ).count()


        pending = employee_tasks.exclude(
            status="completed"
        ).count()


        if total > 0:

            employee_performance = round(
                (completed / total) * 100,
                2
            )

        else:

            employee_performance = 0


        employee_reports.append({

            "employee": employee,

            "total_tasks": total,

            "completed_tasks": completed,

            "pending_tasks": pending,

            "performance": employee_performance,

        })


    # =====================================
    # EMPLOYEE OF THE MONTH
    # =====================================

    month_start = today.replace(
        day=1
    )


    month_tasks = Task.objects.filter(
        created_at__date__gte=month_start,
        created_at__date__lte=today
    )


    monthly_employee_reports = []


    for employee in employees:


        employee_tasks = month_tasks.filter(
            assigned_to=employee
        )


        total = employee_tasks.count()


        completed = employee_tasks.filter(
            status="completed"
        ).count()


        if total > 0:

            emp_performance = round(
                (completed / total) * 100,
                2
            )

        else:

            emp_performance = 0


        monthly_employee_reports.append({

            "employee": employee,

            "completed_tasks": completed,

            "performance": emp_performance

        })


    employee_of_month = None


    if monthly_employee_reports:

        employee_of_month = max(

            monthly_employee_reports,

            key=lambda x: (
                x["completed_tasks"],
                x["performance"]
            )

        )


    # =====================================
    # CONTEXT
    # =====================================

    context = {

        "period": period,

        "total_tasks": total_tasks,

        "completed_tasks": completed_tasks,

        "pending_tasks": pending_tasks,

        "overdue_tasks": overdue_tasks,

        "performance": performance,

        "employee_reports": employee_reports,

        "employee_of_month": employee_of_month,

    }


    return render(
        request,
        "work_report.html",
        context
    )