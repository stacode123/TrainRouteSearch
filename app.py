#Import Libraries
import warnings
from datetime import time
from typing import Dict, Any, List, Tuple
import heapq
import pandas as pd


from flask import Flask, render_template, request
from datetime import datetime, timedelta
warnings.simplefilter(action='ignore', category=FutureWarning)
app = Flask(__name__)
def ReadExcel(sheet):
    df = pd.read_excel("rj.xlsx", sheet_name=sheet)
    s=False
    index = df[(df.iloc[:, 0] == "Informacja o pociągu") | (df.iloc[:, 0] == "Train Info")].index[0]
    df = df.iloc[index:].reset_index(drop=True)
    s = False
    empty_row = pd.DataFrame([[None] * len(df.columns)], columns=df.columns)
    #df = pd.concat([empty_row, df], )
    index = df[(df.iloc[:, 0] == "Koniec") | (df.iloc[:, 0] == "End")].index[0]
    df = df.iloc[:index].reset_index(drop=True)
    df.fillna(method='ffill', inplace=True)
    return df
def sort_key(item):
    if item['departure_time'] == '?':
        return time.max  # Use the maximum time value for 'KOLIZJA'
    return item['departure_time']
def sort_key2(item):
    if isinstance(item, time):
        a = item.hour*60+item.minute
        return a
    return 0
def sort_key3(item):
    return item['departure_time']
def sort_key4(item):
    if isinstance(item, time):
        a = item.hour*60+item.minute
        if a <= 720:
            return a + 1440
        else:
            return a
    return 0
stations = []
sheet= pd.ExcelFile("rj.xlsx")
sheets = sheet.sheet_names
per = len(sheets)
it = 0
print("Importing Data")
# Extract Station Names
for i in sheets:
    it+=1
    print(f"{(it / per) * 100:.2f}%")
    if "LK" in i:
        df = ReadExcel(i)
        df.fillna(method='ffill', inplace=True)
        column_a_data = df['Unnamed: 0'].tolist()
        stations = stations + column_a_data
# Remove station names that are not actual stations
stations = list(set(stations) - {" nan"})
stations = list(set(stations) - {"nan"})
stations = list(set(stations) - {"Informacja o pociągu"})
stations = list(set(stations) - {"Train Info"})
stations = list(set(stations) - {"Warszawa\xa0Zachodnia"})
# Populate Departure and Arrival Dictionaries
Departures =  {i: [] for i in stations}
Arrivals =  {i: [] for i in stations}

print("Parsing Data")
per = 2*len(sheets)
it = 0
# Extract Departure Times
for i in sheets:
    it+=1
    print(f"{(it / per) * 100:.2f}%")
    if "LK" in i:
        df = ReadExcel(i)
        df.fillna(method='ffill', inplace=True) # Drop rows where all elements are NaN

        train_details = df.iloc[:2].to_dict('records')
        for x in range(2,df.shape[1]):
            for index, row in df.iloc[2:].iterrows():
                station = row['Unnamed: 0']
                if station in Departures and row['Unnamed: 1'] == "odj.":
                    departure_time = row['Unnamed: {}'.format(x)]
                    if {'departure_time': departure_time,'train_details': [train_details[0]["Unnamed: {}".format(x)],train_details[1]["Unnamed: {}".format(x)]]} not in Departures[station]:
                        if departure_time != '<' and departure_time != '|' and departure_time != '?' and departure_time == departure_time:
                           Departures[station].append({'departure_time': departure_time,'train_details': [train_details[0]["Unnamed: {}".format(x)],train_details[1]["Unnamed: {}".format(x)]]})

