from rest_framework import permissions

from .models import TenantMembership


class TenantRBACPermission(permissions.BasePermission):
    role_write_allow = {TenantMembership.Role.ADMIN, TenantMembership.Role.OPERATOR}

    def _membership_for_request(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return None
        return TenantMembership.objects.filter(tenant_id=tenant_id, user=request.user).first()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return request.user.is_superuser
        membership = self._membership_for_request(request)
        if not membership:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return membership.role in self.role_write_allow

    def has_object_permission(self, request, view, obj):
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return request.user.is_superuser

        object_tenant_id = getattr(obj, "tenant_id", None)
        if str(object_tenant_id) != str(tenant_id):
            return False

        membership = self._membership_for_request(request)
        if not membership:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return membership.role in self.role_write_allow
