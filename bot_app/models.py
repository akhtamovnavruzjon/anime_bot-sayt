from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Janr nomi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Janr"
        verbose_name_plural = "Janrlar"


class Anime(models.Model):
    title = models.CharField(max_length=255, verbose_name="Anime nomi")
    code = models.IntegerField(unique=True, verbose_name="Anime kodi")
    genres = models.ManyToManyField(Genre, related_name="animes", verbose_name="Janrlari")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsifi")

    # Web-sayt va Telegram bot uchun rasmlar
    poster = models.ImageField(upload_to="posters/", blank=True, null=True, verbose_name="Web uchun Poster (Rasm)")
    image_file_id = models.CharField(max_length=550, blank=True, null=True, verbose_name="Telegram Photo File ID")

    def __str__(self):
        return f"{self.code} - {self.title}"

    class Meta:
        verbose_name = "Anime"
        verbose_name_plural = "Animelar"


class Episode(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name="episodes", verbose_name="Anime")
    season = models.IntegerField(default=1, verbose_name="Fasl")
    episode_number = models.IntegerField(verbose_name="Qism raqami")
    file_id = models.CharField(max_length=550, verbose_name="Telegram Video File ID")

    def __str__(self):
        return f"{self.anime.title} | {self.season}-fasl {self.episode_number}-qism"

    class Meta:
        verbose_name = "Qism"
        verbose_name_plural = "Qismlar"
        unique_together = ('anime', 'season', 'episode_number')