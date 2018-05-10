from prisonapp import *
from models import User, Comment, Visitation, VisitationLogs, Visitors, Announcements, Prisoner

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify ({'message':'token is missing!'}), 401

        try:
            data=jwt.decode(token, app.config['SECRET_KEY'])

            current_user=User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated



@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password, firstname=data['firstname'], middlename=data['middlename'],
                    lastname=data['lastname'], contact=data['contact'], address=data['address'], birthday=data['birthday'], prisoner=data['prisoner'], role_id=2, status="PENDING",
                    age=data['age'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message':'Registered successfully!'})

@app.route('/api/login/', methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate':'Basic realm = "Login required!"'})

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required!"'})

    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id':user.public_id, 'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=90)}, app.config['SECRET_KEY'])

        print 'Token generated!'
        return jsonify({'status':'ok', 'token': token.decode('UTF-8'), 'role_id':user.role_id, 'public_id':user.public_id,'message':'login successful!'})

@app.route('/api/user/visitation', methods=['POST'])
@token_required
def visitation(current_user):
    data = request.get_json()
    user = User.query.filter_by(public_id=data['public_id']).first()

    new_visit = Visitation(vId=int(user.id),nameP=data['nameP'],date=data['vDate'],numberOfVisitors=int(data['numV']), status='PENDING')
    db.session.add(new_visit)
    db.session.commit()

    return jsonify({ 'message' : 'Success!' })


@app.route('/api/user/comment', methods=['POST'])
@token_required
def post_comment(current_user):
    data = request.get_json()
    get_id = User.query.filter_by(public_id=data['public_id']).first()

    new_comment = Comment(uid=int(get_id.id), content=data['comment'])
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message':'Comment submitted! Thank you for your opinion!'})

	
@app.route('/api/clerk/get_users', methods=['GET'])
@token_required
def get_all_users(current_user):

    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

    users = User.query.all()
    output = []

    for user in users:
        user_data = {}
        user_data['username'] = user.username
        output.append(user_data)

    return jsonify({ 'users':output })

@app.route('/api/clerk/visitor_data', methods=['GET'])
@token_required
def get_visitors(current_user):
    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

    users = User.query.filter((User.role_id==str(2)) & (User.status=="PENDING"))
    usersApproved = User.query.filter((User.role_id==str(2)) & (User.status=="VERIFIED"))

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
        user_data['status'] = user.status
        user_data['id'] = user.id
        res.append(user_data)

    tes = []
    for user2 in usersApproved:
        user_data = {}
        user_data['firstname'] = user2.firstname
        user_data['middlename'] = user2.middlename
        user_data['lastname'] = user2.lastname
        user_data['age'] = user2.age
        user_data['contact'] = user2.contact
        user_data['address'] = user2.address
        user_data['birthday'] = str(user2.birthday)
        user_data['status'] = user2.status
        user_data['id'] = user2.id
        tes.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res), 'entries2': tes, 'count2': len(tes)})

@app.route('/api/admin/visitor_data', methods=['GET'])
@token_required
def get_visitors_admin(current_user):
    if current_user.role_id != '0':
        return jsonify ({'message':'Cannot perform that function!'})

    users = User.query.filter((User.role_id==str(2)) & (User.status=="VERIFIED"))

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
        user_data['status'] = user.status
        user_data['id'] = user.id
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})


@app.route('/api/clerk/account_accept', methods=['POST'])
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

    return jsonify({'message':'Account Verified!'})

@app.route('/api/clerk/manage_requests', methods=['GET'])
@token_required
def manage_requests(current_user):

    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

    visitations = Visitation.query.filter_by(status="PENDING").order_by(Visitation.date).all()
    vis_approved = Visitation.query.filter((Visitation.status=="APPROVED"))

    res = []

    for visitation in visitations:
        user_data = {}
        user_data['vId'] = visitation.vId
        user_data['nameP'] = visitation.nameP
        user_data['date'] = str(visitation.date)
        user_data['numberOfVisitors'] = visitation.numberOfVisitors
        user_data['status'] = visitation.status
        user_data['id'] = visitation.id
        res.append(user_data)

    tes = []

    for visitation2 in vis_approved:
        user_data = {}
        user_data['vId'] = visitation2.vId
        user_data['nameP'] = visitation2.nameP
        user_data['date'] = str(visitation2.date)
        user_data['numberOfVisitors'] = visitation2.numberOfVisitors
        user_data['status'] = visitation2.status
        user_data['id'] = visitation2.id
        tes.append(user_data)



    return jsonify({'status': 'ok', 'entries': res, 'count': len(res), 'entries2': tes, 'count2': len(tes)})


