from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product

# --- 1. PRODUCT FORM (For Admin Dashboard) ---
class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        # Make the description a larger text box (5 rows tall)
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        
        for field in self.fields:
            # Default style for normal inputs (Name, Price, etc.) -> Pill Shape
            css_class = 'form-control rounded-pill px-3 py-2 bg-light border-0 mb-2'
            
            # Special style for Description -> Rectangle Box with rounded corners
            if field == 'description':
                css_class = 'form-control rounded-4 px-3 py-3 bg-light border-0 mb-2'
            
            self.fields[field].widget.attrs.update({'class': css_class})


# --- 2. USER REGISTRATION FORM (For Sign Up Page) ---
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify # Helps clean the username
from .models import Product

# ... (Keep ProductForm as is) ...

from django.utils.text import slugify

class CreateUserForm(UserCreationForm):
    # 1. Single "Full Name" field
    full_name = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={
        'placeholder': 'Full Name',
        'class': 'form-control rounded-pill px-3 py-2 bg-light border-0 mb-2'
    }))

    class Meta:
        model = User
        # 2. We ONLY ask for Name and Email (Username is hidden/auto-generated)
        fields = ['full_name', 'email']

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control rounded-pill px-3 py-2 bg-light border-0 mb-2',
            'placeholder': 'Email Address'
        })

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit=False)
        
        name_input = self.cleaned_data['full_name']
        user.first_name = name_input  # Store "John Doe" in first_name for display

        # 3. Auto-Generate Unique Username
        # "John Doe" -> "johndoe"
        base_username = slugify(name_input).replace("-", "")
        if not base_username:
             base_username = "user"

        username = base_username
        counter = 1
        
        # If "johndoe" exists, try "johndoe1", "johndoe2"...
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        user.username = username

        if commit:
            user.save()
        return user