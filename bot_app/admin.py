from django.contrib import admin
from .models import Anime, Episode,Genre

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1

@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ('title', 'code')
    search_fields = ('code', 'title')
    inlines = [EpisodeInline]  # Anime sahifasining o'zida qismlarni qo'shish imkonini beradi

admin.site.register(Genre)