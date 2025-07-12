from django import forms
from django.core.validators import FileExtensionValidator
from .models import Text


class TextForm(forms.ModelForm):
    """Form for creating and editing texts"""
    
    tags = forms.CharField(
        required=False,
        help_text="Separate tags with commas (e.g., military, speech, historical)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'military, speech, historical'
        })
    )
    
    class Meta:
        model = Text
        fields = ['title', 'content', 'description', 'tags', 'difficulty', 'time_limit', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a descriptive title for your text'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Enter the text content you want to memorize...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this text (optional)'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional time limit in minutes',
                'min': 1
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['description'].required = False
        self.fields['time_limit'].required = False
        
        # If editing existing text, populate tags field
        if self.instance.pk and self.instance.tags:
            self.fields['tags'].initial = self.instance.tags
    
    def clean_content(self):
        """Validate content length and format"""
        content = self.cleaned_data.get('content')
        if content:
            content = content.strip()
            if len(content) < 10:
                raise forms.ValidationError("Text content must be at least 10 characters long.")
            
            word_count = len(content.split())
            if word_count < 5:
                raise forms.ValidationError("Text must contain at least 5 words.")
            elif word_count > 10000:
                raise forms.ValidationError("Text is too long. Maximum 10,000 words allowed.")
        
        return content
    
    def clean_tags(self):
        """Clean and validate tags"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Clean up tags: strip whitespace, convert to lowercase, remove duplicates
            tag_list = [tag.strip().lower() for tag in tags.split(',') if tag.strip()]
            tag_list = list(dict.fromkeys(tag_list))  # Remove duplicates while preserving order
            
            if len(tag_list) > 10:
                raise forms.ValidationError("Maximum 10 tags allowed.")
            
            # Validate individual tags
            for tag in tag_list:
                if len(tag) < 2:
                    raise forms.ValidationError(f"Tag '{tag}' is too short. Minimum 2 characters.")
                if len(tag) > 30:
                    raise forms.ValidationError(f"Tag '{tag}' is too long. Maximum 30 characters.")
                if not tag.replace('-', '').replace('_', '').isalnum():
                    raise forms.ValidationError(f"Tag '{tag}' contains invalid characters. Use only letters, numbers, hyphens, and underscores.")
            
            return ', '.join(tag_list)
        
        return ''


class TextFileUploadForm(forms.Form):
    """Form for uploading text files"""
    
    file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['txt'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.txt'
        }),
        help_text="Upload a .txt file containing the text you want to memorize"
    )
    
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank to use filename as title'
        }),
        help_text="Optional: Override the default title (filename)"
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Brief description of this text (optional)'
        })
    )
    
    difficulty = forms.ChoiceField(
        choices=Text.DIFFICULTY_CHOICES,
        initial='beginner',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'military, speech, historical'
        }),
        help_text="Separate tags with commas"
    )
    
    time_limit = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional time limit in minutes'
        })
    )
    
    is_public = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Make this text available to other users"
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")
            
            # Try to read and validate content
            try:
                content = file.read().decode('utf-8')
                file.seek(0)  # Reset file pointer
                
                if len(content.strip()) < 10:
                    raise forms.ValidationError("File content is too short. Minimum 10 characters required.")
                
                word_count = len(content.split())
                if word_count < 5:
                    raise forms.ValidationError("File must contain at least 5 words.")
                elif word_count > 10000:
                    raise forms.ValidationError("File is too long. Maximum 10,000 words allowed.")
                    
            except UnicodeDecodeError:
                raise forms.ValidationError("File must be a valid UTF-8 text file.")
        
        return file


class TextSearchForm(forms.Form):
    """Form for searching and filtering texts"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search titles, descriptions, or tags...'
        })
    )
    
    difficulty = forms.ChoiceField(
        required=False,
        choices=[('', 'All Difficulties')] + Text.DIFFICULTY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    tag = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by tag'
        })
    )
    
    my_texts_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Show only my texts"
    )