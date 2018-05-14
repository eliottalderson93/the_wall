from flask import Flask, render_template, redirect, request, session, flash
import re
from datetime import datetime
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
# create a regular expression object that we can use run operations on

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'KeepItSecretKeepItSafe'
bcrypt = Bcrypt(app)
mysql = connectToMySQL('walldb')

class User:
    def __init__(self,id):
        self.idusers = id
        self.first_name = getDataFromBase('first_name','users','idusers','{}'.format(id))
        self.last_name = getDataFromBase('last_name','users','idusers','{}'.format(id))
        self.email = getDataFromBase('email','users','idusers','{}'.format(id))
        self.namestring = self.first_name + ' ' +self.last_name
#         self.email = getDataFromBase('email','users','id','{}'.format(id))
#         self.password

class Message:
    def __init__(self,id):
        self.idmessages = id
        self.user_id_fk = getDataFromBase('user_id_fk','messages','idmessages','{}'.format(id))
        self.message = getDataFromBase('message','messages','idmessages','{}'.format(id))
        self.created_at = getDataFromBase('created_at','messages','idmessages','{}'.format(id))
        self.updated_at = getDataFromBase('updated_at','messages','idmessages','{}'.format(id))

class Comment:
    def __init__(self,id):
        self.idcomments = id
        self.msg_id_fk = getDataFromBase('msg_id_fk','comments','idcomments','{}'.format(id))
        self.user_id_fk = getDataFromBase('user_id_fk','comments','idcomments','{}'.format(id))
        self.comment = getDataFromBase('comment','comments','idcomments','{}'.format(id))
        self.created_at = getDataFromBase('created_at','comments','idcomments','{}'.format(id))
        self.updated_at = getDataFromBase('updated_at','comments','idcomments','{}'.format(id))

@app.route('/')
def index():
    if 'initial' in session:
        session['initial'] = False
        session['user_id'] = -1
        if session['user_id'] != -1: #user is here
            flash('You are logged in')
            return redirect('/success')
        #print(session)
    else:
        session['initial'] = True #initialize
        session['user_id'] = -1
        session['valid'] =True
        session['first_name'] = 'you little orc' #someone has hacked in if they read this
    if session['initial'] == False:
        session['valid'] =True
    return render_template('code.html')

@app.route("/register", methods=['POST'])
def reserve():     
    if len(request.form['first_name']) < 2:
        flash("First name too short", 'first_name')
        session['valid'] =False
    elif request.form['first_name'].isalpha() == False:
        flash("First name invalid", 'first_name')
        session['valid'] =False
    if len(request.form['last_name']) < 2:
        flash("Last name too short", 'last_name')
        session['valid'] =False
    elif request.form['last_name'].isalpha() == False:
        flash("Last name invalid", 'last_name')
        session['valid'] =False
    if not EMAIL_REGEX.match(request.form['email']):
        print('REGEX')
        flash("Invalid Email Address!",'email')
        session['valid'] = False
    else: #check if in DB 
        print('is the email in DB?')
        if (checkDB('email','users',request.form['email'])==True):
            print('email in DB, user cannot use same email')
            flash("Invalid Email Address!",'email')
            session['valid'] = False
        else:
            print('email is not in DB')
    if request.form['password'] != request.form['confirm']:
        flash("Passwords must match",'confirm')
        session['valid'] =False
    if len(request.form['password']) < 8:
        flash("Password too short",'password')
        session['valid'] =False
    #end verification
    print('is this session valid? :',session['valid'])
    if session['valid'] == True:
        first = request.form['first_name']
        last = request.form['last_name']
        email = request.form['email']
        pw_hash = hashPassword(request.form['password'])
        session['user_id'] = createUser(first,last,email,pw_hash)
        session['first_name'] = first
        session['user_obj'] = User(session['user_id']).__dict__
        return redirect('/success')
    else:
        return redirect('/')

@app.route("/login_page")
def display():
    return render_template('login.html')

