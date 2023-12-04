from django import forms
from django.contrib.auth.models import User
from .models import Task,Stage

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['content', 'start_date', 'end_date', 'status', 'stage', 'user']
        widgets = {
            'user': forms.CheckboxSelectMultiple,
            'stage': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['stage'].queryset = Stage.objects.all()
        self.fields['user'].queryset = User.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        stage = cleaned_data.get('stage')

        if start_date and end_date and stage:
            if start_date < stage.start_date:
                self.add_error('start_date', 'Start date must be greater than or equal to the start date of the stage.')

            if end_date > stage.end_date:
                self.add_error('end_date', 'End date must be less than or equal to the end date of the stage.')

        return cleaned_data

