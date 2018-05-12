from prisonapp import *
from models import User, Comment, Visitation, Announcements, Tokens


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])

            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# START OF VISITOR API

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password,
                    firstname=data['firstname'], middlename=data['middlename'],
                    lastname=data['lastname'], contact=data['contact'], address=data['address'],
                    birthday=data['birthday'], prisoner=data['prisoner'], role_id=2, status=True,
                    age=data['age'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully!'})


@app.route('/api/login/', methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required!"'})

    user = User.query.filter_by(username=auth.username).first()
    tokens = Tokens.query.filter_by(uid=user.id).first()

    fmt = '%Y-%m-%d %H:%M:%S.%f %Z'

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required!"'})

    if check_password_hash(user.password_hash, auth.password):

        if tokens is None:

            token = jwt.encode(
                {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=4320)},
                app.config['SECRET_KEY'])
            utc_changed = datetime.datetime.utcnow() + datetime.timedelta(minutes=4320)
            utc_changed = utc_changed.replace(tzinfo=pytz.utc)
            new_token = Tokens(uid=user.id, token=token,
                               ttl=utc_changed.astimezone(pytz.timezone("Asia/Singapore")))
            db.session.add(new_token)
            db.session.commit()

            return jsonify(
                {'status': '200', 'token': token.decode('UTF-8'), 'role_id': user.role_id, 'public_id': user.public_id,
                 'message': 'login successful!', 'prisoner': user.prisoner, 'accountStatus': user.status})

        else:

            diff1 = tokens.ttl
            diff2 = datetime.datetime.utcnow()
            diff2 = diff2.replace(tzinfo=pytz.utc)
            diff = diff1 - (diff2.astimezone(pytz.timezone("Asia/Singapore")))
            minutessince = int(diff.total_seconds() / 60)

            if (minutessince > 0):

                token = jwt.encode(
                    {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=minutessince)},
                    app.config['SECRET_KEY'])

                return jsonify(
                {'status': '200', 'token': token.decode('UTF-8'), 'role_id': user.role_id, 'public_id': user.public_id,
                 'message': 'login successful!', 'prisoner': user.prisoner, 'accountStatus': user.status})

            elif (minutessince <= 0):

                tokened = jwt.encode(
                    {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=4320)},
                    app.config['SECRET_KEY'])

                updated = Tokens.query.filter_by(uid=user.id).first()
                updated.token = tokened
                utc = datetime.datetime.utcnow() + datetime.timedelta(minutes=4320)
                utc = utc.replace(tzinfo=pytz.utc)
                updated.ttl = (utc.astimezone(pytz.timezone("Asia/Singapore")))
                db.session.commit()

                return jsonify(
                    {'status': '200', 'token': tokened.decode('UTF-8'), 'role_id': user.role_id,
                     'public_id': user.public_id,
                     'message': 'login successful!', 'prisoner': user.prisoner, 'accountStatus': user.status})


@app.route('/api/user/visitation', methods=['POST'])
@token_required
def visitation(current_user):
    data = request.get_json()

    print data['pid']

    user = User.query.filter_by(public_id=data['pid']).first()


    new_visit = Visitation(vId=int(user.id), nameP=data['nameP'], date=data['vDate'],
                           numberOfVisitors=int(data['numV']), status='PENDING', time=data['timeV'],
                           relationship=data['relation'])
    db.session.add(new_visit)
    db.session.commit()

    return jsonify({'message': 'Success!'})




@app.route('/api/user/comment', methods=['POST'])
@token_required
def post_comment(current_user):
    data = request.get_json()
    get_id = User.query.filter_by(public_id=data['public_id']).first()

    new_comment = Comment(uid=int(get_id.id), content=data['comment'])
    db.session.add(new_comment)
    db.session.commit()



    return jsonify({'message': 'Comment submitted! Thank you for your opinion!'})

@app.route('/api/user/announcements', methods=['GET'])
def get_announcements():

    ann = Announcements.query.order_by(desc(Announcements.date)).all()

    def jsonlord(ann):
        my_list = []
        new_list = {"announcements" : ""}
        for data in ann:
            my_list.append({'date': str(data.date), 'content': data.content, 'title': data.title})

        new_list.update({"announcements": my_list})
        return jsonify(new_list)

    return jsonlord(ann)



# END OF VISITOR API


# START OF CLERK API


# END OF CLERK API
