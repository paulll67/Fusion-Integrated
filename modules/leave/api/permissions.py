"""Permission helpers for the Leave API."""

from rest_framework.permissions import BasePermission


class _ScopedCollection(BasePermission):
    codes: tuple[str, ...] = ()
    message = "You do not have permission to view this leave collection."

    def has_permission(self, request, view):
        principal = getattr(request, "principal", None)
        if principal is None:
            return False
        return principal.has_any_permission(*self.codes)


def ScopedCollection(*codes: str):  # noqa: N802
    return type(
        "ScopedCollection_" + "_".join(codes).replace(".", "_"),
        (_ScopedCollection,),
        {"codes": codes},
    )
