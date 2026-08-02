from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Anime, Genre, Episode

# 1. Asosiy sahifa (Barcha animelar ro'yxati)
def anime_list(request):
    animes = Anime.objects.all().order_by('-id') # Yangi animelar birinchi chiqadi
    return render(request, 'anime_list.html', {'animelar': animes})

# 2. Anime haqida batafsil ma'lumot sahifasi
def anime_detail(request, pk):
    anime = get_object_or_404(Anime, pk=pk)
    return render(request, 'anime_detail.html', {'anime': anime})

# 3. Faqat Superuser uchun anime qo'shish sahifasi
@user_passes_test(lambda u: u.is_superuser)

def add_anime(request):
    if request.method == 'POST':
        # 1. Anime yaratamiz (models.py dagi image_file_id bilan)
        title = request.POST.get('title')
        code = request.POST.get('code')
        poster = request.FILES.get('poster')
        image_file_id = request.POST.get('image_file_id') # Telegram rasm IDsi
        description = request.POST.get('description')

        anime = Anime.objects.create(
            title=title,
            code=code,
            poster=poster,
            image_file_id=image_file_id,
            description=description
        )

        # 2. Janrlarni biriktiramiz
        genre_ids = request.POST.getlist('genres')
        if genre_ids:
            anime.genres.set(genre_ids)

        # 3. Qismlarni Episode modelidagi `file_id` maydoniga saqlaymiz
        seasons = request.POST.getlist('seasons[]')
        episode_numbers = request.POST.getlist('episode_numbers[]')
        file_ids = request.POST.getlist('file_ids[]')

        for i in range(len(seasons)):
            if seasons[i] and episode_numbers[i] and i < len(file_ids) and file_ids[i]:
                Episode.objects.create(
                    anime=anime,
                    season=seasons[i],
                    episode_number=episode_numbers[i],
                    file_id=file_ids[i] # Aniq models.py dagi `file_id`
                )

        return redirect('/')

    genres = Genre.objects.all()
    return render(request, 'add_anime.html', {'genres': genres})