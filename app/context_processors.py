from .utils.constants import ACTIVE, PROJECT_MANAGER, MEMBER, STAGE_OWNER


def constants(request):
    return {
        "ACTIVE": ACTIVE,
        "PM": PROJECT_MANAGER,
        "MEMBER": MEMBER,
        "STAGE_OWNER": STAGE_OWNER,
    }
