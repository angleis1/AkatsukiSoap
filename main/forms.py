import re
import io
from datetime import timedelta
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from froala_editor.widgets import FroalaEditor
from PIL import Image
from django.utils import timezone
from .models import User, ProfileUser, MasterClass, MasterRequest, Review, SignUpClass, MasterClassDateTime, QuizQuestion, QuizOption


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    fio = forms.CharField(
        max_length=255,
        label='ФИО',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Только кириллица, пробелы и дефисы.',
        validators=[
            RegexValidator(
                regex=r'^[а-яА-ЯёЁ\s-]+$',
                message='ФИО может содержать только кириллические буквы, пробелы и дефисы.'
            )
        ]
    )
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (___) ___-__-__',
            'id': 'phone-input',
            'autocomplete': 'off',
            'autocomplete': 'new-password'
        }),
        help_text='Введите номер телефона.'
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # username: только латиница и цифры, макс. 20
        self.fields['username'].max_length = 20
        self.fields['username'].help_text = 'Только латинские буквы и цифры, до 20 символов.'
        self.fields['username'].validators = [
            RegexValidator(
                regex=r'^[a-zA-Z0-9]+$',
                message='Логин должен содержать только латинские буквы и цифры.'
            ),
            MaxLengthValidator(20)
        ]

        # Пароль: мин. 8 символов, без пробелов, латиница+цифры+символы
        self.fields['password1'].validators = [
            MinLengthValidator(8, message='Пароль должен содержать минимум 8 символов.'),
            RegexValidator(
                regex=r'^\S+$',
                message='Пароль не может содержать пробелы.'
            ),
            RegexValidator(
                regex=r'^[a-zA-Z0-9!@#$%^&*()_+=\-[\]{};:\'"\\|,.<>/?`~]+$',
                message='Пароль может содержать только латинские буквы, цифры и символы (без пробелов).'
            )
        ]
        self.fields['password1'].help_text = 'Минимум 8 символов, без пробелов, латиница, цифры, спецсимволы.'
        self.fields['password2'].validators = self.fields['password1'].validators
        self.fields['password2'].help_text = 'Повторите пароль.'

        # Общие стили
        for field_name, field in self.fields.items():
            if field_name != 'captcha':
                field.widget.attrs.update({'class': 'form-control'})

    def clean_phone(self):
        phone_raw = self.cleaned_data['phone']
        digits = re.sub(r'\D', '', phone_raw)
        if len(digits) == 10:
            return f"+7({digits[:3]})-{digits[3:6]}-{digits[6:8]}-{digits[8:]}"
        elif len(digits) == 11 and digits.startswith('7'):
            return f"+7({digits[1:4]})-{digits[4:7]}-{digits[7:9]}-{digits[9:]}"
        else:
            raise forms.ValidationError("Введите 10 цифр (код +7 добавится автоматически).")

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email


class LoginFormWithCaptcha(AuthenticationForm):
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox,
        error_messages={"required": "Пожалуйста, подтвердите, что вы не робот."}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class MasterClassCreateForm(forms.ModelForm):
    description = forms.CharField(widget=FroalaEditor)
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        required=True,
        label='Изображение мастер-класса (будет автоматически обрезано до 16:9)'
    )
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox,
        error_messages={"required": "Пожалуйста, подтвердите, что вы не робот."}
    )

    class Meta:
        model = MasterClass
        fields = ['name', 'category', 'description', 'duration_minutes',
                  'format', 'method_payment', 'price', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field not in [self.fields['captcha'], self.fields['description'], self.fields['image']]:
                field.widget.attrs.update({'class': 'form-control'})
        for field_name in ['category', 'format', 'method_payment']:
            self.fields[field_name].widget.attrs['class'] = 'form-select'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise forms.ValidationError("Необходимо загрузить изображение.")
        if not image.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            raise forms.ValidationError("Неподдерживаемый формат. Разрешены: PNG, JPG, JPEG, GIF, WEBP.")
        try:
            img = Image.open(io.BytesIO(image.read()))
            image.seek(0)
        except Exception as e:
            raise forms.ValidationError(f"Не удалось прочитать изображение. Возможно, файл повреждён. Ошибка: {e}")
        return image


class MasterClassDateTimeForm(forms.ModelForm):
    class Meta:
        model = MasterClassDateTime
        fields = ['date_event', 'time_event', 'count']
        widgets = {
            'date_event': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time_event': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_date_event(self):
        date = self.cleaned_data['date_event']
        max_date = timezone.now().date() + timedelta(weeks=3)
        if date > max_date:
            raise forms.ValidationError(f"Дата не может быть позже чем через 3 недели (макс. {max_date})")
        return date


class ProfileUserForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ProfileUser
        fields = ['fio', 'phone', 'avatar', 'bio', 'email']  # добавили email
        widgets = {
            'fio': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),  # без чекбокса
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email__iexact=email)
        if self.user and self.user.pk:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            user = profile.user
            user.email = self.cleaned_data['email']
            user.save()
        return profile


class MasterRequestForm(forms.ModelForm):
    class Meta:
        model = MasterRequest
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Почему вы хотите стать мастером?'
            }),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Ваш отзыв'}),
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-select'}),
        }


class SignupStatusForm(forms.ModelForm):
    class Meta:
        model = SignUpClass
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'form-select'})}

class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        questions = QuizQuestion.objects.all().order_by('order')
        for q in questions:
            choices = [(opt.id, opt.text) for opt in q.options.all()]
            self.fields[f'q_{q.id}'] = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect(attrs={'class': 'quiz-radio'}),
                label=q.text,
                required=True
            )