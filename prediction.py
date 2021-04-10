import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from pandas.io.html import read_html
import requests
from bs4 import BeautifulSoup
import os

batting_directory = r"C:\Users\Lenovo\Desktop\Cricket Predictor\matchstats\batting"
bowling_directory = r"C:\Users\Lenovo\Desktop\Cricket Predictor\matchstats\bowling"
if not os.path.exists(batting_directory):
    os.makedirs(batting_directory)
if not os.path.exists(bowling_directory):
    os.makedirs(bowling_directory)

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


player_urls = allplayersurl()


def battingstats(player):
    """
    Takes Players Name and provides DataFrames for Batting Statistic of Player
    """
    # Batting Performances
    try:
        url = "https://stats.espncricinfo.com/ci/engine/player/{}?class=11;template=results;type=batting;view=innings".format(player_urls[player])
        table = read_html(url, attrs={"class": "engineTable"})
        player_with_bat = table[3]
        if len(player_with_bat.columns) == 14:
            player_with_bat = player_with_bat[player_with_bat['BF'] != '-']
            player_with_bat['Out'] = player_with_bat['Dismissal'].apply(lambda x: 0 if x == 'not out' else 1)
            player_with_bat = player_with_bat[['Runs', 'BF', 'SR', 'Out', 'Opposition', 'Ground', 'Start Date', 'Inns']]
            player_with_bat['Type'] = player_with_bat['Opposition'].apply(lambda x: x.split(" v ")[0])
            player_with_bat = player_with_bat[player_with_bat['Type'] == 'T20I']
            player_with_bat['Opposition'] = player_with_bat['Opposition'].apply(lambda x: x.split(" v ")[1])
            player_with_bat['Runs'] = pd.to_numeric(player_with_bat['Runs'].apply(lambda x: (str(x).replace("*", ''))))
            player_with_bat['SR'] = player_with_bat['SR'].apply(lambda x: float(x) if x != '-' else 0.00)
            player_with_bat['BF'] = pd.to_numeric(player_with_bat['BF'])
            player_with_bat['Runss'] = pd.to_numeric(player_with_bat['Runs'])
            #     player_with_bat['6s'] = pd.to_numeric(player_with_bat['6s'])
            player_with_bat['Inns'] = pd.to_numeric(player_with_bat['Inns'])
            player_with_bat['Start Date'] = pd.to_datetime(player_with_bat['Start Date'])
        else:
            player_with_bat = pd.DataFrame(
                columns=['Runs', 'BF', 'SR', 'Out', 'Opposition', 'Ground', 'Start Date', 'Inns', 'Type'])
    except:
        player_with_bat = pd.DataFrame(
            columns=['Runs', 'BF', 'SR', 'Out', 'Opposition', 'Ground', 'Start Date', 'Inns', 'Type'])
    # Data from our dataset of IPL till 2020

    data = pd.read_csv("Data2.csv", low_memory=False)
    data['4s'] = data['batsman_runs'].apply(lambda x: 1 if x == 4 else 0)
    data['6s'] = data['batsman_runs'].apply(lambda x: 1 if x == 6 else 0)
    data['date'] = pd.to_datetime(data['date'])

    # Batting Data From Ipl
    b_data = data[data['batsman'] == player]
    if len(b_data) > 0:
        bat_data = b_data.groupby(['id'])['batsman_runs', 'is_wicket'].sum()
        bat_data = bat_data.reset_index()
        bat_data['BF'] = bat_data['id'].apply(lambda x: b_data[b_data['id'] == x]['ball'].count())
        bat_data['SR'] = round(bat_data['batsman_runs'] / bat_data['BF'], 4) * 100
        bat_data['Inns'] = bat_data['id'].apply(lambda x: b_data[b_data['id'] == x]['inning'].unique()[0])
        bat_data['Opposition'] = bat_data['id'].apply(lambda x: b_data[b_data['id'] == x]['bowling_team'].unique()[0])
        bat_data['Ground'] = bat_data['id'].apply(lambda x: b_data[b_data['id'] == x]['city'].unique()[0])
        bat_data['Start Date'] = bat_data['id'].apply(lambda x: b_data[b_data['id'] == x]['date'].unique()[0])
        bat_data['Type'] = 'IPL'
        bat_data = bat_data.rename(columns={'batsman_runs': 'Runs', 'is_wicket': 'Out'})
        bat_data = bat_data.drop('id', 1)

    else:
        bat_data = pd.DataFrame(
            columns=['Runs', 'BF', 'SR', 'Out', 'Opposition', 'Ground', 'Start Date', 'Inns', 'Type'])

    player_with_bat = player_with_bat.append(bat_data, ignore_index=True)
    player_with_bat = player_with_bat[player_with_bat['BF'] != 0]
    player_with_bat = player_with_bat.sort_values("Start Date").reset_index()

    # Batting Additional Data
    if len(player_with_bat) > 0:
        player_with_bat['Avg_9'] = 0
        player_with_bat['BF_Avg_9'] = 0
        player_with_bat['Avg'] = 0
        player_with_bat['BF-1'] = 0
        player_with_bat['Runs-1'] = 0
        player_with_bat['SR-1'] = 0
        # We will take the average of last 5 inning with avg 4's,6's,'SR','Runs',Avg
        # Avg 4's : No of 4's per Ball Faced
        # Avg 6's : No of 6's per Ball Faced
        # Avg SR: SR/ no of innings for less than 5 else SR/5
        # Avg_5: Average in last 5 innings/5

        for i in range(1, len(player_with_bat)):
            if i > 9:
                if player_with_bat.loc[i - 9:i - 1, 'Out'].sum() != 0:
                    player_with_bat.loc[i, 'Avg_9'] = round(
                        player_with_bat.loc[i - 9:i - 1, 'Runs'].sum() / player_with_bat.loc[i - 9:i - 1, 'Out'].sum(),
                        2)
                else:
                    player_with_bat.loc[i, 'Avg_9'] = player_with_bat.loc[i - 9:i - 1, 'Runs'].sum()
                player_with_bat.loc[i, 'BF_Avg_9'] = round(player_with_bat.loc[i - 9:i - 1, 'BF'].sum() / 9, 2)

            else:
                if player_with_bat.loc[:i - 1, 'Out'].sum() != 0:
                    player_with_bat.loc[i, 'Avg_9'] = round(
                        player_with_bat.loc[:i - 1, 'Runs'].sum() / player_with_bat.loc[:i - 1, 'Out'].sum(), 2)
                else:
                    player_with_bat.loc[i, 'Avg_9'] = player_with_bat.loc[:i - 1, 'Runs'].sum()
                player_with_bat.loc[i, 'BF_Avg_9'] = round(player_with_bat.loc[:i - 1, 'BF'].sum() / (i + 1), 2)

            if player_with_bat.loc[i - 6:i - 1, 'Out'].sum() != 0:
                player_with_bat.loc[i, 'Avg'] = round(
                    player_with_bat.loc[:i - 1, 'Runs'].sum() / player_with_bat.loc[:i - 1, 'Out'].sum(), 2)
            else:
                player_with_bat.loc[i, 'Avg'] = player_with_bat.loc[:i - 1, 'Runs'].sum()
            player_with_bat.loc[i, 'BF-1'] = player_with_bat.loc[i - 1, 'BF']
            player_with_bat.loc[i, 'Runs-1'] = player_with_bat.loc[i - 1, 'Runs']
            player_with_bat.loc[i, 'SR-1'] = player_with_bat.loc[i - 1, 'SR']
    player_with_bat.to_csv(os.path.join(batting_directory, player) + ".csv")
    return player_with_bat

