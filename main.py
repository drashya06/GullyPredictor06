import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import re
from flask import Flask,render_template,redirect,url_for,send_from_directory,request
import requests
from bs4 import BeautifulSoup
from pandas.io.html import read_html
from prediction import bowling_predictor,batting_predictor


data = requests.get("https://www.espncricinfo.com/live-cricket-score")
data = BeautifulSoup(data.text, "lxml")
livescore = data.find(class_="row no-gutters")

livefix = {}
for i, matchdata in enumerate(livescore):
    fix = {}
    fix["url"] = "https://www.espncricinfo.com" + matchdata.find("a", class_="match-info-link-FIXTURES").get("href")
    scoreblock = matchdata.find(class_='match-info match-info-FIXTURES')
    if scoreblock.find(class_="status red"):
        status = scoreblock.find(class_="status red")
    else:
        status = scoreblock.find(class_="status")
    description = scoreblock.find(class_='description')
    teams = scoreblock.find(class_="teams")
    try:
        fix["status"] = str(status.text).upper()
    except:
        fix["status"] = str(status).upper()

    fix['description'] = description.text

    fix["status-text"] = matchdata.find(class_="status-text").text

    for j, team in enumerate(teams):
        if team.find(class_="batting-indicator"):
            fix['Team_' + str(j+1)] = [team.find(class_="name").text, team.find(class_="score").text,
                                         team.find(class_="score-info").text]

        elif team.find(class_="score-detail"):
            fix['Team_' + str(j+1)] = [team.find(class_="name").text, team.find(class_="score").text,
                                         team.find(class_="score-info").text]

        else:
            fix['Team_' + str(j+1)] = [team.find(class_="name").text]
    livefix[i] = fix

url = "https://www.espncricinfo.com/ci/content/player/index.html"

data = requests.get(url)
data = BeautifulSoup(data.text, "lxml")

# player_urls = {}
# player_id = {}
intl_team_url = {}
main_url = "https://www.espncricinfo.com/ci/content/player/country.html?country="
total = data.select(".ciPlayersHomeCtryList")
for i in total:
    team_html = i.find_all("a")
    for team in team_html:
        if team.text not in intl_team_url.keys():
            intl_team_url[team.text] = main_url + re.split("=", team.get("href"))[1]

team_url = intl_team_url


def cappedplayerurls():
    # Get all capped player from here and then extract there data frame

    url = "https://www.espncricinfo.com/ci/content/player/index.html"

    data = requests.get(url)
    data = BeautifulSoup(data.text, "lxml")

    contractedplayer_urls = {}
    player_id = {}
    intl_team_url = {}
    main_url = "https://www.espncricinfo.com/ci/content/player/country.html?country="
    total = data.select(".ciPlayersHomeCtryList")
    for i in total:
        team_html = i.find_all("a")
        for team in team_html:
            if team.text not in intl_team_url.keys():
                intl_team_url[team.text] = main_url + re.split("=", team.get("href"))[1]

    for team in intl_team_url:
        team_players = {}
        url = intl_team_url[team]
        teamdata = requests.get(url)
        teamdata = BeautifulSoup(teamdata.text, "lxml")
        playerdata = teamdata.select(".playersTable")
        #     print(len(playerdata))
        for k in playerdata:
            playerstats = k.find_all("tr")
            for m in playerstats:
                player = m.find_all("td")
                for dta in player:
                    p_data = dta.find_all("a")
                    for p in p_data:
                        if p.text not in team_players.keys():
                            contractedplayer_urls[p.text] = str(p.get("href")).split("/")[-1]

    return contractedplayer_urls
# All Capped player at Present
player_urls = cappedplayerurls()


