from flask import Flask, request, render_template, redirect, session, flash
from dotenv import load_dotenv
import os
import pickle
import pandas as pd
from models import db, User

# load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] =  os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] =  os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

#load model
model = pickle.load(open('disease_condition_reviews.pkl', 'rb'))
model1 = pickle.load(open('disease_prediction.pkl', 'rb'))
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
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Login unsuccessful. Check email and password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        new_user = User(name=name,email=email, password=password)
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
        return render_template('home.html')
    return redirect('/login')

@app.route('/predict', methods=['POST'])
def predict():
    review = request.form['review']
        
    review_transformed = vectorizer.transform([review])
    
    prediction = model.predict(review_transformed)[0]
    top_drugs = get_top_drugs(prediction,df)
    
    return render_template('result.html', prediction=prediction,top_drugs=top_drugs)


def get_top_drugs(prediction, df):
    filtered_data = df[df['condition'] == prediction]
    top_drugs = (filtered_data.groupby('drugName')
                              .agg({'rating': 'mean'})
                              .sort_values('rating', ascending=False)
                              .head(20)
                              .reset_index())
    print(top_drugs)
    return top_drugs.to_dict(orient='records')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