def bowlingstats(player):
    """
    Takes Players Name and provides DataFrames for Batting Statistic of Player
    """
    # Bowling Performance
    try:
        url = "https://stats.espncricinfo.com/ci/engine/player/{}?class=11;template=results;type=bowling;view=innings".format(
            player_urls[player])
        table = read_html(url, attrs={"class": "engineTable"})
        player_with_ball = table[3]
        if len(player_with_ball.columns) == 12:
            player_with_ball = player_with_ball[
                (player_with_ball['Overs'] != 'DNB') & (player_with_ball['Overs'] != 'TDNB')]
            if len(player_with_ball) > 0:
                player_with_ball = player_with_ball[
                    ['Overs', 'Runs', 'Wkts', 'Econ', 'Inns', 'Opposition', 'Ground', 'Start Date']]
                player_with_ball['Type'] = player_with_ball['Opposition'].apply(lambda x: x.split(" v ")[0])
                player_with_ball = player_with_ball[player_with_ball['Type'] == "T20I"]
                player_with_ball['Opposition'] = player_with_ball['Opposition'].apply(lambda x: x.split(" v ")[1])
                player_with_ball['Runs'] = pd.to_numeric(player_with_ball['Runs'])
                player_with_ball['Overs'] = pd.to_numeric(player_with_ball['Overs'])
                player_with_ball['Wkts'] = pd.to_numeric(player_with_ball['Wkts'])
                player_with_ball['Inns'] = pd.to_numeric(player_with_ball['Inns'])
                player_with_ball['Econ'] = player_with_ball['Econ'].apply(lambda x: float(x))
                player_with_ball['Start Date'] = pd.to_datetime(player_with_ball['Start Date'])

        else:
            player_with_ball = pd.DataFrame(columns=['Overs', 'Runs', 'Wkts', 'Econ', 'Inns', 'Opposition',
                                                     'Ground', 'Start Date', 'Type'])
    except:
        player_with_ball = pd.DataFrame(columns=['Overs', 'Runs', 'Wkts', 'Econ', 'Inns', 'Opposition',
                                                 'Ground', 'Start Date', 'Type'])
    # IPl Data

    data = pd.read_csv("Data2.csv", low_memory=False)
    data['date'] = pd.to_datetime(data['date'])

    # Bowling Data from IPL

    b_data = data[data['bowler'] == player]
    if len(b_data) > 16:
        bowl_data = b_data.groupby('id')['batsman_runs', 'is_wicket'].sum()
        bowl_data = bowl_data.reset_index()
        bowl_data['BF'] = bowl_data['id'].apply(lambda x: b_data[b_data['id'] == x]['ball'].count())
        bowl_data['Inns'] = bowl_data['id'].apply(lambda x: b_data[b_data['id'] == x]['inning'].unique()[0])
        bowl_data['Opposition'] = bowl_data['id'].apply(lambda x: b_data[b_data['id'] == x]['batting_team'].unique()[0])
        bowl_data['Ground'] = bowl_data['id'].apply(lambda x: b_data[b_data['id'] == x]['city'].unique()[0])
        bowl_data['Start Date'] = bowl_data['id'].apply(lambda x: b_data[b_data['id'] == x]['date'].unique()[0])
        bowl_data['Type'] = 'IPL'
        bowl_data['Econ'] = round(bowl_data['batsman_runs'] * 6 / bowl_data['BF'], 2)
        bowl_data['Overs'] = bowl_data['BF'].apply(lambda x: (int(x / 6) + (x % 6) * .1))
        bowl_data = bowl_data.drop(['id', 'BF'], 1)
        bowl_data = bowl_data.rename(columns={'batsman_runs': 'Runs', 'is_wicket': 'Wkts'})
    else:
        bowl_data = pd.DataFrame(columns=['Overs', 'Runs', 'Wkts', 'Econ', 'Inns', 'Opposition',
                                          'Ground', 'Start Date', 'Type'])
    player_with_ball = player_with_ball.append(bowl_data, ignore_index=True)
    player_with_ball = player_with_ball.sort_values("Start Date").reset_index()

    # Bowling Additional Data
    # Avg_Eco, Wkts-1, Runs-1, Overs-1
    if len(player_with_ball) > 0:
        player_with_ball['Avg_Eco'] = 0
        player_with_ball['Wkts-1'] = 0
        player_with_ball['Runs-1'] = 0
        player_with_ball['Overs-1'] = 0

        for i in range(1, len(player_with_ball)):
            if i > 5:
                player_with_ball.loc[i, 'Avg_Eco'] = round(player_with_ball.loc[i - 5:i - 1, 'Econ'].sum() / 5, 2)
            else:
                player_with_ball.loc[i, 'Avg_Eco'] = round(player_with_ball.loc[:i - 1, 'Econ'].sum() / (i), 2)
            player_with_ball.loc[i, 'Wkts-1'] = player_with_ball.loc[i - 1, 'Wkts']
            player_with_ball.loc[i, 'Runs-1'] = player_with_ball.loc[i - 1, 'Runs']
            player_with_ball.loc[i, 'Overs-1'] = player_with_ball.loc[i - 1, 'Overs']

    player_with_ball.to_csv(os.path.join(bowling_directory, player) + ".csv")
    return player_with_ball

