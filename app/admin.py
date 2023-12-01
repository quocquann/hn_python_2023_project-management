from django.contrib import admin
from .models import Project, Stage, Task, UserProject, UserStage, UserTask

# Register your models here.

admin.site.register(Project)
admin.site.register(Stage)
admin.site.register(Task)
admin.site.register(UserProject)
admin.site.register(UserStage)
admin.site.register(UserTask)
