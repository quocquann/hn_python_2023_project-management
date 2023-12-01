TASK_STATUS_CHOICES = (
    (0, "New"),
    (1, "In Progress"),
    (2, "Resolved"),
    (3, "Rejected"),
)

TASK_STATUS_DEFAULT = 0

PROJECT_STATUS_CHOICES = (
    (0, "Active"),
    (1, "Closed"),
)

ACTIVE = 0
CLOSED = 1

PROJECT_STATUS_DEFAULT = 0

ROLE_USERPROJECT_CHOICES = (
    (0, "Project Manager"),
    (1, "Stage Owner"),
    (2, "Member"),
)

ROLE_USERPROJECT_DEFAULT = 2

ROLE_USERSTAGE_CHOICES = (
    (0, "Stage Owner"),
    (1, "Member"),
)

ROLE_USERSTAGE_DEFAULT = 1
