from sqlalchemy import desc, asc

from prisonapp import *
from models import User, Comment, Visitation, VisitationLogs, Visitors, Announcements, Prisoner, NewsUpdate, Tokens
import time


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


@app.route('/api/register', methods=['POST'])
@cross_origin('*')
def register_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    exists = User.query.filter_by(username=data['username']).first()

    if exists is None:
        new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password,
                        firstname=data['firstname'], middlename=data['middlename'],
                        lastname=data['lastname'], contact=data['contact'], address=data['address'],
                        birthday=data['birthday'], prisoner=data['prisoner'], role_id=2, status="PENDING",
                        age=data['age'])
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Registered successfully!'})
    else:
        return jsonify({'message': 'Username Already Exists!'}), 500


@app.route('/api/login', methods=['GET'])
@cross_origin('*')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required!"'})

    user = User.query.filter_by(username=auth.username).first()
    tokens = Tokens.query.filter_by(uid=user.id).first()
    print ('a')
    fmt = '%Y-%m-%d %H:%M:%S.%f %Z'

    if not user:
        print ('b')
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required!"'})

    if check_password_hash(user.password_hash, auth.password):
        print ('c')
        if tokens is None:
            print ('d')
            exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=4320)
            exp = exp.replace(tzinfo=pytz.utc)
            token = jwt.encode(
                {'public_id': user.public_id, 'exp': exp.astimezone(pytz.timezone("Asia/Singapore"))},
                app.config['SECRET_KEY'])
            utc_changed = datetime.datetime.utcnow() + datetime.timedelta(minutes=4320) + datetime.timedelta(hours=8)
            utc_changed = utc_changed.replace(tzinfo=pytz.utc)
            new_token = Tokens(uid=user.id, token=token,
                               ttl=utc_changed.astimezone(pytz.timezone("Asia/Singapore")))
            db.session.add(new_token)
            db.session.commit()

            return jsonify(
                {'status': '200', 'token': token.decode('UTF-8'), 'role_id': user.role_id, 'public_id': user.public_id,
                 'message': 'login successful!', 'prisoner': user.prisoner, 'accountStatus': user.status})

        else:
            print ('e')
            diff1 = tokens.ttl
            diff2 = datetime.datetime.utcnow()
            diff2 = diff2.replace(tzinfo=pytz.utc)
            diff = diff1 - (diff2.astimezone(pytz.timezone("Asia/Singapore")))
            minutessince = int(diff.total_seconds() / 60)

            if (minutessince > 0):
                expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutessince)
                expiry = expiry.replace(tzinfo=pytz.utc)
                token = jwt.encode(
                    {'public_id': user.public_id, 'exp': expiry.astimezone(pytz.timezone("Asia/Singapore"))},
                    app.config['SECRET_KEY'])

                return jsonify(
                {'status': '200', 'token': token.decode('UTF-8'), 'role_id': user.role_id, 'public_id': user.public_id,
                 'message': 'login successful!', 'prisoner': user.prisoner, 'accountStatus': user.status})

            elif (minutessince <= 0):

                tokened = jwt.encode(
                    {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=4320)+ datetime.timedelta(hours=8)},
                    app.config['SECRET_KEY'])

                updated = Tokens.query.filter_by(uid=user.id).first()
                updated.token = tokened
                utc = datetime.datetime.utcnow() + datetime.timedelta(minutes=4320) + datetime.timedelta(hours=8)
                utc = utc.replace(tzinfo=pytz.utc)
                updated.ttl = (utc.astimezone(pytz.timezone("Asia/Singapore")))
                db.session.commit()

                return jsonify(
                    {'status': '200', 'token': tokened.decode('UTF-8'), 'role_id': user.role_id,
                     'public_id': user.public_id,
                     'message': 'login successful!', 'prisoner': user.prisoner, 'accountStatus': user.status})


