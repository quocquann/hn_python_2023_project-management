from .utils.constants import ACTIVE, PROJECT_MANAGER, MEMBER


def constants(request):
    return {
        "ACTIVE": ACTIVE,
        "PM": PROJECT_MANAGER,
        "MEMBER": MEMBER,
    }
