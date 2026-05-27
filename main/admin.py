from django.contrib import admin
from .models import AboutVideo
from .models import Fact
from main.models import *
@admin.register(AboutVideo)
class AboutVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']


@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    list_display = ['text', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']

admin.site.register(Role)
admin.site.register(ProfileUser)
admin.site.register(Category)
admin.site.register(MasterClass)
admin.site.register(SignUpClass)
admin.site.register(Review)
admin.site.register(MasterRequest)
admin.site.register(QuizOption)
admin.site.register(QuizResult)
admin.site.register(QuizQuestion)