# Extract Arrival Data
for i in sheets:
    it+=1
    print(f"{(it / per) * 100:.2f}%")
    if "LK" in i:
        df = ReadExcel(i)
        df.fillna(method='ffill', inplace=True) # Drop rows where all elements are NaN

        train_details = df.iloc[:2].to_dict('records')
        for x in range(2,df.shape[1]):
            for index, row in df.iloc[2:].iterrows():
                station = row['Unnamed: 0']
                if station in Arrivals and row['Unnamed: 1'] == "przyj." or row['Unnamed: 1'] == "przj." and station != "Warszawa\xa0Zachodnia":
                    departure_time = row['Unnamed: {}'.format(x)]
                    if {'departure_time': departure_time,'train_details': [train_details[0]["Unnamed: {}".format(x)],train_details[1]["Unnamed: {}".format(x)]]} not in Arrivals[station]:
                        if departure_time != '<' and departure_time != '|' and departure_time == departure_time:
                            Arrivals[station].append({'departure_time': departure_time,'train_details': [train_details[0]["Unnamed: {}".format(x)],train_details[1]["Unnamed: {}".format(x)]]})


trains = {}   #Dictionary of all stations and departure times for each train
trainsls = {} #Dictionary of all stations and arrival times for each train
trainslss = {} #Dictionary of the last station and arrival time for each train
#Generate train Dictionary
for i in Departures:
    for x in Departures[i]:
        trains[tuple(x['train_details'])] = []
        trainsls[tuple(x['train_details'])] = []
        trainslss[tuple(x['train_details'])] = []
#Sort the Dictionary
for key in trains:
    trains[key] = list(set(trains[key]))
for key in trainsls:
    trainsls[key] = list(set(trainsls[key]))
for key in trainslss:
    trainslss[key] = list(set(trainslss[key]))


#Itterate through all the stations and add the stations and departure times to the dictionary
for i in Departures:
    for x in Departures[i]:
        trains[tuple(x['train_details'])].append(i) # Append the station to the train
        trains[tuple(x['train_details'])].append(x['departure_time']) # Append the departure time to the train #
#Sort the dictionary by departure time
trainssort = {}
for key in trains:
    a = max([trains[key][i + 1] for i in range(0, len(trains[key]), 2)])
    b = min([trains[key][i + 1] for i in range(0, len(trains[key]), 2)])
    if sort_key2(a) - sort_key2(b) >= 720:
        trainssort[key] = sorted([(trains[key][i], trains[key][i + 1]) for i in range(0, len(trains[key]), 2)],key=lambda x: sort_key4(x[1]))
    else:
        trainssort[key] = sorted([(trains[key][i], trains[key][i + 1]) for i in range(0, len(trains[key]), 2)],key=lambda x: sort_key2(x[1]))

#Append Trains to trainsls
for i in Arrivals:
    for x in Arrivals[i]:
        if tuple(x['train_details']) not in trainsls:
            trainsls[tuple(x['train_details'])] = []
#Itterate through all the stations and add the stations and arrival times to the dictionary
for i in Arrivals:
    for x in Arrivals[i]:
        trainsls[tuple(x['train_details'])].append(i) # Append the station to the train
        trainsls[tuple(x['train_details'])].append(x['departure_time'])  # Append the departure time to the train

#Remove Duplicate Trains
for key in trainslss:
    trainslss[key] = list(set(trainslss[key]))

#Find Last Station for all trains and append to trainslss
for i in trainslss:
    a = max([trainsls[i][x + 1] for x in range(0, len(trainsls[i]), 2)])
    b = min([trainsls[i][x + 1] for x in range(0, len(trainsls[i]), 2)])
    if sort_key2(a) - sort_key2(b) >= 720:
        sort = (sorted(trainsls[i], key=sort_key4)[-1],trainsls[i][trainsls[i].index(sorted(trainsls[i], key=sort_key4)[-1])-1])
    else:
        sort = (sorted(trainsls[i], key=sort_key2)[-1],trainsls[i][trainsls[i].index(sorted(trainsls[i], key=sort_key2)[-1])-1])
    if trainslss[i] != sort:
        trainslss[i] = sort
train_data = {}



print(trainslss)
print(trains)
for (train_name, train_number), schedule in trainssort.items():
    train_data[(train_name, train_number)] = []
    for station, dep_time in schedule:
        arr_time = trainsls[(train_name, train_number)][trainsls[(train_name, train_number)].index(station) + 1] if station in trainsls[(train_name, train_number)] else datetime.time(datetime.combine(datetime.today(),dep_time)-timedelta(minutes=1))
        train_data[(train_name, train_number)].append((station, dep_time.strftime('%H:%M'), arr_time.strftime('%H:%M') if isinstance(arr_time, time) else dep_time.strftime('%H:%M')))
    train_data[(train_name, train_number)].append((trainslss[(train_name, train_number)][1],trainslss[(train_name, train_number)][0].strftime('%H:%M'),trainslss[(train_name, train_number)][0].strftime('%H:%M')))
