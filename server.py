import json
from flask import Flask,render_template,request,redirect,flash,url_for


competition_file = 'competitions.json'
club_file ='clubs.json'


app = Flask(__name__)
app.secret_key = 'something_special'

# def loadClubs():
#     with open(club_file) as c:
#          listOfClubs = json.load(c)['clubs']
#          return listOfClubs
# def loadCompetitions():
#     with open(competition_file) as comps:
#          listOfCompetitions = json.load(comps)['competitions']
#          return listOfCompetitions

def loadDB(db_file, name):
    with open(db_file) as c:
         db_list = json.load(c)[name]
         return db_list


competitions = loadDB(competition_file, 'competitions')
clubs = loadDB(club_file, 'clubs')

# def updateClubsDB():
#     with open(club_file, "w") as c:
#         data = {'clubs': clubs}
#         json.dump(data, c)
#
# def updateCompetitionDB():
#     with open('competitions.json', "w") as cr:
#         data = {'competitions': competitions}
#         json.dump(data, cr)


def updateDB(db_file, data_dict):
    with open(db_file, "w") as c:
        json.dump(data_dict, c)



def loadPlacesAlreadyBooked(competition, club):
    if len(competition['clubsParticipating']) > 0:
        for i in competition['clubsParticipating']:
            if club['name'] == i['club']:
                return int(i['placesBooked'])
    else:
        return 0


def updatePlacesBookedOrCreate(competition, club, places):
    if len(competition['clubsParticipating']) > 0:
        count=0
        for i in competition['clubsParticipating']:
            if club['name'] == i['club']:
                i['placesBooked'] = places
                count += 1
        if count == 0:
            competition["clubsParticipating"].append(
                {'club': club['name'], 'placesBooked': places})
        return competition
    else:
        competition["clubsParticipating"].append({'club': club['name'], 'placesBooked': places})
        return competition


@app.route('/')
def index(error_message="False"):
    return render_template('index.html', error_message=error_message)


@app.route('/showSummary',methods=['POST'])
def showSummary():
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
    except IndexError:
        return index(error_message="Sorry, that email wasn't found.")
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        placesAlreadyBooked = loadPlacesAlreadyBooked(foundCompetition, foundClub)
        return render_template('booking.html',club=foundClub,competition=foundCompetition, placesAlreadyBooked=placesAlreadyBooked)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesAlreadyBooked = loadPlacesAlreadyBooked(competition, club)
    placesRequired = int(request.form['places'])
    totalPlacesBooked = placesAlreadyBooked+placesRequired
    if placesRequired > int(club['points']):
        error_message = "You don't have enough points to make this reservation"
        return render_template('booking.html', club=club, competition=competition, error_message=error_message)
    elif totalPlacesBooked > 12:
        error_message = "You can't book more than 12 places for an event"
        return render_template('booking.html', club=club, competition=competition, placesAlreadyBooked=placesAlreadyBooked,
                               error_message=error_message)
    else:
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