def allplayersurl():
    url = "https://www.espncricinfo.com/ci/content/player/index.html"

    data = requests.get(url)
    data = BeautifulSoup(data.text, "lxml")

    total = data.select(".ciPlayersHomeCtryList")

    for i in total:
        team_html = i.find_all("a")
        team_url = {}
        for team in team_html:
            if team.text not in team_url.keys():
                team_url[team.text] = team.get("href").split("?")[-1]
    # for team in intl_team_url:
    #     team_players = {}
    #     url = intl_team_url[team]
    #     teamdata = requests.get(url)
    #     teamdata = BeautifulSoup(teamdata.text, "lxml")
    #     playerdata = teamdata.select(".playersTable")
    #     #     print(len(playerdata))
    #     for k in playerdata:
    #         playerstats = k.find_all("tr")
    #         for m in playerstats:
    #             player = m.find_all("td")
    #             for dta in player:
    #                 p_data = dta.find_all("a")
    #                 for p in p_data:
    #                     if p.text not in team_players.keys():
    #                         player_urls[p.text] = "https://www.espncricinfo.com" + str(p.get("href"))
    #                         player_id[p.text] = str(p.get("href")).split("/")[-1]

    # All Players Url After 2000 Debut

    allplayer_urls = {}
    for team in team_url:
        #     print(team)
        for type_ in range(2, 4):
            url = "https://www.espncricinfo.com/ci/content/player/caps.html?{};class={}".format(team_url[team], type_)
            # Players Capped after 2000 for ODI,T20
            data = requests.get(url)
            data = BeautifulSoup(data.text, "lxml")

            p_data = data.find(class_="ciPlayerbycapstable")
            li = p_data.find_all("li")

            for l in li:
                ul = l.find_all("ul")

                if len(ul) > 0:
                    if int(ul[0].find(class_="ciPlayerplayed").text.split(",")[-1].split('/')[0]) > 1999:
                        player_d = ul[0].find(class_="ciPlayername")
                        player_d = player_d.find("a")
                        player_url = player_d.get("href").split("/")[-1]
                        player_name = player_d.text
                        if player_name not in allplayer_urls.keys():
                            allplayer_urls[player_name] = player_url
    return allplayer_urls

allplayer_urls = allplayersurl()
# IPL Result and Link generation

url = "https://stats.espncricinfo.com/ci/engine/records/team/series_results.html?id=117;type=trophy"
ipl_results = requests.get(url)
ipl_results = BeautifulSoup(ipl_results.text,"lxml")
url_seasonwise = {}
d = ipl_results.select(".engineTable")
d = d[0].find("tbody")
t = d.find_all("td")
for i in range(len(t)):
    if "Indian Premier League" in t[i].text:
        s = t[i].find(class_="data-link").get("href").split("/")[-1]
        url_seasonwise[t[i+1].text.replace("/","-")] = s.split(".")[0]
url_seasonwise['2021'] = '1249214'

team_urls = intl_team_url

data_ = requests.get("https://www.espncricinfo.com/series/ipl-2021-1249214/match-schedule-fixtures")
data_ = BeautifulSoup(data_.text, "lxml")
iplscore = data_.find(class_="row no-gutters")

iplfix = {}
for i, matchdata in enumerate(iplscore):
    fix = {}
    fix["url"] = "https://www.espncricinfo.com" + matchdata.find("a", class_="match-info-link-FIXTURES").get("href")
    scoreblock = matchdata.find(class_='match-info match-info-FIXTURES')
    if scoreblock.find(class_="status red"):
        status = scoreblock.find(class_="status red")
    else:
        status = scoreblock.find(class_="status")
    description = scoreblock.find(class_='description')
    teams = scoreblock.find(class_="teams")
    try:
        fix["status"] = status.text
    except:
        fix["status"] = status

    fix['description'] = description.text

    fix["status-text"] = matchdata.find(class_="status-text").text

    for j, team in enumerate(teams):
        if team.find(class_="batting-indicator"):
            fix['Team_' + str(j)] = [team.find(class_="name").text, team.find(class_="score").text,
                                     team.find(class_="score-info").text]

        elif team.find(class_="score-detail"):
            fix['Team_' + str(j + 1)] = [team.find(class_="name").text, team.find(class_="score").text,
                                         team.find(class_="score-info").text]

        else:
            fix['Team_' + str(j + 1)] = [team.find(class_="name").text]
    iplfix[i] = fix

def profile_pic(url):
    p_data = requests.get('https://www.espncricinfo.com/ci/content/player/'+url)
    p_data = BeautifulSoup(p_data.text, "lxml")
    return p_data.find_all("img")[3].get("src")

def ipl_seasonwise_squad(ids):
    url = "https://www.espncricinfo.com/ci/content/squad/index.html?object={}".format(ids)
    data = requests.get(url)
    data = BeautifulSoup(data.text, "lxml")
    ipl_urls = {}
    data = data.select(".squads_list")[0]
    dt = data.find_all("a")
    for a in dt:
        # a = dt.find_all("a")
        ipl_urls[a.text.replace(" Squad", '')] = "https://www.espncricinfo.com" + a.get("href")
    return ipl_urls


def squad(team):
    team_urls = ipl_urls
    team_players_url = {}
    url = team_urls[team]
    data = requests.get(url)
    data = BeautifulSoup(data.text, "lxml")
    data = data.find("ul", class_="large-block-grid-2 medium-block-grid-2 small-block-grid-1")
    data = data.find_all("li")
    team_players = {}
    for d in data:
        pinfo = []
        im = d.find(class_="large-7 medium-7 small-7 columns")
        try:
            im = "https://www.espncricinfo.com" + im.find("img").get("src")
        except:
            im = ""
        pinfo.append(im)
        span = d.find_all("span")
        name = d.find("h3")
        name = name.find("a")
        player = name.text.strip()
        for s in span:
            pinfo.append(s.text.replace("withdrawn player", ''))
        team_players[player] = pinfo
        if player not in team_players_url.keys():
            team_players_url[player] = d.find("a").get("href").split("/")[-1]
        not_found = True
        if player not in allplayer_urls.keys():
