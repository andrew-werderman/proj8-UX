# Brevet Flask Application
# Author: Andrew Werderman

import os
import flask
from flask import Flask, redirect, url_for, request, render_template
from pymongo import MongoClient
from acp_times import open_time, close_time  # Brevet time calculations

import arrow  # Replacement for datetime, based on moment.js
import config
import logging

app = Flask(__name__)
CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY

client = MongoClient('mongodb://mongo:27017/')
db = client['brevetdb']
collection = db['brevet']

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    collection.delete_many({})
    return render_template('calc.html')


@app.route('/db')
def db():
    _controls = collection.find()
    controls = []
    for ctrl in _controls:
        controls.append({
            'control_km': ctrl['control_km'],
            'control_location': ctrl['control_location'],
            'open_time': ctrl['open_time'],
            'close_time': ctrl['close_time']
        })
    return render_template('db.html', items=controls)


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] = flask.url_for("index")
    return render_template('404.html'), 404

###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")

    # Get input values 
    km = request.args.get('km', 999, type=float)
    brev_dist_km = request.args.get('brev_dist_km', 300, type=int)
    start_date = request.args.get('start_date', '2018-01-19', type=str)
    start_time = request.args.get('start_time', '16:00:00', type=str)

    # Combine date/time into correct format
    dateTime = '{} {}'.format(start_date, start_time)
    brev_start_time = arrow.get(dateTime, 'YYYY-MM-DD HH:mm')
    
    # Calculate open and close times
    open_times = open_time(km, brev_dist_km, brev_start_time)
    close_times = close_time(km, brev_dist_km, brev_start_time)
    result = {"open": open_times.for_json(), "close": close_times.for_json()}

    return flask.jsonify(result=result)


@app.route('/_submit_to_db', methods=['POST'])
def _submit_to_db():
    brevet = []
    numItems = 0
    collection.delete_many({}) # Clear out all current inputs

    # Collect brevet data from POST (return type: string)
    control_kms = request.form.getlist('km')
    control_locs = request.form.getlist('location')
    open_times = request.form.getlist('open')
    close_times = request.form.getlist('close')
    
    for i, item in enumerate(open_times):
        # Invalid input handled on page, OPEN_TIME field will be empty string
        if (item == ''):
            continue
        control_doc = {
            'control_km': int(control_kms[i]),
            'control_location': control_locs[i],
            'open_time': open_times[i],
            'close_time': close_times[i]
        }
        brevet.append(control_doc)
        numItems += 1

    if (brevet == []):
        result = {'message': 'Empty Brevet', 'num': numItems}
    else: 
        # Sort brevet and insert it into the db
        brevet.sort(key=lambda ctrl: ctrl['control_km'])
        collection.insert(brevet)
        result = {'message': 'A-OK', 'num': numItems}

    return flask.jsonify(result=result)


@app.route('/_display_db')
def _display_db():
    result = url_for('db')
    return flask.jsonify(result=result)

#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(
        host='0.0.0.0',
        port=CONFIG.PORT,
        debug=True,
        extra_files = [
            './templates/calc.html',
            './templates/db.html'
        ])