@app.route("/login", methods=['POST'])
def mainframe():
    debugHelp(message='LOGINPOST')
    attempt = request.form['email']
    if not EMAIL_REGEX.match(attempt):
        flash("We don't recognize your email")
        return redirect('/login_page')
    correct_email = checkDB('email','users',attempt)
    print('Check email::',correct_email)
    debugHelp(message='LOGINPOST')
    correct_passwordDB = getDataFromBase('password','users','email',attempt)
    print('DB_OBJ::',correct_passwordDB)
    print('SUBMIT_PASSWORD::',request.form['password'])
    if (correct_passwordDB == False):   #check if we misqueried the DB
        correct_password = False        #will fail below and redirect
    else:
        print('DB_PASS::', correct_passwordDB)
        correct_password = bcrypt.check_password_hash(correct_passwordDB,request.form['password'])
    debugHelp(message='LOGINPOST')
    print('let me in?',correct_password,correct_email)
    if correct_password and correct_email:
        print('this password matches an email')
        #user = getDataFromBase('first_name','users','email',attempt) #returns a size 1 tuple of dict, access user[0]['key']
        user_id = getDataFromBase('idusers','users','email',attempt)
        user = User(user_id)
        #print('USER_OBJ1::',user)
        user = user.__dict__
        session['user_obj'] = user
        debugHelp(message='BACK_LOGINPOST')
        print('USER_OBJ2::',user)
        session['first_name'] = user['first_name']
        print('SESSION_FIRST::',session['first_name'])
        return redirect('/success')
    else:
        flash("Invalid Login")
        return redirect('/login_page')

