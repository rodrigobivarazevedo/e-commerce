from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, timedelta


from .models import User, AuctionListing, Bid, Comment
from .forms import ListingForm, BidForm, CommentForm


def index(request):
    active_listings = AuctionListing.objects.filter(status='active')
    return render(request, 'auctions/index.html', {'active_listings': active_listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.start_time = datetime.now()  # Set start_time to current date and time
            listing.end_time = listing.start_time + timedelta(hours=24)  # Set end_time to 24 hours after start_time
            # Save the uploaded image file
            listing.save()
            return redirect(reverse('index'))
    else:
        form = ListingForm()
    return render(request, 'auctions/create_listing.html', {'form': form})


def listing_detail(request, listing_id):
    # Retrieve the listing object from the database
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    bidform = BidForm()
    commentform = CommentForm()
    # Check if the user is signed in and perform necessary logic for watchlist, bidding, closing auction, commenting
    return render(request, 'auctions/listing_detail.html', {'listing': listing, "bidform":bidform, "commentform":commentform})


@login_required
def add_bid(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Get the highest bid for the current listing
            highest_bid = listing.bids.order_by('-amount').first()
            
            # Check if the bid is higher than the starting bid and the highest bid (if it exists)
            if amount > listing.starting_bid and (not highest_bid or amount > highest_bid.amount):
                bid = Bid(amount=amount, bidder=request.user, auction_listing=listing)
                bid.save()
                
                # Update current price
                listing.current_price = amount
                listing.save()
                
                messages.success(request, 'Bid placed successfully.')
            else:
                messages.error(request, 'Bid must be greater than the starting bid and any previous bids.')
            
            return redirect('listing_detail', listing_id=listing_id)
    else:
        form = BidForm()
    
    return render(request, 'auctions/add_bid.html', {'form': form, 'listing': listing})


@login_required
def add_comment(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            comment = Comment(content=content, commenter=request.user, auction_listing=listing)
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('listing_detail', listing_id=listing_id)
    else:
        form = CommentForm()
    return render(request, 'auctions/add_comment.html', {'form': form, 'listing': listing})



@login_required
def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    user = request.user
    user.watchlist.add(listing)
    return redirect('listing_detail', listing_id=listing_id)

@login_required
def remove_from_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    user = request.user
    user.watchlist.remove(listing)
    return redirect('listing_detail', listing_id=listing_id)

def watchlist(request):
    user = request.user
    watchlist = user.watchlist.all()
    return render(request, 'auctions/watchlist.html', {'watchlist': watchlist})

def close_auction(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)

    # Ensure only the seller can close the auction
    if request.user == listing.seller:
        # Close the auction and update its status
        listing.status = 'closed'
        # Perform additional logic such as determining the highest bidder
        # and declaring them as the winner
        listing.save()

        messages.success(request, "Auction closed successfully.")
    else:
        messages.error(request, "You are not authorized to close this auction.")

    return redirect('listing_detail', listing_id=listing_id)


