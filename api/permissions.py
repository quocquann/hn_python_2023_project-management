from rest_framework import permissions

from app.utils.helpers import is_pm


class IsPM(permissions.BasePermission):
    def has_permission(self, request, view):
        project = view.kwargs.get("project_id")
        return is_pm(request.user, project)
