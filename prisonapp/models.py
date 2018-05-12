from prisonapp import *


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username=db.Column(db.String(32), unique=True,index=True)
    password_hash=db.Column(db.String(128))
    firstname = db.Column(db.String(30))
    middlename = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    age = db.Column(db.String(5))
    contact = db.Column(db.String(15))
    address = db.Column(db.TEXT())
    birthday = db.Column(db.DATE)
    prisoner = db.Column(db.String(60))
    role_id=db.Column(db.String(2))
    status=db.Column(db.Boolean)
    comments = db.relationship('Comment', backref='user', lazy=True)
    visits = db.relationship('Visitation', backref='user', lazy=True)
    tokens = db.relationship('Tokens', backref='user', lazy=True)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer(), primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text())
    date = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow())
    reply = db.Column(db.Text(), nullable=True)
    dateReplied = db.Column(db.DateTime, nullable=True)

class Prisoner(db.Model):
    __tablename__ = 'prisoner'
    id = db.Column(db.Integer(), primary_key=True)
    firstname = db.Column(db.String(30))
    middlename = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    birthday = db.Column(db.DATE)
    age = db.Column(db.String(5))

class Visitation(db.Model):
    __tablename__ = 'visitation'
    id = db.Column(db.Integer(), primary_key=True)
    vId = db.Column(db.Integer, db.ForeignKey('user.id'))
    nameP = db.Column(db.String(36))
    date = db.Column(db.DATE)
    relationship = db.Column(db.String(20))
    time = db.Column(db.String(20))
    numberOfVisitors = db.Column(db.Integer())
    status = db.Column(db.String(20))

class Announcements(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer(), primary_key=True)
    sid = db.Column(db.Integer(), unique=False)
    date = db.Column(db.DATE, unique=False)
    title = db.Column(db.String(40), unique=False)
    content = db.Column(db.Text(), unique=False)

class Tokens(db.Model):
    __tablename__ = 'tokens'
    tid = db.Column(db.Integer(), primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(220))
    ttl = db.Column(db.DateTime(timezone=True))