#             print(player)
            for name, url in allplayer_urls.items():
#                 print(d.find("a").get("href").split("/")[-1])
                if url == d.find("a").get("href").split("/")[-1]:
                    team_players_url[name] = team_players_url.pop(player)
                    team_players[name] = team_players.pop(player)
                    not_found = False
                    break
        if not_found:
            allplayer_urls[player] = d.find("a").get("href").split("/")[-1]
            player_urls[player] = d.find("a").get("href").split("/")[-1]
    return team_players_url,team_players

ipl_urls = ipl_seasonwise_squad("1249214")

app = Flask(__name__)

app.config['SECRET_KEY'] ='f48300a6510cad4e23cb9294dc1928b2'

@app.route("/",methods=['GET','POST'])
@app.route("/home")
def home():
    return render_template('home.html',livescores=iplfix,teams = team_urls)

@app.route("/live")
def live():
    return render_template('live.html',livescores = livefix,teams = team_urls)

@app.route('/livescorecard/<int:index>',methods=['GET','POST'])
def livescorecard(index):
    url_ = livefix[index]['url']
    print(url_)
    data_ = requests.get(url_)
    data_ = BeautifulSoup(data_.text, "lxml")
    scorecard = {}
    print(str(livefix[index]['status']).upper())
    if str(livefix[index]['status']).upper() == "LIVE":
        livescore = data_.find(class_="live-scorecard")
        try:
            scorecard["current_inning"] = livescore.find(class_="current-innings-data d-flex flex-row").text
        except:
            scorecard["current_inning"] = livescore.find(class_="current-innings-data d-flex flex-row")
        df = read_html(livefix[index]['url'],attrs={'class': 'table table-left mb-0'})
        table = []
        for i in range(len(df)):
            df[i] = df[i].rename(columns={"Unnamed: 0":""})
            table.append(df[i].to_html(index=False))
        try:
            scorecard['current_partnership'] = str(data_.find(class_="current-partnerships text-left").text).replace('\xa0',' ')
        except:
            scorecard['current_partnership'] = str(data_.find(class_="current-partnerships text-left")).replace('\xa0', ' ')
        try:
            scorecard["reviews"] = data.find(class_='reviews').text
        except:
            scorecard["reviews"] = data.find(class_='reviews')
        return render_template('livescore.html',scorecard=scorecard, tables=table,teams = team_urls)
    elif str(livefix[index]['status']).upper() == "RESULT":
        livescore = data_.find(class_="match-body")
        content = livescore.find_all(class_="card content-block match-scorecard-table")
        for cont in content:
            header= cont.find(class_="header-title label").text
            table = []
            table.append(read_html(livefix[i]['url'], attrs={"class": "table batsman"}))
            table.append(read_html(livefix[i]['url'], attrs={"class": "table bowler"}))

        return render_template('result.html',header=header,tables=table,teams = team_urls)

    else:
        return render_template('live.html',teams = team_urls)

@app.route("/team<string:t>")
def team(t):
    team_players_url = {}
    if t in ['Chennai Super Kings','Delhi Capitals','Kolkata Knight Riders','Mumbai Indians','Punjab Kings','Rajasthan Royals','Royal Challengers Bangalore','Sunrisers Hyderabad']:
        team_players_url,team_players = squad(t)
        team_urls = ipl_urls
    else:
        team_urls = intl_team_url
        url = team_urls[t]
        team_players = []
        teamdata = requests.get(url)
        teamdata = BeautifulSoup(teamdata.text, "lxml")
        playerdata = teamdata.select(".playersTable")
        for k in playerdata:
            playerstats = k.find_all("tr")
            for m in playerstats:
                player = m.find_all("td")
                for dta in player:
                    p_data = dta.find_all("a")
                    for p in p_data:
                        if p.text not in team_players_url:
                            team_players_url[p.text] = "https://www.espncricinfo.com" + str(p.get("href")).replace("ci",str(t).replace(" ",'').lower())
    player_img=[]
    for name in team_players_url:
        player_img.append(profile_pic(team_players_url[name]))
    return render_template('team.html',players = list(team_players_url.keys()),num_players=len(list(team_players_url.keys())),team_now=t,player_img=player_img,teams = team_urls,pinfo=team_players)