def batting_predictor(player, oppo, grd, inn, type_):
    """
    player: Player Name, oppo: Opposition, grd: Ground, inn: Inning, type_: Type of Match

    """
    try:
        batting = pd.read_csv(os.path.join(batting_directory, player) + ".csv")
    except:
        batting = battingstats(player)
    # Batting Predictor
    if len(batting) >= 20:
        le_ground = LabelEncoder()
        le_oppo = LabelEncoder()
        le_type = LabelEncoder()
        batting['Ground'] = batting['Ground'].fillna("UNK")
        batting['Ground'] = le_ground.fit_transform(batting['Ground'])
        batting['Opposition'] = batting['Opposition'].fillna("UNK")
        batting['Opposition'] = le_oppo.fit_transform(batting['Opposition'])
        batting['Type'] = le_type.fit_transform(batting['Type'])

        # Data to be taken from previous records

        avg_9 = batting.loc[len(batting) - 9:len(batting) - 1, 'Runs'].sum()
        bf_avg_9 = round(batting.loc[len(batting) - 9:len(batting) - 1, 'BF'].sum() / 9, 2)
        avg = round(batting.loc[:len(batting) - 1, 'Runs'].sum() / batting.loc[:len(batting) - 1, 'Out'].sum(), 2)
        bf_1 = batting.loc[len(batting) - 1, 'BF-1']
        runs_1 = batting.loc[len(batting) - 1, 'Runs-1']
        sr_1 = batting.loc[len(batting) - 1, 'SR-1']

        # Conversion of String Data to Numeric by Label Encoder
        try:
            labelled_type = le_type.transform([type_])
        except:
            le_type.classes_ = np.append(le_type.classes_, type_)
            labelled_type = le_type.transform([type_])
        try:
            labelled_grd = le_ground.transform([grd])
        except:
            le_ground.classes_ = np.append(le_ground.classes_, grd)
            labelled_grd = le_ground.transform([grd])
        try:
            labelled_oppo = le_oppo.transform([oppo])
        except:
            le_oppo.classes_ = np.append(le_oppo.classes_, oppo)
            labelled_oppo = le_oppo.transform([oppo])

        # Ball Prediction
        X_balls = batting[
            ['Opposition', 'Ground', 'Inns', 'Type', 'Avg_9', 'BF_Avg_9', 'Avg', 'BF-1', 'Runs-1', 'SR-1']].values
        y_balls = batting['BF'].values

        X_train, X_test, y_train, y_test = train_test_split(X_balls, y_balls, test_size=0.1, random_state=0)

        model1 = RandomForestRegressor(n_estimators=450, random_state=12)
        model1.fit(X_train, y_train)

        predicted_balls_played = model1.predict(
            [[labelled_oppo, labelled_grd, inn, labelled_type, avg_9, bf_avg_9, avg, bf_1, runs_1, sr_1]])

        # This don't provide enough accuracy for now ...
        batting['Predicted BF'] = model1.predict(X_balls)
        batting['Predicted BF'] = batting['Predicted BF'].apply(lambda x: int(x))

        X_runs = batting[['Predicted BF', 'BF-1', 'Runs-1', 'SR-1', 'Type']]
        y_runs = batting['Runs'].values

        X_train, X_test, y_train, y_test = train_test_split(X_runs, y_runs, test_size=0.1, random_state=5)

        model2 = RandomForestRegressor(random_state=9)
        model2.fit(X_train, y_train)

        # Accuracy above 70
        return int(model2.predict([[predicted_balls_played, bf_1, runs_1, sr_1, labelled_type]]))
    else:
        return "NA"


