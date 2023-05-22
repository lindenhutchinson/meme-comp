from django.contrib import admin

from .models import User, Competition, Vote, Participant, Meme, SeenMeme

admin.site.register(User)
admin.site.register(Competition)
admin.site.register(Vote)
admin.site.register(Participant)
admin.site.register(Meme)
admin.site.register(SeenMeme)