@app.route("/player/<string:name>")
def player(name):
    # print(name)
    url = player_urls[name]
    df = read_html(url, attrs={"class": "engineTable"})
    table = []
    for i in range(len(df)):
        if i != 2:
            table.append(df[i].to_html(index=False))
    table_info = ['Batting and fielding averages','Bowling averages','Recent matches']
    p_data = requests.get(url)
    p_data = BeautifulSoup(p_data.text, "lxml")
    p_info = p_data.find_all(class_="ciPlayerinformationtxt")
    p_img = p_data.find_all("img")[3].get("src")
    player_info = {}
    for pin in p_info:
        player_info[pin.find_all("b")[0].text] = str(pin.find_all("span")[0].text).replace("\n", '')
    return render_template('player.html',img=p_img,info=player_info,tables=table,table_info=table_info,table_length=len(table),teams = team_urls)

@app.route("/ipl",defaults={'ids':"1249214"})
# @ipl.route("/ipl<string:ids>")
def ipl(ids):
    url = "https://stats.espncricinfo.com/ci/engine/records/team/series_results.html?id=117;type=trophy"
    table = read_html(url, attrs={"class": "engineTable"})
    table[0] = table[0].drop(['Unnamed: 2','Margin'],1)
    ipl_urls = ipl_seasonwise_squad(ids)
    return render_template('ipl.html',tables=[table[0].to_html(render_links=True,index=False,justify="center")],seasons=list(url_seasonwise),teams=list(ipl_urls))

@app.route("/predictor/<int:no>")
def predictor(no):
    url = iplfix[no]['url']
    teams = {'Chennai Super Kings': "CSK", 'Delhi Capitals': "DC", 'Kolkata Knight Riders': "KKR",
             'Mumbai Indians': 'MI', 'Punjab Kings': 'KXI', 'Rajasthan Royals': 'RR',
             'Royal Challengers Bangalore': 'RCB', 'Sunrisers Hyderabad': 'SRH'}
    team1 = iplfix[no]['Team_1'][0]
    team2 = iplfix[no]['Team_2'][0]
    team_players_url1,squad_team_1_info = squad(team1)
    team_players_url2,squad_team_2_info = squad(team2)
    # Squad from Live match
    try:
        data = requests.get(url)
        data = BeautifulSoup(data.text, "lxml")
        com_data = data.find_all(class_="match-comment-long-text match-comment-padder")[0]
        ann_squad = {}
        for da in com_data:
            try:
                if da.find("b").text == team1:
                    t = da.text.split(':')
                    ann_squad[t[0]] = t[1]
                elif da.find("b").text == team2:
                    t = da.text.split(':')
                    ann_squad[t[0]] = t[1]
            except:
                continue
        updated_squad = {}
        for te in ann_squad:
            remove_digits = str.maketrans('', '', digits)
            t1 = ann_squad[te].split(',')
            t1 = [p.translate(remove_digits).strip() for p in t1]
            t1 = [p.split('(')[0].strip() for p in t1]
            updated_squad[te] = t1
        squad_team_1 = updated_squad[team1]
        squad_team_2 = updated_squad[team2]

    except:
        squad_team_1 = list(squad_team_1)
        squad_team_2 = list(squad_team_2)

    team1 = teams[team1]
    team2 = teams[team2]
    ground = iplfix[no]['description'].split(',')[1].strip()
    type_ = "IPL"
    team1_dict = {}
    for player in squad_team_1:
        print(player)
        inning = {}
        for i in range(1, 3):
            runs_scored = batting_predictor(player, team2, ground, i, type_)
            wickets_taken = bowling_predictor(player, team2, ground, i, type_)
            inning[i] = {'Runs Scored': runs_scored, "Wicket Taken": wickets_taken}
        team1_dict[player] = inning
    team2_dict = {}
    for player in squad_team_2:
        print(player)
        inning = {}
        for i in range(1, 3):
            runs_scored = batting_predictor(player, team2, ground, i, type_)
            wickets_taken = bowling_predictor(player, team2, ground, i, type_)
            inning[i] = {'Runs Scored': runs_scored, "Wicket Taken": wickets_taken}
        team2_dict[player] = inning

    # player_img_t1 = []
    # player_img_t2 = []
    # for name in team_players_url1:
    #     player_img_t1.append(profile_pic(team_players_url1[name]))
    #
    # for name in team_players_url2:
    #     player_img_t2.append(profile_pic(team_players_url2[name]))
    return render_template('predictor.html',team1=team1,team2=team2,
                           squad1 = squad_team_1,num_players_t1 = len(squad_team_1),
                           squad2 = squad_team_2,num_players_t2 = len(squad_team_2),
                           t1_predict=team1_dict,t2_predict=team2_dict,
                           player_img_t1=squad_team_1_info,player_img_t2=squad_team_2_info,teams=list(ipl_urls))

if __name__ == "__main__":
    app.run(debug=True)