@app.route('/api/user/visitation', methods=['POST'])
@cross_origin('*')
@token_required
def visitation(current_user):
    data = request.get_json()
    user = User.query.filter_by(public_id=data['pid']).first()

    new_visit = Visitation(vId=int(user.id), nameP=data['nameP'], date=data['vDate'], relationship=data['relationship'],
                           numberOfVisitors=int(data['numV']), status='PENDING')
    db.session.add(new_visit)
    db.session.commit()

    return jsonify({'message': 'Success!'})


@app.route('/api/user/comment', methods=['POST'])
@cross_origin('*')
@token_required
def post_comment(current_user):
    data = request.get_json()
    get_id = User.query.filter_by(public_id=data['public_id']).first()

    new_comment = Comment(uid=int(get_id.id), content=data['comment'], date=str(datetime.datetime.utcnow()))
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'Comment submitted! Thank you for your opinion!'})


@app.route('/api/clerk/get_users', methods=['GET'])
@cross_origin('*')
@token_required
def get_all_users(current_user):
    if current_user.role_id != '1':
        return jsonify({'message': 'Cannot perform that function!'})

    users = User.query.all()
    output = []

    for user in users:
        user_data = {}
        user_data['username'] = user.username
        output.append(user_data)

    return jsonify({'users': output})


