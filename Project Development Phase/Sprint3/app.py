import numpy as np

import requests

from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

API_KEY = "fbxfE8KinT0zcp5iFQn0Khh_xndwV2MEDSInZSPwuQ1m"
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
        response_scoring = requests.post('https://eu-de.ml.cloud.ibm.com/ml/v4/deployments/50de7571-dc70-4a04-ac09-022ba9a6ed47/predictions?version=2022-11-17', json=payload_scoring,
                                         headers={'Authorization': 'Bearer ' + mltoken})
        print("Scoring response")
        prediction = response_scoring.json()["predictions"][0]["values"][0][0]
        print(prediction)
        final_prediction = round(prediction, 2)
        return render_template('results.html', z=str(final_prediction))
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
    app.run(debug=True)
