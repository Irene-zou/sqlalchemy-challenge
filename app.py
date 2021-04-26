from flask import Flask, jsonify
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
import datetime as dt

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite", echo=False)

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

app = Flask(__name__)

@app.route("/")
def home():
    print("Server received request for 'Home' page...")
    #text returned to be in HTML since that's what the web page can render
    return "<strong>Available routes:</strong>\
            <ul>\
            <li><i>/api/v1.0/precipitation</i></li>\
            <li><i>/api/v1.0/stations</i></li>\
            <li><i>/api/v1.0/tobs</i></li>\
            <li><i>/api/v1.0/<strong>[start]</strong></i></li>\
            <li><i>/api/v1.0/<strong>[start]</strong>/<strong>[end]</strong></i></li>\
            </ul>"

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'precipitation' endpoint...")
    most_active_stations = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all() #getting the most active station IDs
    most_active_single_station = most_active_stations[0][0] #list of lists -- getting the 0th element of the outer list and then the 0th element of the inner list, i.e. the single most active station ID
    this_station_most_recent_date = session.query(Measurement.date).filter(Measurement.station == most_active_single_station).order_by(Measurement.date.desc()).first()
    intDateListStation = this_station_most_recent_date[0].split('-') #splitting the formatted date to a list
    most_recent_query_date_station = dt.date(int(intDateListStation[0]), int(intDateListStation[1]), int(intDateListStation[2])) #converting date list to a date object
    query_date = most_recent_query_date_station - dt.timedelta(days=365) #getting the date from a year ago
    precipitation_query_results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.station == most_active_single_station).filter(Measurement.date > query_date).order_by(Measurement.date).all() #querying the SQLite DB
    session.close() #closing connection to database

    precipitation_list = [] #list for storing the dictionary
    for date, prcp in precipitation_query_results: #for every date and precipitation value in the query results
        precipitation_dictionary = {} #dictionary used to keep the dates (as keys) and precipitation (as values) separate
        precipitation_dictionary[date] = prcp #for each row of the query results, the date will be the dictionary key and the precipitation will be the dictionary value
        precipitation_list.append(precipitation_dictionary) #append the dictionary to the list so later we can jsonify the data

    return jsonify(precipitation_list) #return the JSON representation of the list

@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'stations' endpoint...")
    station_query_results = session.query(Station.station).all() #query for getting all the weather station IDs
    session.close() #closing connection to database
    station_list = []
    for element in station_query_results:
        station_list.append(element[0]) #iterating through the list of lists to get the 0th element of each inner list (station ID)
    return jsonify(station_list) #return the JSON representation of the list

@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for 'tobs' endpoint...")
    most_active_stations = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all() #getting the most active station IDs
    most_active_single_station = most_active_stations[0][0] #list of lists -- getting the 0th element of the outer list and then the 0th element of the inner list, i.e. the single most active station ID
    this_station_most_recent_date = session.query(Measurement.date).filter(Measurement.station == most_active_single_station).order_by(Measurement.date.desc()).first()
    intDateListStation = this_station_most_recent_date[0].split('-') #splitting the formatted date to a list
    most_recent_query_date_station = dt.date(int(intDateListStation[0]), int(intDateListStation[1]), int(intDateListStation[2])) #converting date list to a date object
    query_date = most_recent_query_date_station - dt.timedelta(days=365) #getting the date from a year ago
    #the following query will return the dates and temperature observations of the most active station for the last year of data
    station_date_temp_results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_single_station).filter(Measurement.date > query_date).all()
    session.close() #closing connection to database

    return jsonify(station_date_temp_results)

@app.route("/api/v1.0/<start>")
def startDate(start):
    print("Server received request for 'start' endpoint...")
    most_active_stations = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all() #getting the most active station IDs
    most_active_single_station = most_active_stations[0][0] #list of lists -- getting the 0th element of the outer list and then the 0th element of the inner list, i.e. the single most active station ID
    temperature_data = session.query(Measurement.tobs).filter(Measurement.station == most_active_single_station).filter(Measurement.date >= start).all()
    session.close() #closing connection to database

    temperature_list = []
    for temp in temperature_data:
        temperature_list.append(temp[0]) #getting the 0th element from each inner list to help with formatting
    try:
        min_temp = "min: " + str(min(temperature_list))
        avg_temp = "avg: " + str(round(np.mean(temperature_list),0))
        max_temp = "max: " + str(max(temperature_list))
    except ValueError: #if we get this particular error, the user entered a date that does not have temperature data associated with it
        return jsonify({"error": "There are no temperature entries for this date range."}), 404

    final_temperature_list = []
    final_temperature_list.append([min_temp, avg_temp, max_temp]) #appending the formatted variables to the final list

    return jsonify(final_temperature_list) #return the JSON representation of the final, formatted list

@app.route("/api/v1.0/<start>/<end>")
def startEndDate(start, end):
    most_active_stations = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all() #getting the most active station IDs
    most_active_single_station = most_active_stations[0][0] #list of lists -- getting the 0th element of the outer list and then the 0th element of the inner list, i.e. the single most active station ID
    temperature_data = session.query(Measurement.tobs).filter(Measurement.station == most_active_single_station).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    session.close() #closing connection to database

    temperature_list = []
    for temp in temperature_data:
        temperature_list.append(temp[0]) #getting the 0th element from each inner list to help with formatting
    try:
        min_temp = "min: " + str(min(temperature_list))
        avg_temp = "avg: " + str(round(np.mean(temperature_list),0))
        max_temp = "max: " + str(max(temperature_list))
    except ValueError: #if we get this particular error, the user entered a date that does not have temperature data associated with it
        return jsonify({"error": "There are no temperature entries for this date range."}), 404

    final_temperature_list = []
    final_temperature_list.append([min_temp, avg_temp, max_temp]) #appending the formatted variables to the final list

    return jsonify(final_temperature_list) #return the JSON representation of the final, formatted list

if __name__ == "__main__":
    app.run(debug=True)
