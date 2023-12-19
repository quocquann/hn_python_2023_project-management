from django.contrib import admin
from .models import Project, Stage, Task, UserProject, UserStage

# Register your models here.

admin.site.register(Stage)
admin.site.register(Task)
admin.site.register(UserProject)
admin.site.register(UserStage)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "name",
        "describe",
        "start_date",
        "end_date",
        "status",
        "deleted_at",
    )
