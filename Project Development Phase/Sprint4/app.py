import numpy as np
import csv
import sys
import requests
import pickle

from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import dotenv_values

config = dotenv_values(".env")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

API_KEY = config['API_KEY']

token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
                                                                                 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + mltoken}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/', methods=['GET'])
def index():
    if session.get('logged_in'):
        return render_template('home.html')
    else:
        return render_template('index.html', message="Welcome!")


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db.session.add(
                User(username=request.form['username'], password=request.form['password']))
            db.session.commit()
            return redirect(url_for('login'))
        except:
            return render_template('index.html', message="User Already Exists")
    else:
        return render_template('register.html')


@app.route('/results/', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        kms_driven = request.form['Kilometers_Driven']
        fuel_type = request.form['Fuel_Type']
        transmission = request.form['Transmission']
        engine_cc = request.form['Engine_CC']
        power = request.form['Power']
        seats = request.form['Seats']
        carprice = request.form['Price']
        t1 = [[int(kms_driven), str(fuel_type), str(transmission), int(
            engine_cc), int(power), int(seats), int(carprice), ]]
        # t1 = [[1, "Maruti Swift VDI", "Maruti", "Delhi", 2014, int(kms_driven), str(fuel_type), str(transmission), "First", int(
        # engine_cc), int(power), int(seats), int(carprice), ]]
        payload_scoring = {"input_data": [{"field": [
            ["Kilometers_Driven", "Fuel_Type", "Transmission", "Engine CC", "Power", "Seats", "Price"]], "values": t1}]}
        response_scoring = requests.post('https://eu-de.ml.cloud.ibm.com/ml/v4/deployments/acb7733e-5447-4b2d-b358-312456c41d1f/predictions?version=2022-11-17', json=payload_scoring,
                                         headers={'Authorization': 'Bearer ' + mltoken})
        print(type(response_scoring))
        print("Scoring response")
        prediction = response_scoring.json()
        # ["predictions"][0]["values"][0][0]
        print(prediction)
        new_prediction = None
        if 'errors' in prediction:
            loaded_model = pickle.load(open('regression2.pkl', 'rb'))
            if(t1[0][1] == 'CNG'):
                t1[0][1] = 0
            elif(t1[0][1] == 'Diesel'):
                t1[0][1] = 1
            elif(t1[0][1] == 'Petrol'):
                t1[0][1] = 2
            elif(t1[0][1] == 'LPG'):
                t1[0][1] = 3
            elif(t1[0][1] == 'Electric'):
                t1[0][1] = 4

            if(t1[0][2] == 'Manual'):
                t1[0][2] = 0
            elif(t1[0][2] == 'Automatic'):
                t1[0][2] = 1
            t2 = [[25000, 0, 0, 1200, 130, 4, 6]]
            new_prediction = loaded_model.predict(t2)
            # new_prediction = new_prediction[0]
        else:
            new_prediction = prediction["predictions"][0]["values"][0][0]
        final_prediction = round(new_prediction, 2)

        suggested_cars = []
        csv_file = csv.reader(open('CARS_2.csv', "r"), delimiter=",")
        for row in csv_file:
            if(row[12] == 'Mileage Km/L'):
                continue
            else:
                num1 = float(final_prediction)
                num2 = float(row[12])
                if abs(num1-num2) <= 1:
                    suggested_cars.append(row[1])
                    # print(row[1])
        suggested_cars = set(suggested_cars)

        return render_template('results.html', z=str(final_prediction), car_list = suggested_cars)
    #     try:
    #         db.session.add(User(username=request.form['username'], password=request.form['password']))
    #         db.session.commit()
    #         return redirect(url_for('login'))
    #     except:
    #         return render_template('index.html', message="User Already Exists")
    # else:
    #     return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u = request.form['username']
        p = request.form['password']
        data = User.query.filter_by(username=u, password=p).first()
        if data is not None:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('index.html', message="Incorrect Details")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))


if(__name__ == '__main__'):
    app.secret_key = "ThisIsNotASecret:p"
    with app.app_context():
        db.create_all()
    app.run(debug=config['DEBUG'])
