import json
import datetime
from flask import Flask,render_template,request,redirect,flash,url_for


competition_file = 'competitions.json'
club_file ='clubs.json'


app = Flask(__name__)
app.secret_key = 'something_special'


def loadDB(db_file, name):
    with open(db_file) as c:
         db_list = json.load(c)[name]
         return db_list


competitions = sorted(loadDB(competition_file, 'competitions'), key=lambda item: item['date'], reverse=True)
clubs = loadDB(club_file, 'clubs')


def updateDB(db_file, data_dict):
    with open(db_file, "w") as c:
        json.dump(data_dict, c)


def loadPlacesAlreadyBooked(competition, club):
    if len(competition['clubsParticipating']) > 0:
        count = 0
        for i in competition['clubsParticipating']:
            if club['name'] == i['club']:
                count += 1
                return int(i['placesBooked'])
        if count == 0:
            return 0
    else:
        return 0


def datetime_check(competition):
    today = date_str_split(str(datetime.datetime.now()))
    competition_date = date_str_split(competition['date'])

    if int(today) < int(competition_date):
        competition['status'] = 'open'
    else:
        competition['status'] = 'closed'
    return competition


def date_str_split(date):
    days = date[:10].replace("-","")
    hours = date[11:16].replace(":","")
    date = days+hours
    return str(date)


def bookingLimit(competition, club, already_booked):
    listed = []
    listed.append(int(competition['numberOfPlaces']))
    listed.append(int(club['points']))
    listed.append(12-int(already_booked))
    return min(listed)


def updatePlacesBookedOrCreate(competition, club, places):
    if len(competition['clubsParticipating']) > 0:
        count=0
        for i in competition['clubsParticipating']:
            if club['name'] == i['club']:
                count += 1
                if places == 0 :
                    index_to_delete = competition['clubsParticipating'].index(i)
                    del competition['clubsParticipating'][index_to_delete]
                else :
                    i['placesBooked'] = places
        if count == 0:
            competition["clubsParticipating"].append(
                {'club': club['name'], 'placesBooked': places})
    else:
        if places > 0:
            competition["clubsParticipating"].append({'club': club['name'], 'placesBooked': places})
    return competition


@app.route('/')
def index(error_message="False"):
    return render_template('index.html', error_message=error_message)


@app.route('/showSummary',methods=['POST'])
def showSummary():
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
        for i in competitions:
            i = datetime_check(i)
    except IndexError:
        return index(error_message="Sorry, that email wasn't found.")
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        placesAlreadyBooked = loadPlacesAlreadyBooked(foundCompetition, foundClub)
        bookingMax = bookingLimit(foundCompetition, foundClub, placesAlreadyBooked)
        return render_template('booking.html',club=foundClub, competition=foundCompetition, placesAlreadyBooked=placesAlreadyBooked,
                               booking_max=bookingMax)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    competition = datetime_check(competition)
    placesAlreadyBooked = loadPlacesAlreadyBooked(competition, club)
    placesRequired = int(request.form['places'])
    totalPlacesBooked = placesAlreadyBooked+placesRequired
    competition['numberOfPlaces'] = int(competition['numberOfPlaces'])-placesRequired
    competition = updatePlacesBookedOrCreate(competition, club, totalPlacesBooked)
    club['points'] = int(club['points'])-placesRequired
    club_db = updateDB(club_file, {"clubs":clubs})
    competition_db = updateDB(competition_file, {"competitions":competitions})
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)








# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))

