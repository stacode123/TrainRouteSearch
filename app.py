#Import Libraries
import warnings
from asyncio import Timeout
from collections import defaultdict

from datetime import time
import datetime
import signal
import pandas as pd

from flask import Flask, render_template, request
from datetime import datetime, timedelta

from pandas.core.common import maybe_iterable_to_list
startdate = datetime.today()
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
        train_data[(train_name, train_number)].append((station, datetime.combine(datetime.today(),arr_time), datetime.combine(datetime.today(),dep_time) ))
    train_data[(train_name, train_number)].append((trainslss[(train_name, train_number)][1],datetime.combine(datetime.today(),trainslss[(train_name, train_number)][0]),datetime.combine(datetime.today(),trainslss[(train_name, train_number)][0])))
print(train_data)

import heapq
from datetime import datetime, timedelta

from collections import defaultdict
from datetime import datetime, timedelta


class Connection:
    def __init__(self, departure_station, arrival_station, departure_time, arrival_time, train_info):
        self.departure_station = departure_station
        self.arrival_station = arrival_station
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.train_info = train_info  # Tuple containing (traindata, trainNumber)


class Connection:
    def __init__(self, departure_station, arrival_station, departure_time, arrival_time, train_info):
        self.departure_station = departure_station
        self.arrival_station = arrival_station
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.train_info = train_info  # Tuple containing (traindata, trainNumber)


def connection_scan_algorithm_multiple_paths(connections, start_station, start_time, end_station, max_options=10,
                                             time_threshold=timedelta(minutes=10)):
    # Initialize earliest arrival times with lists of arrival options
    far_future = datetime.max
    earliest_arrival = defaultdict(lambda: [])
    earliest_arrival[start_station].append((start_time, None))  # Start with start_time and no connection

    # Backtracking dictionary to reconstruct multiple paths
    backtrack = defaultdict(lambda: [])

    # Process each connection in chronological order
    for connection in connections:
        # For each arrival option at the departure station
        for (arr_time, _) in earliest_arrival[connection.departure_station]:
            # If this connection departs after the earliest arrival time, it’s usable
            if arr_time <= connection.departure_time:
                new_arrival_time = connection.arrival_time

                # Check if we already have similar options at the arrival station
                is_similar = any(
                    abs((new_arrival_time - existing_time).total_seconds()) < time_threshold.total_seconds()
                    for (existing_time, _) in earliest_arrival[connection.arrival_station])

                # Only add if it’s a sufficiently different arrival time
                if not is_similar:
                    # Add the new arrival option
                    earliest_arrival[connection.arrival_station].append((new_arrival_time, connection))
                    backtrack[connection.arrival_station].append((connection, arr_time))

                    # Maintain only top `max_options` sorted by earliest arrival
                    earliest_arrival[connection.arrival_station].sort()
                    if len(earliest_arrival[connection.arrival_station]) > max_options:
                        earliest_arrival[connection.arrival_station] = earliest_arrival[connection.arrival_station][
                                                                       :max_options]

    # Reconstruct multiple paths, ensuring paths end at end_station
    paths = []
    for (final_arrival_time, _) in earliest_arrival[end_station]:
        path = []
        current_station = end_station
        current_time = final_arrival_time

        while current_station != start_station:
            # Try to find the connection leading to the current station and time
            try:
                connection, arr_time = next((conn, arr_time) for conn, arr_time in backtrack[current_station] if
                                            conn.arrival_time == current_time)
            except StopIteration:
                # Break out of the loop if no matching connection is found
                path = None
                break

            path.append(connection)
            current_station = connection.departure_station
            current_time = arr_time

            # Stop if we've reached the start station to prevent further backtracking
            if current_station == start_station:
                break

        # Only add valid paths that end at the destination
        if path and path[0].arrival_station == end_station:
            # Reverse path to go from start to end
            paths.append(list(reversed(path)))


    formated_routes = []
    for idx, path in enumerate(paths, 1):
        formatted_path = []
        for conn in path:
            if len(formatted_path) > 0 and conn.train_info[1] == formatted_path[-1]["train number"]:
                formatted_path[-1]["arrival_station"] = conn.arrival_station
                formatted_path[-1]["arrival_time"] = conn.arrival_time.strftime("%H:%M")
            else:
                formatted_path.append({
                    "train": conn.train_info[0],
                    "train number": conn.train_info[1],
                    "departure_station": conn.departure_station,
                    "departure_time": conn.departure_time.strftime("%H:%M"),
                    "arrival_station": conn.arrival_station,
                    "arrival_time": conn.arrival_time.strftime("%H:%M")
                })
        formated_routes.append(formatted_path)
    print(formated_routes)
    return formated_routes


def convert_dict_to_connections(train_dict):
    connections = []

    for (trainData, trainNumber), stations in train_dict.items():
        for i in range(len(stations) - 1):
            # Extract data for consecutive stations
            departure_station, _, departure_time = stations[i]
            arrival_station, arrival_time, _ = stations[i + 1]

            # Create a Connection instance
            connection = Connection(
                departure_station=departure_station,
                arrival_station=arrival_station,
                departure_time=departure_time,
                arrival_time=arrival_time,
                train_info=(trainData, trainNumber)
            )

            # Add to connections list
            connections.append(connection)

    return connections
connections = convert_dict_to_connections(train_data)

# formatted_routes = []
# for total_time, route in unique_routes:
#     formatted_route = []
#     if route:
#         current_train = route[0][1]
#         start_station = route[0][2]
#         start_time = route[0][4]
#         end_station, end_time = route[0][3], route[0][5]
#
#         for leg in route[1:]:
#             train_name, train_number, dep_station, arr_station, dep_time, arr_time = leg
#             if train_number == current_train:
#                 end_station = arr_station
#                 end_time = arr_time
#             else:
#                 formatted_route.append({
#                     "train": f"{route[0][0]} ({current_train})",
#                     "departure_station": start_station,
#                     "departure_time": start_time,
#                     "arrival_station": end_station,
#                     "arrival_time": end_time
#                 })
#                 current_train = train_number
#                 start_station = dep_station
#                 start_time = dep_time
#                 end_station, end_time = arr_station, arr_time
#
#         formatted_route.append({
#             "train": f"{route[-1][0]} ({current_train})",
#             "departure_station": start_station,
#             "departure_time": start_time,
#             "arrival_station": end_station,
#             "arrival_time": end_time
#         })
#     formatted_routes.append((total_time, formatted_route))
#
# return formatted_routes

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
        found_routes = connection_scan_algorithm_multiple_paths(connections, start, datetime.combine(startdate,departure_time),  goal)
        newtime = timedelta(minutes=30)
        while found_routes == []:
            newtime = newtime + timedelta(minutes=30)
            found_routes = connection_scan_algorithm_multiple_paths(connections, start, datetime.combine(startdate,departure_time)+newtime,  goal)
            if newtime > timedelta(hours=24):
                break
        route_options = found_routes
        result = "No route found."

    return render_template('index.html', stations=stations, route_options=route_options, result=result)




if __name__ == '__main__':
    app.run(debug=True)
