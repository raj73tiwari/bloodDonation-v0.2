from flask import Flask, redirect,render_template,request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,login_required,logout_user,current_user,login_manager
from sqlalchemy.sql import func


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='Doante-Blood'
db=SQLAlchemy(app)
migrate=Migrate(app,db)



# models

class User( db.Model,UserMixin):
    id =db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(150),nullable=False)
    age=db.Column(db.Integer,nullable=False)
    email=db.Column(db.String(150),unique=True)
    contact=db.Column(db.Integer,nullable=False)
    blood=db.Column(db.String(30),nullable=False)
    password=db.Column(db.String(150),nullable=False)
    appointments=db.relationship('Appointment',backref='user')
    transactions=db.relationship('Transaction',backref='user')

class Appointment(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    appointment_time=db.Column(db.String(150))
    time= db.Column(db.DateTime, default=datetime.now)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    donate=db.Column(db.Boolean,nullable=False)
    status=db.Column(db.Boolean)

class Transaction(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    time=db.Column(db.DateTime, default=datetime.now)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    donate=db.Column(db.Boolean,nullable=False)

class Blood(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    type=db.Column(db.String(150),nullable=False)
    quantity=db.Column(db.Integer,nullable=False)

# routes

login_manager=LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))



@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get("email")
        password=request.form.get("password")

        user=User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                login_user(user)
                flash(" Signed in successfully !",category='success')
                if user.id !=2:
                    return redirect('/user')
                return redirect('/admin')
            else:
                flash('Incorrect password!',category='error')
        else:
            flash("Email doesn't exist!",category='error')

    return render_template('login.html')



@app.route("/signup",methods=['GET','POST'])
def signup():
    if request.method=='POST':
        new_name=request.form.get("user_name")
        new_email=request.form.get("user_email")
        new_password=request.form.get("user_password")
        new_age=request.form.get("user_age")
        new_blood=request.form.get("user_blood")
        new_contact=request.form.get("user_number")

        user=User.query.filter_by(email=new_email).first()
        if user:
            flash("Email already exists !",category='error')
        else:
            l=True
            e=True
            p=True
            no=True
            if len(new_name)<3:
                flash("Name too short!",category='error')
                l=False
            if len(new_email)<6:
                flash("Email too short !",category='error')
                e=False
            if len(new_password)<4:
                flash("Password too short !",category='error')
                p=False
            if len(new_contact)<10:
                flash("Please enter 10 digit mobile number !",category='error')
                no=False
            if (l and p and e and no):
                new_user=User(email=new_email,name=new_name,password=generate_password_hash(new_password,method='sha256'),blood=new_blood,age=new_age,contact=new_contact)  
                db.session.add(new_user)
                db.session.commit()    
                login_user(new_user)
                flash("Signed up successfully !",category='success')
                return redirect('/user')
    return render_template('signup.html')


@app.route("/logout")
@login_required
def signout():
    logout_user()
    flash("Signed out successfully !",category='success')
    return redirect('/')


@app.route("/")
def home():
    
    return render_template('homePage.html',user=False)








@app.route("/user")
@login_required
def user():
    don=0
    rec=0
    for trans in current_user.transactions:
        if trans.donate:
            don+=1
        else:
            rec+=1
    dValue=str(don)+" "+str(rec)
    dLabel="donated received"
    dTotal=don+rec
    rec_trans=current_user.transactions[len(current_user.transactions)-2:]
    return render_template('userPage.html',dValue=dValue,dLabel=dLabel,dTotal=dTotal,rec_trans=rec_trans)

@app.route("/usrHis")
@login_required
def userHis():
    return render_template('userHistory.html')



@app.route("/receive",methods=['GET','POST'])
@login_required
def blood_req():
    if request.method=='POST':
        if len(current_user.appointments)>=4:
            flash("Appointment limit exceed !",category='error')    
            return redirect('/user')
        date=request.form.get("date")
        new_app=Appointment(user_id=current_user.id,donate=False,appointment_time=date)  
        db.session.add(new_app)
        db.session.commit()
        flash("Appointment successfully booked !",category='success')    
        return redirect('/user')

    return render_template('receiveForm.html')


@app.route("/donate",methods=['GET','POST'])
@login_required
def donate():
    if request.method=='POST':
        if len(current_user.appointments)>=4:
            flash("Appointment limit exceed !",category='error')    
            return redirect('/user')
        date=request.form.get("date")

        if current_user.age<18:
                flash("You must be 18 years old to donate blood !",category='error')
        if current_user.age>60:
                flash("You age should  be less than 60 to donate blood !",category='error')
        else:
            new_app=Appointment(user_id=current_user.id,donate=True,appointment_time=date)  
            db.session.add(new_app)
            db.session.commit()
            flash("Appointment successfully booked !",category='success')    
            return redirect('/user')
    return render_template('donationForm.html')

@app.route("/delApp/<int:id>",methods=['GET','POST'])
@login_required
def delApp(id):
    curr_appoint=Appointment.query.filter_by(id=id).first()
    db.session.delete(curr_appoint)
    db.session.commit()
    flash("Appointment deleted successfully !",category='success')
    if current_user.id==2:
        return redirect('/admin')
    return redirect('/user')

@app.route("/admin",methods=['GET','POST'])
@login_required
def admin():
    pending_app,scheduled_app=sort_appointment()
    av_bl,dTotal,dLabel,dValue=av_blood()
    av_comp_bl=avl_comp_bl()
    recent_trans= Transaction.query.order_by(Transaction.time.desc()).limit(5).all()
    
    return render_template('admin.html',scheduled_app=scheduled_app,pending_app=pending_app,av_blood=av_bl,recent_trans=recent_trans,dValue=dValue,dLabel=dLabel,dTotal=dTotal,avl_comp_bl=av_comp_bl)

@app.route("/accApp/<int:id>",methods=['GET','POST'])
@login_required
def accApp(id):
    curr_appoint=Appointment.query.filter_by(id=id).first()
    curr_appoint.status=True
    db.session.commit()
    flash("Appointment scheduled !",category='success')
    return redirect('/admin')

@app.route("/sDon/<int:id>",methods=['GET','POST'])
@login_required
def sDon(id):
    curr_appoint=Appointment.query.filter_by(id=id).first()
    curr_trans=Transaction(user_id=curr_appoint.user_id,donate=curr_appoint.donate)
    blood=Blood.query.filter_by(type=curr_appoint.user.blood).first()
    blood.quantity+=1
    db.session.add(curr_trans)
    db.session.delete(curr_appoint)
    db.session.commit()
    flash("Blood donation executed successfully!",category='success')
    return redirect('/admin')

@app.route("/sRec/<int:id>/<bl>",methods=['GET','POST'])
@login_required
def sRec(id,bl):
    curr_appoint=Appointment.query.filter_by(id=id).first()
    curr_trans=Transaction(user_id=curr_appoint.user_id,donate=curr_appoint.donate)
    blood=Blood.query.filter_by(type=bl).first()
    blood.quantity-=1
    db.session.add(curr_trans)
    db.session.delete(curr_appoint)
    db.session.commit()
    flash("Blood successfully received by user !",category='success')
    return redirect('/admin')

def av_blood():
    blood_list=Blood.query.all()
    blood_dict={}
    dTotal=0
    dLabel=""
    dValue=""
    for blood in blood_list:
        blood_dict[blood.type]=blood.quantity
        x,y=blood.type.split()
        dLabel+=" "+x+y
        dValue+=" "+str(blood.quantity)
        dTotal+=blood.quantity
    return blood_dict,dTotal,dLabel,dValue

def sort_appointment():
    all_appoint=Appointment.query.all()
    scheduled_app=[]
    pending_app=[]
    for appoint in all_appoint:
        if appoint.status==True:
            scheduled_app.append(appoint)
        elif appoint.status is None:
            pending_app.append(appoint)
    pending_app.sort(key=lambda appoint: datetime.strptime(appoint.appointment_time, '%Y-%m-%d'))
    scheduled_app.sort(key=lambda appoint: datetime.strptime(appoint.appointment_time, '%Y-%m-%d'))
    return pending_app,scheduled_app

def avl_comp_bl():
    pending_app,scheduled_app=sort_appointment()
    av_bl,dTotal,dLabel,dValue=av_blood()
    avl_comp_bl={}
    compatible_bl={'O +':['O +','O -'],'A +':['O +','O -','A +','A -'],'B +':['O +','O -','B +','B -'],'AB +':['O -','A -','B -','AB -','O +','A +','B +','AB +'],'O -':['O -'],'A -':['O -','A -'],'B -':['O -','B -'],'AB -':['O -','A -','B -','AB -']}
    for app in scheduled_app:
        if not app.donate:
            donors=compatible_bl[app.user.blood]
            avl=[]
            for i in donors:
                if av_bl[i]>0:
                    avl.append(i)
            avl_comp_bl[app.user.blood]=avl
    print(avl_comp_bl)
    return avl_comp_bl
        







@app.route("/allUsers",methods=['GET','POST'])
@login_required
def allUsr():
    user_lis=User.query.all()
    return render_template('allUsers.html',user_lis=user_lis)

@app.route("/adHistory",methods=['GET','POST'])
@login_required
def adHistory():
    all_trans=Transaction.query.all()
    return render_template('adminHistory.html',all_trans=all_trans)

@app.route("/adInv",methods=['GET','POST'])
@login_required
def adInv():
    av_bl,dTotal,dLabel,dValue=av_blood()
    return render_template('bloodinv.html',av_bl=av_bl,dTotal=dTotal,dLabel=dLabel,dValue=dValue)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error-404.html'), 404



if __name__=="__main__":
    app.run(debug=True)