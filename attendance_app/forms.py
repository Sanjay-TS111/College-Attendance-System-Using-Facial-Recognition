from django import forms
from .models import Timetable

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['subject_name', 'day_of_week', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(format='%I:%M%p'),
            'end_time': forms.TimeInput(format='%I:%M%p'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        time_formats = [
            '%I:%M%p',     
            '%I:%M %p',     
            '%H:%M:%S',     
            '%H:%M',        
        ]
        self.fields['start_time'].input_formats = time_formats
        self.fields['end_time'].input_formats = time_formats

    def clean_start_time(self):
        start_time = self.cleaned_data['start_time']
        return start_time

    def clean_end_time(self):
        end_time = self.cleaned_data['end_time']
        return end_time