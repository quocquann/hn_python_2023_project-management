from django.test import TestCase

from app.models import Stage, Project
from app.utils import constants


class StageModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        project = Project.objects.create(
            name="Project 1",
            describe="Describe",
            start_date="2021-01-01",
            end_date="2021-01-02",
            status=0,
        )

        Stage.objects.create(
            name="Stage 1",
            start_date="2021-01-01",
            end_date="2021-01-02",
            project=project,
        )

    def test_name_label(self):
        stage = Stage.objects.get(id=1)
        field_label = stage._meta.get_field("name").verbose_name
        self.assertEqual(field_label, "Name")

    def test_name_max_length(self):
        stage = Stage.objects.get(id=1)
        max_length = stage._meta.get_field("name").max_length
        self.assertEqual(max_length, 50)

    def test_start_date_label(self):
        stage = Stage.objects.get(id=1)
        field_label = stage._meta.get_field("start_date").verbose_name
        self.assertEqual(field_label, "Start date")

    def test_start_date_type(self):
        stage = Stage.objects.get(id=1)
        field_type = stage._meta.get_field("start_date").get_internal_type()
        self.assertEqual(field_type, "DateField")

    def test_end_date_label(self):
        stage = Stage.objects.get(id=1)
        field_label = stage._meta.get_field("end_date").verbose_name
        self.assertEqual(field_label, "End date")

    def test_end_date_type(self):
        stage = Stage.objects.get(id=1)
        field_type = stage._meta.get_field("end_date").get_internal_type()
        self.assertEqual(field_type, "DateField")

    def test_status_label(self):
        stage = Stage.objects.get(id=1)
        field_label = stage._meta.get_field("status").verbose_name
        self.assertEqual(field_label, "Status")

    def test_status_default(self):
        stage = Stage.objects.get(id=1)
        default = stage._meta.get_field("status").default
        self.assertEqual(default, 0)

    def test_status_choices(self):
        stage = Stage.objects.get(id=1)
        choices = stage._meta.get_field("status").choices
        self.assertEqual(choices, ((0, "Active"), (1, "Closed"), (2, "Slowed")))

    def test_project_label(self):
        stage = Stage.objects.get(id=1)
        field_label = stage._meta.get_field("project").verbose_name
        self.assertEqual(field_label, "Project")

    def test_stage_has_project(self):
        stage = Stage.objects.get(id=1)
        project = Project.objects.get(id=1)
        self.assertEqual(stage.project, project)

    def test_deleted_at_label(self):
        stage = Stage.objects.get(id=1)
        field_label = stage._meta.get_field("deleted_at").verbose_name
        self.assertEqual(field_label, "Deleted at")

    def test_deleted_at_null(self):
        stage = Stage.objects.get(id=1)
        null = stage._meta.get_field("deleted_at").null
        self.assertEqual(null, True)


class ProjectModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Project.objects.create(
            name="First Project",
            end_date="2024-02-11",
            status=constants.ACTIVE,
        )

    def test_name_label(self):
        project = Project.objects.get(id=1)
        field_label = project._meta.get_field("name").verbose_name
        self.assertEqual(field_label, "Project name")

    def test_name_max_length(self):
        project = Project.objects.get(pk=1)
        max_length = project._meta.get_field("name").max_length
        self.assertEqual(max_length, 50)

    def test_describe_label(self):
        project = Project.objects.get(pk=1)
        field_label = project._meta.get_field("describe").verbose_name
        self.assertEqual(field_label, "Describe")

    def test_describe_max_length(self):
        project = Project.objects.get(pk=1)
        max_length = project._meta.get_field("describe").max_length
        self.assertEqual(max_length, 500)

    def test_start_date_label(self):
        project = Project.objects.get(pk=1)
        field_label = project._meta.get_field("start_date").verbose_name
        self.assertEqual(field_label, "Start date")

    def test_start_date_auto_now_add(self):
        project = Project.objects.get(pk=1)
        auto_now_add = project._meta.get_field("start_date").auto_now_add
        self.assertEqual(auto_now_add, True)

    def test_end_date_label(self):
        project = Project.objects.get(pk=1)
        field_label = project._meta.get_field("end_date").verbose_name
        self.assertEqual(field_label, "End date")

    def test_status_label(self):
        project = Project.objects.get(pk=1)
        field_label = project._meta.get_field("status").verbose_name
        self.assertEqual(field_label, "Status")

    def test_status_choices(self):
        project = Project.objects.get(pk=1)
        field_choices = project._meta.get_field("status").choices
        self.assertEqual(field_choices, constants.PROJECT_STATUS_CHOICES)

    def test_status_default(self):
        project = Project.objects.get(pk=1)
        default = project._meta.get_field("status").default
        self.assertEqual(default, constants.PROJECT_STATUS_DEFAULT)

    def test_deleted_at_label(self):
        project = Project.objects.get(pk=1)
        field_label = project._meta.get_field("deleted_at").verbose_name
        self.assertEqual(field_label, "Deleted at")

    def test_user_label(self):
        project = Project.objects.get(pk=1)
        field_label = project._meta.get_field("user").verbose_name
        self.assertEqual(field_label, "User")

    def test_deleted_at_null_true(self):
        project = Project.objects.get(pk=1)
        null = project._meta.get_field("deleted_at").null
        self.assertEqual(null, True)

    def test_deleted_at_blank_true(self):
        project = Project.objects.get(pk=1)
        blank = project._meta.get_field("deleted_at").blank
        self.assertEqual(blank, True)