print(train_data)

import heapq
from datetime import datetime, timedelta


def time_difference_in_minutes(start_time, end_time):
    """Calculate the difference in minutes between two time objects, handling next-day wrap-around."""
    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)
    if end_dt < start_dt:  # If end time is past midnight, adjust for next day
        end_dt += timedelta(days=1)
    return int((end_dt - start_dt).total_seconds() / 60)


def dijkstra_find_routes(start, goal, departure_time, buffer_time, max_options=3):
    # Convert buffer time to integer minutes
    buffer_delta = buffer_time

    # Priority queue: stores (total_travel_time, current_station, current_time, path_so_far)
    queue = [(0, start, departure_time, [])]

    # Best known travel times to each station
    best_times = {start: 0}

    # Store multiple valid paths to the destination
    found_routes = []

    while queue and len(found_routes) < max_options:
        # Get the route with the shortest travel time so far
        total_travel_time, current_station, current_time, path = heapq.heappop(queue)

        # If we reached the goal, add the route to found_routes
        if current_station == goal:
            found_routes.append((total_travel_time, path))
            continue

        # Explore all possible train options from the current station
        for (train_name, train_number), schedule in train_data.items():
            for i in range(len(schedule) - 1):
                from_station, dep_time_str, arr_time_str = schedule[i]
                to_station, next_dep_time_str, next_arr_time_str = schedule[i + 1]

                # Only consider trains that leave from the current station
                if from_station != current_station:
                    continue

                # Parse times for departure and arrival as time objects
                dep_time = datetime.strptime(dep_time_str, "%H:%M").time()
                arr_time = datetime.strptime(next_arr_time_str, "%H:%M").time()

                # Check if the current path’s arrival time plus buffer time allows for this departure
                if time_difference_in_minutes(current_time, dep_time) >= buffer_delta:
                    # Calculate travel time to this new station
                    travel_time = time_difference_in_minutes(dep_time, arr_time)
                    waiting_time = time_difference_in_minutes(current_time, dep_time)
                    new_total_travel_time = total_travel_time + travel_time + waiting_time

                    # If we found a faster way to reach this station, add to queue
                    if to_station not in best_times or new_total_travel_time < best_times[to_station]:
                        best_times[to_station] = new_total_travel_time
                        new_path = path + [
                            (train_name, train_number, from_station, to_station, dep_time_str, next_arr_time_str)]
                        heapq.heappush(queue, (new_total_travel_time, to_station, arr_time, new_path))

    # Format the found routes as needed
    formatted_routes = []
    for total_time, route in found_routes:
        formatted_route = []
        for train_name, train_number, dep_station, arr_station, dep_time, arr_time in route:
            formatted_route.append({
                "train": f"{train_name} ({train_number})",
                "departure_station": dep_station,
                "departure_time": dep_time,
                "arrival_station": arr_station,
                "arrival_time": arr_time
            })
        formatted_routes.append((total_time, formatted_route))

    return formatted_routes

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    route_options = []
    stations = sorted(set(station for schedule in train_data.values() for station, _, _ in schedule))

    if request.method == 'POST':
        start = request.form['start']
        goal = request.form['goal']
        departure_hour = int(request.form['departure_hour'])
        departure_minute = int(request.form['departure_minute'])
        buffer_time = int(request.form['buffer_time'])  # Get buffer time in minutes
        departure_time = time(departure_hour, departure_minute)  # Convert to datetime.time

        # Get multiple route options
        found_routes = dijkstra_find_routes(start, goal, departure_time, buffer_time, max_options=3)
        if found_routes:
            for total_time, route in found_routes:
                route_options.append({
                    "total_time": total_time,
                    "legs": route
                })
        result = "No route found."

    return render_template('index.html', stations=stations, route_options=route_options, result=result)




if __name__ == '__main__':
    app.run(debug=True)