@app.route('/api/clerk/schedule_accept', methods=['POST'])
@token_required
def schedule_accept(current_user):

    data = request.get_json()
    visitor = Visitation.query.filter_by(id=data['vis_id']).first()

    # print data['user_id']
    if str(data['response']) == 'yes':
        visitor.status = 'APPROVED'
        db.session.commit()
        new_logs = VisitationLogs(log_vId=data['vis_id'], user_vId=data['userid'])
        db.session.add(new_logs)
        db.session.commit()
        return jsonify({'message':'Scheduled!'})


    elif str(data['response']) == 'no':
        visitor.status = 'DECLINED'
        db.session.commit()
        return jsonify({'message':'Schedule Declined!'})




@app.route('/api/admin/addprisoner', methods=['POST'])
@token_required
def add_prisoner(current_user):
    if current_user.role_id != '0':
        return jsonify ({'message':'Cannot perform that function!'})

    data = request.get_json()

    new_prisoner = Prisoner(firstname=data['firstname'], middlename=data['middlename'], lastname=data['lastname'], birthday=data['birthday'], age=data['age'], crime=data['crime'])

    db.session.add(new_prisoner)
    db.session.commit()

    return jsonify({'message':'Added successfully!'})

  
@app.route('/api/admin/visit_logs', methods=['GET'])
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
        user_data['fname'] = user_inf.firstname
        user_data['mname'] = user_inf.middlename
        user_data['lname'] = user_inf.lastname
        user_data['inmate'] = visittime.nameP
        user_data['date'] = str(visittime.date)
        res.append(user_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})
	
@app.route('/api/clerk/visit_unregistered', methods=['POST'])
@token_required
def visitors(current_user):
    data = request.get_json()

    newVisitor = Visitors(firstname=data['firstname'], middlename=data['middlename'], lastname=data['lastname'], address=data['address'], contactno=data['contactno'], prisonername=data['prisonername'], relationship=data['relationship'],date=str(datetime.datetime.now()))
    db.session.add(newVisitor)
    db.session.commit()

    return jsonify({'message':'Visitor verified'})

@app.route('/api/admin/announcements', methods=['POST'])
@token_required
def announcements(current_user):
    data = request.get_json()

    newAnnouncement = Announcements(title=data['title'], announcement=data['announcement'], date=datetime.datetime.now())
    db.session.add(newAnnouncement)
    db.session.commit()

    return jsonify({'message':'Announcement successfully added!'})

@app.route('/api/admin/announcements_get', methods=['GET'])
@token_required
def getAnnouncements(current_user):

    if current_user.role_id != '0':
        return jsonify ({'message':'Cannot perform that function!'})

    announce = Announcements.query.all()

    res = []

    for ann in announce:
        ann_data = {}
        ann_data['id'] = ann.id
        ann_data['title'] = ann.title
        ann_data['announcement'] = ann.announcement

        res.append(ann_data)

    return jsonify({'status': 'ok', 'entries': res, 'count': len(res)})
	
@app.route('/api/admin/addclerk', methods=['POST'])
@token_required
def add_clerk(current_user):
    if current_user.role_id != '0':
        return jsonify ({'message':'Cannot perform that function!'})

    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password_hash=hashed_password,
                    firstname=data['firstname'], middlename=data['middlename'],
                    lastname=data['lastname'], contact=data['contact'], address=data['address'],
                    birthday=data['birthday'], role_id=1, status=True,
                    age=data['age'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully!'})

@app.route('/api/clerk/prisoner_data', methods=['GET'])
@token_required
def get_prisoners(current_user):
    if current_user.role_id != '1':
        return jsonify ({'message':'Cannot perform that function!'})

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
@token_required
def edit_prisonerdata(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    editable = Prisoner.query.filter_by(id=data['id']).first()

    editable.firstname = data['firstname']
    editable.middlename = data['middlename']
    editable.lastname = data['lastname']
    editable.birthday = data['birthday']
    editable.crime = data['crime']

    db.session.commit()

    return jsonify({'message': 'Edit successful!'})

@app.route('/api/admin/edit_announcement', methods=['POST'])
@token_required
def edit_announcement(current_user):
    if current_user.role_id != '0':
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    editable = Announcements.query.filter_by(id=data['id']).first()

    editable.title = data['title']
    editable.announcement = data['announcement']

    db.session.commit()

    return jsonify({'message': 'Edit successful!'})