@app.route('/api/clerk/visitor_data', methods=['GET'])
@cross_origin('*')
@token_required
def get_visitors(current_user):
    if current_user.role_id != '1':
        return jsonify({'message': 'Cannot perform that function!'})

    users = User.query.filter((User.role_id == str(2)) & ((User.status == "PENDING") | (User.status == "VERIFIED")))

    res = []

    for user in users:
        user_data = {}
        user_data['firstname'] = user.firstname
        user_data['middlename'] = user.middlename
        user_data['lastname'] = user.lastname
        user_data['age'] = user.age
        user_data['contact'] = user.contact
        user_data['address'] = user.address
        user_data['birthday'] = str(user.birthday)
        user_data['prisoner'] = user.prisoner
        user_data['status'] = user.status
        user_data['id'] = user.id
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/admin/visitor_data', methods=['GET'])
@cross_origin('*')
@token_required
def get_visitors_admin(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    users = User.query.filter((User.role_id == str(2)) & ((User.status == "PENDING") | (User.status == "VERIFIED")))

    res = []

    for user in users:
        user_data = {}
        user_data['firstname'] = user.firstname
        user_data['middlename'] = user.middlename
        user_data['lastname'] = user.lastname
        user_data['age'] = user.age
        user_data['contact'] = user.contact
        user_data['address'] = user.address
        user_data['birthday'] = str(user.birthday)
        user_data['prisoner'] = user.prisoner
        user_data['status'] = user.status
        user_data['id'] = user.id
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/clerk/account_accept', methods=['POST'])
@cross_origin('*')
@token_required
def accept(current_user):
    data = request.get_json()
    user = User.query.filter_by(id=data['user_id']).first()

    if str(data['response']) == 'yes':
        user.status = "VERIFIED"
        print user.id
        db.session.commit()

    else:
        user.status = "DECLINED"
        print user.id
        db.session.commit()

    return jsonify({'message': 'Account Verified!'})


@app.route('/api/clerk/manage_requests', methods=['GET'])
@cross_origin('*')
@token_required
def manage_requests(current_user):
    if current_user.role_id != '1':
        return jsonify({'message': 'Cannot perform that function!'})

    visitations = Visitation.query.filter_by(status="PENDING").order_by(desc(Visitation.date)).all()
    vis_approved = Visitation.query.filter((Visitation.status == "APPROVED"))

    res = []

    for visitation in visitations:
        visitor = User.query.filter_by(id=visitation.vId).first()
        splitted = visitation.nameP.split()
        prisoner = Prisoner.query.filter_by(firstname=str(splitted[0])).first()
        if prisoner is None:
            crime = 'null'
        else:
            crime = prisoner.crime

        user_data = {}
        user_data['vId'] = visitation.vId
        user_data['fname'] = visitor.firstname
        user_data['mname'] = visitor.middlename
        user_data['lname'] = visitor.lastname
        user_data['nameP'] = visitation.nameP
        user_data['crime'] = crime
        user_data['date'] = str(visitation.date)
        user_data['numberOfVisitors'] = visitation.numberOfVisitors
        user_data['status'] = visitation.status
        user_data['id'] = visitation.id
        res.append(user_data)

    tes = []

    for visitation2 in vis_approved:
        visitor = User.query.filter_by(id=visitation2.vId).first()
        user_data = {}
        user_data['vId'] = visitation2.vId
        user_data['fname'] = visitor.firstname
        user_data['mname'] = visitor.middlename
        user_data['lname'] = visitor.lastname
        user_data['nameP'] = visitation2.nameP
        user_data['date'] = str(visitation2.date)
        user_data['numberOfVisitors'] = visitation2.numberOfVisitors
        user_data['status'] = visitation2.status
        user_data['id'] = visitation2.id
        tes.append(user_data)

    dateNow = str(time.strftime("%Y-%m-%d"))
    return jsonify(
        {'status': 'ok', 'entries': res, 'count': len(res), 'entries2': tes, 'count2': len(tes), 'datenow': dateNow})


@app.route('/api/clerk/schedule_accept', methods=['POST'])
@cross_origin('*')
@token_required
def schedule_accept(current_user):
    data = request.get_json()
    visitor = Visitation.query.filter_by(id=data['vis_id']).first()

    # print data['user_id']
    if str(data['response']) == 'yes':
        visitor.status = 'APPROVED'
        db.session.commit()
        dt = datetime.datetime.now().time()
        dtWithoutSeconds = dt.replace(second=0, microsecond=0)
        new_logs = VisitationLogs(log_vId=data['vis_id'], user_vId=data['userid'], accepter_id=current_user.id,
                                  timein=dtWithoutSeconds, timeout="Null")
        db.session.add(new_logs)
        db.session.commit()
        return jsonify({'message': 'Scheduled!'})


    elif str(data['response']) == 'no':
        visitor.status = 'DECLINED'
        db.session.commit()
        return jsonify({'message': 'Schedule declined!'})


@app.route('/api/clerk/timeout', methods=['POST'])
@cross_origin('*')
@token_required
def time_out(current_user):
    data = request.get_json()
    visitor = VisitationLogs.query.filter(
        (VisitationLogs.log_vId == data['vis_id']) & (VisitationLogs.user_vId == data['userid'])).first()
    visitation = Visitation.query.filter(Visitation.id == data['vis_id']).first()

    if str(data['response']) == 'yes':
        visitation.status = 'Visitation Done'
        db.session.commit()
        dt = datetime.datetime.now().time()
        dtWithoutSeconds = dt.replace(second=0, microsecond=0)
        visitor.timeout = dtWithoutSeconds
        db.session.commit()
        return jsonify({'message': 'Timed out!'})


@app.route('/api/admin/addprisoner', methods=['POST'])
@cross_origin('*')
@token_required
def add_prisoner(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()
    exists = Prisoner.query.filter_by(firstname=data['firstname']).first()

    if exists is not None:
        if exists.firstname == data['firstname'] and exists.lastname == data['lastname']:
            return jsonify({'message': 'Prisoner Already Exists!'}), 500

    else:
        new_prisoner = Prisoner(firstname=data['firstname'], middlename=data['middlename'], lastname=data['lastname'],
                            birthday=data['birthday'], age=data['age'], crime=data['crime'])

        db.session.add(new_prisoner)
        db.session.commit()

        return jsonify({'message': 'Added successfully!'})


@app.route('/api/admin/visit_logs', methods=['GET'])
@cross_origin('*')
@token_required
def visit_logs(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    visitationlogs = VisitationLogs.query.all()
    res = []

    for visit_logs in visitationlogs:
        user_data = {}
        user_inf = User.query.filter_by(id=visit_logs.user_vId).first()
        visittime = Visitation.query.filter_by(id=visit_logs.log_vId).first()
        vislog = VisitationLogs.query.filter_by(id=visit_logs.id).first()
        accepter_inf = User.query.filter_by(id=visit_logs.accepter_id).first()
        user_data['fname_accepter'] = accepter_inf.firstname
        user_data['mname_accepter'] = accepter_inf.middlename
        user_data['lname_accepter'] = accepter_inf.lastname
        user_data['fname'] = user_inf.firstname
        user_data['mname'] = user_inf.middlename
        user_data['lname'] = user_inf.lastname
        user_data['inmate'] = visittime.nameP
        user_data['relationship'] = visittime.relationship
        user_data['date'] = str(visittime.date)
        user_data['timein'] = vislog.timein
        user_data['timeout'] = vislog.timeout
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/clerk/visit_unregistered', methods=['POST'])
@cross_origin('*')
@token_required
def visitors(current_user):
    data = request.get_json()

    newVisitor = Visitors(firstname=data['firstname'], middlename=data['middlename'], lastname=data['lastname'],
                          address=data['address'], contactno=data['contactno'], prisonername=data['prisonername'],
                          relationship=data['relationship'], date=str(datetime.datetime.utcnow()))
    db.session.add(newVisitor)
    db.session.commit()

    return jsonify({'message': 'Visitor verified'})


@app.route('/api/admin/announcements', methods=['POST'])
@cross_origin('*')
@token_required
def announcements(current_user):
    data = request.get_json()

    newAnnouncement = Announcements(title=data['title'], announcement=data['announcement'],
                                    date=datetime.datetime.utcnow())
    db.session.add(newAnnouncement)
    db.session.commit()

    return jsonify({'message': 'Announcement successfully added!'})


@app.route('/api/admin/announcements_get', methods=['GET'])
@cross_origin('*')
@token_required
def getAnnouncements(current_user):
    announce = Announcements.query.order_by(desc(Announcements.date)).all()

    res = []

    for ann in announce:
        ann_data = {}
        ann_data['id'] = ann.id
        ann_data['title'] = ann.title
        ann_data['announcement'] = ann.announcement
        ann_data['date'] = str(ann.date)

        res.append(ann_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/admin/comments_get', methods=['GET'])
@cross_origin('*')
@token_required
def getComments(current_user):
    comment = Comment.query.order_by(desc(Comment.date)).all()

    res = []

    for com in comment:
        ann_data = {}
        ann_data['id'] = com.id
        ann_data['content'] = com.content
        ann_data['date'] = str(com.date)

        res.append(ann_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/user/announcements', methods=['GET'])
@cross_origin('*')
def get_announcements():
    ann = Announcements.query.order_by(desc(Announcements.date)).all()

    def jsonlord(ann):
        my_list = []
        new_list = {"announcements": ""}
        for data in ann:
            my_list.append({'date': str(data.date), 'content': data.announcement, 'title': data.title})

        new_list.update({"announcements": my_list})
        return jsonify(new_list)

    return jsonlord(ann)



@app.route('/api/admin/addclerk', methods=['POST'])
@cross_origin('*')
@token_required
def add_clerk(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')
    exists = User.query.filter_by(username=data['username']).first()

    if exists is None:
        new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password,
                        firstname=data['firstname'], middlename=data['middlename'],
                        lastname=data['lastname'], contact=data['contact'], address=data['address'],
                        birthday=data['birthday'], role_id=1, status="VERIFIED",
                        age=data['age'])
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Registered successfully!'})

    else:
        return jsonify({'message': 'Username Already Taken!'}), 500


@app.route('/api/clerk/prisoner_data', methods=['GET'])
@cross_origin('*')
@token_required
def get_prisoners(current_user):
    if current_user.role_id != '1':
        return jsonify({'message': 'Cannot perform that function!'})

    prisoners = Prisoner.query.all()

    res = []

    for prisoner in prisoners:
        prisoner_data = {}
        prisoner_data['firstname'] = prisoner.firstname
        prisoner_data['middlename'] = prisoner.middlename
        prisoner_data['lastname'] = prisoner.lastname
        prisoner_data['birthday'] = str(prisoner.birthday)
        prisoner_data['age'] = prisoner.age
        prisoner_data['crime'] = prisoner.crime
        res.append(prisoner_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/admin/prisoner_data', methods=['GET'])
@cross_origin('*')
@token_required
def adminget_prisoners(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    prisoners = Prisoner.query.all()

    res = []

    for prisoner in prisoners:
        prisoner_data = {}
        prisoner_data['id'] = prisoner.id
        prisoner_data['firstname'] = prisoner.firstname
        prisoner_data['middlename'] = prisoner.middlename
        prisoner_data['lastname'] = prisoner.lastname
        prisoner_data['birthday'] = str(prisoner.birthday)
        prisoner_data['age'] = prisoner.age
        prisoner_data['crime'] = prisoner.crime
        res.append(prisoner_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/admin/edit_prisoner', methods=['POST'])
@cross_origin('*')
@token_required
def edit_prisonerdata(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    editable = Prisoner.query.filter_by(id=data['id']).first()
    exists = Prisoner.query.filter_by(firstname=data['firstname']).first()

    if exists is not None:
        if exists.firstname == data['firstname'] and exists.lastname == data['lastname']:
            return jsonify({'message': 'Prisoner Already Exists!'}), 500
    else:
        editable.firstname = data['firstname']
        editable.middlename = data['middlename']
        editable.lastname = data['lastname']
        editable.birthday = data['birthday']
        editable.age = data['age']
        editable.crime = data['crime']

        db.session.commit()

        return jsonify({'message': 'Edit successful!'})


@app.route('/api/admin/edit_announcement', methods=['POST'])
@cross_origin('*')
@token_required
def edit_announcement(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    editable = Announcements.query.filter_by(id=data['id']).first()

    editable.title = data['title']
    editable.announcement = data['announcement']
    editable.date = datetime.datetime.now()

    db.session.commit()

    return jsonify({'message': 'Edit successful!'})

@app.route('/api/admin/visit_walkin', methods=['GET'])
@cross_origin('*')
@token_required
def visit_walkin(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    visitationlogs = Visitors.query.all()
    res = []

    for visit_logs in visitationlogs:
        user_data = {}
        user_data['fname'] = visit_logs.firstname
        user_data['mname'] = visit_logs.middlename
        user_data['lname'] = visit_logs.lastname
        user_data['inmate'] = visit_logs.prisonername
        user_data['relationship'] = str(visit_logs.relationship)
        user_data['date'] = str(visit_logs.date)
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/admin/newsupdate', methods=['POST'])
@cross_origin('*')
@token_required
def newsupdate(current_user):
    data = request.get_json()

    newNewsUpdate = NewsUpdate(title=data['newsTitle'], newsupdate=data['articleContent'], date=datetime.datetime.utcnow())
    db.session.add(newNewsUpdate)
    db.session.commit()

    return jsonify({'message': 'Article submitted!', 'status': 'ok'})


@app.route('/api/view_newsupdate', methods=['GET'])
@cross_origin('*')
def view_newsupdate():
    news_update = NewsUpdate.query.order_by(desc(NewsUpdate.id)).all()

    res = []

    for news in news_update:
        news_data = {}
        news_data['id'] = news.id
        news_data['title'] = news.title
        news_data['newsupdate'] = news.newsupdate
        news_data['date'] = str(news.date)

        res.append(news_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/admin/checkadmin', methods=['GET'])
@cross_origin('*')
def checkadmin():
    check_admin = User.query.filter_by(role_id=str(0)).first()

    if check_admin is None:
        return jsonify({'message': 'Action allowed!', 'action': 'enabled'})
    else:
        return jsonify({'message': 'Action not allowed!', 'action': 'disabled'})


@app.route('/api/admin/setup', methods=['POST'])
@cross_origin('*')
def admin_setup():

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    exists = User.query.filter_by(role_id=str(0)).first()

    if exists is None:
        new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password,
                        firstname=data['firstname'], middlename=data['middlename'],
                        lastname=data['lastname'], contact=data['contact'], address=data['address'],
                        birthday=data['birthday'], role_id=0, status="VERIFIED",
                        age=data['age'])
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Registered successfully!'})
    else:
        return jsonify({'message': 'Admin already Set!'}), 500