@app.route("/create_post", methods = ['POST'])
def create_message():
    #Post to database
    createMessage(session['user_obj']['idusers'],request.form['post_text'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return redirect('/success')

@app.route("/create_comment",methods = ['POST'])
def create_comment():
    #Post to database                            #replace 5 with correct post ID
    msg_id = int(request.form['comment_post_fk'])
    print('SUBMITTED_MSG_FK::',msg_id)
    createComment(session['user_obj']['idusers'],msg_id,request.form['comment_text'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'),datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return redirect('/success')

# def createComment(user_id,msg_id,cmnt_text,time_created,time_updated):
#     debugHelp(message ='CREATECOMMENT')
#     data = { "user_id" : user_id,"msg_id" : msg_id,"comment_text" : cmnt_text, "time_created" : time_created, "time_updated" : time_updated}
#     query = "INSERT INTO messages (user_id_fk,msg_id_fk,comment,created_at,updated_at) VALUES ('{user_id}','{}','{comment_text}','{time_created}','{time_updated}');".format(**data) 
#     print('DATA OBJECT::',data)
#     print('QUERY STRING::',query)
#     msg_id = mysql.query_db(query, data)
#     return msg_id

@app.route("/success")
def success():
    query_users = "SELECT idusers FROM users;"
    query_posts = "SELECT idmessages FROM messages;"
    query_comments = "SELECT idcomments FROM comments;"
    users = mysql.query_db(query_users)
    user_dict = {}
    for id in users:
        this_user = (User(id['idusers']).__dict__)
        user_dict.update({'{}'.format(id['idusers']):this_user}) #user dict has a key of user id to object user
    posts = mysql.query_db(query_posts)
    post_dict = {}
    for id_post in posts:
        #print('ID_post::',id_post)
        this_post = (Message(id_post['idmessages']).__dict__)
        post_dict.update({'{}'.format(id_post['idmessages']):this_post}) #post dict has a key of post id to an object post
    comments = mysql.query_db(query_comments)
    comment_dict = {}
    for id_comment in comments:
        this_comment = (Comment(id_comment['idcomments']).__dict__)
        comment_dict.update({'{}'.format(id_post['idmessages']):this_post}) #post dict has a key of post id to an object post
    print(post_dict)
    print(user_dict)
    print(comment_dict)
    return render_template('user.html',users=user_dict,posts=post_dict,comments=comment_dict)

@app.route('/clear')
def clear():
    debugHelp(message='LOGOUT')
    session.clear()
    debugHelp(message ='SESSION_EMPTY')
    return redirect('/')

def getDataFromBase(category,table,identifier,request):
    #debugHelp(message ='GETDATAFROMBASE')
    this_request = {'category':category,'table':table,identifier:'identifier',request:'request'}
    #print("you are requesting::",this_request)
    query = "SELECT {} FROM {} WHERE {}='{}';".format(category.strip("'"),table.strip("'"),identifier.strip("'"),request.strip("'"))
    #print("you are querying::",query)
    result = mysql.query_db(query)
    if not(result):
        print('no such data')
        return False
    else:
        #print("you get::", result[0]['{}'.format(category.strip("'"))])
        final = result[0]['{}'.format(category.strip("'"))]
        return final

def createComment(user_id,msg_id,cmnt_text,time_created,time_updated):
    debugHelp(message ='CREATECOMMENT')
    data = { "user_id" : user_id,"msg_id" : msg_id,"comment_text" : cmnt_text, "time_created" : time_created, "time_updated" : time_updated}
    query = "INSERT INTO comments (user_id_fk,msg_id_fk,comment,created_at,updated_at) VALUES ('{user_id}','{msg_id}','{comment_text}','{time_created}','{time_updated}');".format(**data) 
    print('DATA OBJECT::',data)
    print('QUERY STRING::',query)
    msg_id = mysql.query_db(query, data)
    return msg_id

def createMessage(user_id,msg_text,time_created,time_updated):
    debugHelp(message ='CREATEMSG')
    data = { "user_id" : user_id,"message_text" : msg_text, "time_created" : time_created, "time_updated" : time_updated}
    query = "INSERT INTO messages (user_id_fk,message,created_at,updated_at) VALUES ('{user_id}','{message_text}','{time_created}','{time_updated}');".format(**data) 
    print('DATA OBJECT::',data)
    print('QUERY STRING::',query)
    msg_id = mysql.query_db(query, data)
    return msg_id

def createUser(fname,lname,email,pw_hash):
    debugHelp(message ='CREATEUSER')
    print('HASH::',pw_hash)
    data = { "first_name" : fname,"last_name" : lname, "email" : email, "password" : pw_hash}
    query = "INSERT INTO users (first_name,last_name,email,password) VALUES ('{first_name}','{last_name}','{email}','{password}');".format(**data) 
    print('DATA OBJECT::',data)
    print('QUERY STRING::',query)
    user_id = mysql.query_db(query, data)
    return user_id

def hashPassword(pw):
    pw_hash = bcrypt.generate_password_hash(pw)
    pw_hash = str(pw_hash).strip('b').replace("'","")
    return pw_hash

def checkDB(col,table,check_var):
    col = str(col)
    table = str(table)
    check_var = str(check_var)
    data = {'col':col,'table':table,'check_var':check_var}
    q_string = "SELECT "+col+" FROM "+table+';'
    debugHelp(message = 'CHECKDB')
    print('QUERY::',q_string)
    print('DATA::',data)
    col_check = mysql.query_db(q_string) #should return dictionary
    print('DICT_ARRAY::',col_check)
    for i in range(len(col_check)): #elements in dictionary
        print('CHECKING DICT_ARRAY')
        print('ELEMENT::',col_check[i]['{}'.format(col)])
        print('checked against::',check_var)
        if col_check[i]['{}'.format(col)] == data['check_var']:
            print('ELEMENT FOUND')
            return True
    print('ELEMENT NOT FOUND')
    return False

def debugHelp(message = ""):
    print("\n\n-----------------------", message, "--------------------")
    print('REQUEST.FORM:', request.form)
    print('SESSION:', session)

if __name__ == "__main__":
    app.run(debug=True)