def bowling_predictor(player, oppo, grd, inn, type_):
    """
    player: Player Name, oppo: Opposition, grd: Ground, inn: Inning, type_: Type of Match

    """
    try:
        bowling = pd.read_csv(os.path.join(bowling_directory, player) + ".csv")
    except:
        bowling = bowlingstats(player)

    if len(bowling) > 20:
        le_ground = LabelEncoder()
        le_oppo = LabelEncoder()
        le_type = LabelEncoder()
        bowling['Ground'] = bowling['Ground'].fillna("UNK")
        bowling['Ground'] = le_ground.fit_transform(bowling['Ground'])
        bowling['Opposition'] = bowling['Opposition'].fillna("UNK")
        bowling['Opposition'] = le_oppo.fit_transform(bowling['Opposition'])
        bowling['Type'] = le_type.fit_transform(bowling['Type'])

        # Conversion of String Data to Numeric by Label Encoder
        try:
            labelled_type = le_type.transform([type_])
        except:
            le_type.classes_ = np.append(le_type.classes_, type_)
            labelled_type = le_type.transform([type_])
        try:
            labelled_grd = le_ground.transform([grd])
        except:
            le_ground.classes_ = np.append(le_ground.classes_, grd)
            labelled_grd = le_ground.transform([grd])
        try:
            labelled_oppo = le_oppo.transform([oppo])
        except:
            le_oppo.classes_ = np.append(le_oppo.classes_, oppo)
            labelled_oppo = le_oppo.transform([oppo])

        # Data from previous matches Avg_Eco, Wkts-1, Runs-1, Overs-1
        avg_econ = round(bowling.loc[len(bowling) - 5:len(bowling) - 1, 'Econ'].sum() / 5, 2)
        wkts_1 = bowling.loc[len(bowling) - 1, 'Wkts']
        runs_1 = bowling.loc[len(bowling) - 1, 'Runs']
        overs_1 = bowling.loc[len(bowling) - 1, 'Overs']

        if (type_ == 'T20I') or (type_ == 'IPL'):
            overs = 4.0

        # Wickets Predictions
        X = bowling[['Inns', 'Opposition', 'Ground', 'Type', 'Avg_Eco', 'Wkts-1', 'Runs-1', 'Overs-1']]
        y = bowling['Wkts'].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=1)

        model3 = RandomForestRegressor(n_estimators=150, criterion="mae", random_state=6)
        model3.fit(X_train, y_train)

        return round(
            model3.predict([[inn, labelled_oppo, labelled_grd, labelled_type, avg_econ, wkts_1, runs_1, overs]])[0], 0)
