from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .forms import EventFilterForm, AddVenueForm, AddEventToVenueForm, MapForm, ReviewForm
from .models import Venue, Event, Genre, Artist, Preview, VenueReview
from .scripts.geocoder import Geocoder
from django.utils import timezone
import requests
from math import ceil
from .helpers import LOREM_2_P, LOREM_1_P, erase_everything, django_image_from_url, django_image_from_file
from random import randint
import os

def is_artist_on_lastfm(artist):
    try:
        api_key = "21be84da5456cdad7c3f91947422f8ad"
        artist.replace(" ", "%20")
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&artist={artist}&api_key={api_key}&format=json"
        r = requests.get(url).json()
        if 'error' in r:
            return False
        # TODO: Verify if it actually contains usefull data.
        return True
    except:
        return False


def index(request):
    """
    The home page containing the search function.
    """
    page_n = int(request.GET.get('p', 1))
    page_n = 1 if page_n == 0 else page_n
    search_results_events = []
    last_page_post_data = None
    filter_div_open = False
    if request.method == 'GET' and 'current-search' in request.session:
        # Whenever you change a page it will be considdered a GET request.
        # I want to force it to be a POST request anyway and apply the form data again.
        request.POST = request.session['current-search']
        request.method = 'POST'
        last_page_post_data = request.POST.copy()
        search_results_events = []

    if request.method == 'POST':
        form = EventFilterForm(request.POST)
        if form.is_valid():
            print(form.data)
            event_title = form.cleaned_data['event_title']
            genres = form.cleaned_data['genres'].split(', ')
            if '' in genres:
                genres.remove('')
            date = form.cleaned_data['date']
            city = form.cleaned_data['city']
            _range = form.cleaned_data['range']
            range_unit = form.cleaned_data['range_unit']
            search_results_events = Event.objects.filter(name__contains=event_title)
            if date:
                filter_div_open = True
                search_results_events = search_results_events.filter(datetime__date=date)
            if genres:
                filter_div_open = True
                search_results_events = search_results_events.filter(genres__name__in=genres).distinct()

            request.session['current-search'] = request.POST

            if last_page_post_data is None:
                # If last_page_post_data is None, the user submitted a different form from the last
                # and the page counter should restart.
                page_n = 1
    else:
        form = EventFilterForm()
        search_results_events = Event.objects.all()

    pages = list(range(int(ceil(len(search_results_events) / 20.0)) + 1)[1:])  # Number of pages
    search_results_events = search_results_events.order_by('datetime')[(page_n-1)*20:page_n*20]  # Only the events that should be displayed on this page.
    # Put the results in blocks of 2. e.g [[event1, event2], [event3, event4], [event5]
    search_results = []
    for i, item in enumerate(search_results_events):
        if i % 2 == 0:
            search_results.append([])
        search_results[-1].append(item)

    all_genres = list(Genre.objects.all().values_list('name', flat=True))
    context = {
        'carousel_events': Event.objects.all().order_by('datetime')[:5],
        'search_results': search_results,
        'page_n': page_n,
        'pages': pages,
        'form': form,
        'all_genres': all_genres,
        'filter_div_open': filter_div_open
    }
    return render(request, 'index.html', context)


def bookmark_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    return HttpResponse("OK")


def event_page(request, event_id):
    event = Event.objects.get(pk=event_id)
    context = {'event': event}
    return render(request, 'event_page.html', context)


