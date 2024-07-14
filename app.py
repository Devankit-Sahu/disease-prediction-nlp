from flask import Flask, request, render_template, redirect, session, flash,jsonify
from dotenv import load_dotenv
import os
import pickle
import pandas as pd
from models import db, User, Appointment
from flask_migrate import Migrate

# load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] =  os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] =  os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

#load model
model = pickle.load(open('disease_condition_reviews.pkl', 'rb'))
#load vectorizer
vectorizer = pickle.load(open('vectorizer.pkl', 'rb'))
#load dataset
df = pd.read_csv('drugsComTest_raw.csv')

def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and  user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            if user.role == 'user':
                return redirect('/')
            else:
                return redirect('/dashboard')
        else:
            flash('Login unsuccessful. Check email and password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        speciality = request.form['speciality']
        available_time = request.form['available_time'] 
        new_user = User(name=name, email=email, role=role,password=password)

        if role == 'doctor':
            new_user.speciality = speciality
            new_user.available_time = available_time
        
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/logout',methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect('/login')

@app.route('/')
def home():
    if session.get('user_id'):
        # doctors = User.query.filter_by(role='doctor').all()
        return render_template('home.html')
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if session.get('user_id') and session.get('role') == 'doctor':
        doctor_id = session['user_id']
        appointments = db.session.query(Appointment, User).join(User, Appointment.user_id == User.id).filter(Appointment.doctor_id == doctor_id).all()
        return render_template('dashboard.html',appointments=appointments)
    return redirect('/login')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/doctors', methods=['GET'])
def doctors():
    doctors = User.query.filter_by(role='doctor').all()
    return render_template('doctors.html',doctors=doctors)

@app.route('/predict', methods=['POST'])
def predict():
    review = request.form['review']
        
    review_transformed = vectorizer.transform([review])
    
    prediction = model.predict(review_transformed)[0]
    top_drugs = get_top_drugs(prediction,df)
    return render_template('result.html', prediction=prediction,top_drugs=top_drugs)

@app.route('/appointments', methods=['GET'])
def appointments():
    if session.get('user_id'):
        user_id = session['user_id']
        appointments = db.session.query(Appointment, User).join(User, Appointment.doctor_id == User.id).filter(Appointment.user_id == user_id).all()
        return render_template('appointments.html', appointments=appointments)
    return redirect('/login')

@app.route('/create_appointment', methods=['POST'])
def create_appointment():
    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'User not logged in!'}), 401
        
        doctor_id = request.form.get('doctor_id')
        date = request.form.get('date')
        time = request.form.get('time')

        if not doctor_id or not date or not time:
            return jsonify({'message': 'Incomplete data!'}), 400

        new_appointment = Appointment(user_id=user_id, doctor_id=doctor_id, date=date, time=time)

        db.session.add(new_appointment)
        db.session.commit()
        return redirect('/appointments')

@app.route('/update_appointment_status/<int:id>', methods=['POST'])
def update_appointment_status(id):
    appointment = Appointment.query.get(id)
    apointment_status = request.form.get('status')
    if not appointment:
        return jsonify({'message': 'Appointment not found!'}), 404
    appointment.status = apointment_status
    db.session.commit()
    return redirect('/dashboard')

@app.route('/delete_appointment/<int:id>', methods=['POST'])
def delete_appointment(id):
    appointment = Appointment.query.get(id)
    if not appointment:
        return jsonify({'message': 'Appointment not found!'}), 404
    db.session.delete(appointment)
    db.session.commit()
    return redirect('/appointments')

def get_top_drugs(prediction, df):
    filtered_data = df[df['condition'] == prediction]
    top_drugs = (filtered_data.groupby('drugName')
                              .agg({'rating': 'mean'})
                              .sort_values('rating', ascending=False)
                              .head(20)
                              .reset_index())
    return top_drugs.to_dict(orient='records')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
