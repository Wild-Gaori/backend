from django.contrib import admin
from .models import Artwork
from .models import Artist

admin.site.register(Artwork)
admin.site.register(Artist)