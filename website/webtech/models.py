from django.contrib.gis.db import models
from django.db.models.functions import Length

from .scripts.geocoder import Geocoder


class Venue(models.Model):
    name = models.CharField(max_length=50)
    point = models.PointField()
    address_fr = models.TextField(default='')
    address_nl = models.TextField(default='')
    description = models.TextField()
    image = models.ImageField(upload_to='images', default='default.png')

    def save(self, *args, **kwargs):
        if not (self.address_fr and self.address_nl):
            geocoder = Geocoder()
            location = geocoder.reverse(self.point)
            self.address_fr = location.address_fr
            self.address_nl = location.address_nl
        super(Venue, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=100)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    description = models.TextField(default='')
    price = models.DecimalField(decimal_places=2, max_digits=7, null=True)
    official_page = models.CharField(max_length=200, default='')
    previews = models.ManyToManyField('Preview')
    datetime = models.DateTimeField()
    genres = models.ManyToManyField('Genre')
    image = models.ImageField(upload_to='images', default='default.png')

    def short_genres_list(self):
        characters_len = 0
        passed_genres = []
        for genre_obj in self.genres.all().order_by(Length('name').asc()):
            if len(passed_genres) < 3 and len(genre_obj.name) + characters_len < 20:
                characters_len += len(genre_obj.name)
                passed_genres.append(genre_obj.name)
            else:
                break
        return passed_genres

    def __str__(self):
        return self.name


class Preview(models.Model):
    url = models.TextField()
    type = models.CharField(max_length=20)


class Genre(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=100)
    events = models.ManyToManyField('Event')
    last_fm_entry_exists = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class VenueReview(models.Model):
    #author = models.ForeignKey('User', on_delete=models.CASCADE)
    text = models.TextField()



