import email
from multiprocessing import context
from unicodedata import name
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

# Create your views here.

# rooms = [
#     {'id': 1, 'name': 'Lets learn python'},
#     {'id': 2, 'name': 'Design with me'},
#     {'id': 3, 'name': 'Frontend Developer'},
# ]

def loginPage(request):    #login page

    page = 'login'   #set page to login

    if request.user.is_authenticated:   #if user is authenticated
        return redirect('home')         #redirect to home

    if request.method == 'POST':        #if method is post
        email = request.POST.get('email').lower()   #get username
        password = request.POST.get('password')      #get password

        try:
            user = User.objects.get(email=email)  #get user by username
        except:
            messages.error(request, 'User does not exist')  #if user does not exist

        user = authenticate(request, email=email, password=password)  #authenticate user

        if user is not None:    #if user is not none
            login(request, user)    #login user
            return redirect('home')     #redirect to home
        else:
            messages.error(request, 'Username Or password does not exist')  #if user does not exist
            return redirect('login')    #redirect to login

    context = {'page': page}    #pass page to context
    return render(request, 'base/login_register.html', context)     #render login_register.html


def logoutUser(request):    #logout user
    logout(request)     #logout user
    return redirect('home')     #redirect to home


def registerPage(request):      #register page
    
    form = MyUserCreationForm()   #create form

    if request.method == 'POST':    #if method is post
        form = MyUserCreationForm(request.POST)   #create form with post data
        if form.is_valid():     #if form is valid
            user = form.save(commit=False)  #save user
            user.username = user.username.lower()     #set username to lowercase
            user.save()     #save user
            login(request, user)    #login user
            return redirect('home')     #redirect to home
        else:
            messages.error(request, 'An error occured')     #if form is not valid

    return render(request, 'base/login_register.html', {'form': form})      #render login_register.html



def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topic = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, 'topics': topic, 'room_count': room_count,
                'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)    #get room by id

    room_messages = room.message_set.all()    #get all messages from room
    participents = room.participants.all()    #get all participents from room

    if request.method == 'POST':    #if method is post
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)     #redirect to room
        

    context = {'room': room, 'room_messages': room_messages,
                'participants': participents}   #pass room and messages to context
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)    #get user by id

    rooms = user.room_set.all()    #get all rooms from user
    room_messages = user.message_set.all()    #get all messages from user
    topics = Topic.objects.all()    #get all topics

    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages,
                'topics': topics}    #pass user to context
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')    #check if user is logged in
def createRoom(request):
    form = RoomForm()   #create form
    topics = Topic.objects.all()    #get all topics

    if request.method == 'POST':
        topic_name = request.POST.get('topic')    #get topic name
        topic, created = Topic.objects.get_or_create(name=topic_name)    #get or create topic
        
        Room.objects.create(
            host=request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
        )
        return redirect('home')     #redirect to home

    context = {'form': form, 'topics': topics}    #pass form to context
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')  #check if user is logged in
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)  #get room by id
    form = RoomForm(instance=room)  #create form with room data
    topics = Topic.objects.all()    #get all topics

    if request.user != room.host:   #check if user is host
        return HttpResponse('You are not allowed here!!!')  #if user is not host, return error

    if request.method == 'POST':
        topic_name = request.POST.get('topic')    #get topic name
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}    #pass form to context
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here!!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)


    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})