def venue_page(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            text = review_form.cleaned_data['text']
            score = review_form.cleaned_data['score']
            review = VenueReview(text=text, score=score, venue=venue, date=timezone.now())
            review.save()

    else:
        review_form = ReviewForm()

    context = {'venue': venue,
               'review_form': review_form
               }
    return render(request, 'venue.html', context)


def map(request):
    context = {
        'form': MapForm(),
        'mapboxtoken': os.environ.get('MAPBOXACCESSTOKEN'),
        }
    return render(request, 'map.html', context)

def events_on_date(request):
    from datetime import date

    def parseEvent(evt):
        return {
                'id': evt.id,
                'name': evt.name,
                'venue': evt.venue.name,
                'latLng': [evt.venue.point.x, evt.venue.point.y],
                'artists': [{'id': x['id'], 'name': x['name']} for x in evt.artists.values()],
                'date': evt.datetime.strftime('%h %-d'),
                'time': evt.datetime.strftime('%H:%M'),
                'weekday': evt.datetime.strftime('%a'),
                }

    events = []
    if request.method == 'GET':
        the_date = date(*(int(request.GET[x]) for x in ('yy','mm','dd')))
        results = Event.objects.filter(datetime__date=the_date)
        events = [parseEvent(x) for x in results]

    response = str(events).replace("'", '"')
    return HttpResponse(response)


def user_locate(request):
    from django.contrib.gis.measure import D
    from django.contrib.gis.geos.point import Point

    def parseVenue(venue):
        return {
                'id': venue.id,
                'name': venue.name,
                'address': venue.address_nl,
                'latLng': [venue.point.x, venue.point.y],
                }


    venues = []
    if request.method == 'GET':
        latlng = Point(float(request.GET['lat']), float(request.GET['lng']))
        results = Venue.objects.filter(point__distance_lte=(latlng, D(km=5)))
        venues = [parseVenue(x) for x in results]

    response = str(venues).replace("'", '"')
    return HttpResponse(response)


# ----------- Testing --------------- #


def add_venue_form_test(request):
    context = {}
    if request.method == 'POST':
        form = AddVenueForm(request.POST, request.FILES)
        if form.is_valid():
            venue_name = form.cleaned_data['venue_name']
            address = form.cleaned_data['address']
            try:
                address_fr, address_nl, point = Geocoder().geocode(address)
                description = form.cleaned_data['description']
                venue_image = form.cleaned_data['venue_image']
                venue_instance = Venue(
                    name=venue_name,
                    point=point,
                    address_fr=address_fr,
                    address_nl=address_nl,
                    description=description,
                    image=venue_image
                )
                venue_instance.save()
            except ValueError:
                form = AddVenueForm()
    else:
        form = AddVenueForm()
    context['form'] = form
    return render(request, 'add_venue_form.html', context)


def add_event_form_test(request):
    context = {}
    if request.method == 'POST':
        form = AddEventToVenueForm(request.POST, request.FILES)
        if form.is_valid():
            event_name = form.cleaned_data['event_name']
            venue = form.cleaned_data['venue']
            artists_raw = form.cleaned_data['artists']
            description = form.cleaned_data['description']
            price_strig = form.cleaned_data['price']
            price = 0 if "free" in price_strig.lower() else float(price_strig)
            event_image = form.cleaned_data['event_image']
            date = form.cleaned_data['date']
            venue_object = Venue.objects.get(id=venue)
            event_instance = Event(name=event_name, venue=venue_object, description=description, price=price, image=event_image, datetime=date)
            event_instance.save()

            for artist in artists_raw.split(','):
                last_fm_exists = is_artist_on_lastfm(artist)
                artist_instance = Artist(name=artist, last_fm_entry_exists=last_fm_exists)
                artist_instance.save()
                artist_instance.events.add(event_instance)
    else:
        form = AddEventToVenueForm()
    context['form'] = form

    return render(request, 'add_event_form.html', context)

def scrapelastfm(request):
    from .scripts.scrapers.lastfm_scraper import LastfmScraper

    Event.objects.all().delete()
    Artist.objects.all().delete()
    Preview.objects.all().delete()
    Genre.objects.all().delete()
    Venue.objects.all().delete()

    scraped = LastfmScraper(Geocoder())

    for venue in scraped.venues:
        venue_object = Venue.objects.filter(name=venue.name)
        if not venue_object:
            venue_object = Venue(
                name=venue.name,
                point=venue.point,
                address_fr=venue.address_fr,
                address_nl=venue.address_nl,
                description=LOREM_1_P,
                image=django_image_from_file('images/default_venue.png')
            )
            venue_object.save()
            for i in range(7):
                review = VenueReview(text=LOREM_2_P, score=randint(0, 10), venue=venue_object, date=timezone.now())
                review.save()

    for event in scraped.events:
        event_object = Event(
            name=event.name,
            venue=Venue.objects.get(name=event.venue.name),
            image=django_image_from_url(event.image) if event.image else django_image_from_file('images/default_event.jpg'),
            official_page=event.official_page,
            description=LOREM_1_P,
            datetime=event.datetime
        )
        event_object.save()

    for artist in scraped.artists:
        last_fm_exists = is_artist_on_lastfm(artist.name)
        artist_object, _ = Artist.objects.get_or_create(name=artist.name, last_fm_entry_exists=last_fm_exists)
        for event in artist.events:
            event_object = Event.objects.get(name=event.name)
            artist_object.events.add(event_object)
        artist_object.save()

    return HttpResponse("OK")


def scrape(request):
    from .scripts.scrapers.flagey_scraper import FlageyScraper
    from .scripts.scrapers.ab_scraper import ABScraper

    Event.objects.all().delete()
    Artist.objects.all().delete()
    Preview.objects.all().delete()
    Genre.objects.all().delete()
    Venue.objects.all().delete()

    for scraper in [FlageyScraper(), ABScraper()]:
        address_fr, address_nl, point = Geocoder().geocode(scraper.venue_addres)
        venue_object, is_new_venue = Venue.objects.get_or_create(
            name=scraper.venue_name,
            point=point,
            address_fr=address_fr,
            address_nl=address_nl,
            description=scraper.description,
            image=django_image_from_url(scraper.venue_image),
        )
        if is_new_venue:
            # Is the venue is new, write some reviews for them.
            for i in range(7):
                review = VenueReview(text=LOREM_2_P, score=randint(0, 10), venue=venue_object, date=timezone.now())
                review.save()

        results = scraper.start_scrape(limit_results=False)
        for event_dict in results:
            event_name = event_dict['event_title']
            description = event_dict['event_description']
            if description is None:
                description = ""
            image = django_image_from_url(event_dict['event_image'])
            event_object = Event(name=event_name,
                                 venue=venue_object,
                                 description=description,
                                 price=event_dict['event_price'],
                                 image=image,
                                 official_page=event_dict['event_url'],
                                 datetime=event_dict['event_datetime'])
            event_object.save()

            # No artists are currently scraped from an event. For testing purposes only, asume the event title is the artist.
            # This will not be accurate, but good enough for demonstration.
            for artist in [event_name]:
                artist_adjusted = artist[:100].split(' feat')[0].split(" + ")[0]  # feat. in a title can mean the the band name was before it.
                last_fm_exists = is_artist_on_lastfm(artist_adjusted)
                artist_instance, new = Artist.objects.get_or_create(name=artist_adjusted, last_fm_entry_exists=last_fm_exists)
                artist_instance.events.add(event_object)

            for preview_url in event_dict['previews']:
                p, _ = Preview.objects.get_or_create(url=preview_url, type="youtube")
                event_object.previews.add(p)

            for genre in event_dict['event_tags']:
                g, _ = Genre.objects.get_or_create(name=genre)
                event_object.genres.add(g)

    return HttpResponse("OK")
