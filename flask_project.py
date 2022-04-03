from flask import Flask,render_template,request,jsonify,session,redirect,url_for,flash
from dbconnection.datamanipulation import *
import datetime

app=Flask(__name__)
app.secret_key='supersecretkey'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/registerAction',methods=['post'])
def registerAction():
    name=request.form['name']
    gender=request.form['gender']
    dob=request.form['dob']
    phone=request.form['phone']
    username=request.form['username']
    password=request.form['password']
    r=sql_edit_insert("insert into register_tb values(NULL,?,?,?,?,?,?)",(name,gender,dob,phone,username+'@mymail.com',password))
    if r>0:
        msg="registration successful"
    else:
        msg="registration failed"
    return render_template('register.html',msg=msg)


@app.route('/checkUsername')
def checkUsername():
    username=request.args.get('username')
    user=sql_query2("select * from register_tb where username=?",[username+'@mymail.com'])
    if len(user)>0:
        msg="exists"
    else:
        msg="not exists"
    return jsonify({'valid':msg})

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loginAction',methods=['post'])
def loginAction():
    username=request.form['username']
    password=request.form['password']
    r=sql_query2("select * from register_tb where username=? and password=?",(username,password))
    if len(r)>0:
        session['id']=r[0][0]
        return render_template('userhome.html')
    else:
        return render_template('login.html',msg="incorrect username or password")

@app.route('/sendmessage')
def sendmessage():
    return render_template('sendmessage.html')

@app.route('/sendmessageAction',methods=['post'])
def sendmessageAction():
    userid=session['id']
    recievername=request.form['recieverid']
    reid=sql_query2("select * from register_tb where username=?",[recievername])
    print("reid=",reid)
    rid=reid[0][0]
    print("rid=",rid)
    message=request.form['message']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H:%M")
    subject=request.form['subject']
    user1=sql_query2("select * from register_tb where id=?",[userid])
    username=user1[0][5]
    r=sql_edit_insert("insert into message_tb values(NULL,?,?,?,?,?,?,?)",(userid,rid,message,date,time,subject,'pending'))
    if r>0:
        return render_template('sendmessage.html',msg="Message sent")
    return render_template('sendmessage.html')


@app.route('/recieveridcheck')
def recieveridcheck():
    recieverid=request.args.get('recieverid')
    print(recieverid)
    user=sql_query2("select * from register_tb where username=?",[recieverid])
    if len(user)>0:
        msg="exists"
    else:
        msg="not exists"
    print(msg)
    return jsonify({'valid':msg})

@app.route('/sentmessage')
def sentmessage():
    senderid=session['id']
    #message=sql_query2("select register_tb.username,message_tb.* from register_tb inner join message_tb on register_tb.id=message_tb.recieverid where senderid=? and status!=?",(senderid,'deleted by sender'))
    message=sql_query2("select * from message_tb where senderid=? and status!=?",(senderid,'deleted by sender'))
    return render_template('sentmessage.html',data=message)


@app.route('/delete')
def delete():
    uid=request.args.get('uid')
    r=sql_query2("select * from message_tb where id=?",[uid])
    if len(r)>0:
        status=r[0][7]
        if status == 'deleted by reciever':
            d=sql_edit_insert("delete from message_tb where id=?",[uid])
        else:
            d=sql_edit_insert("update message_tb set status=? where id=?",('deleted by sender',uid))
            
            
    return redirect(url_for('sentmessage'))

@app.route('/inbox')
def inbox():
    senderid=session['id']
    sender=sql_query2("select * from register_tb where id=?",[senderid])
    username=sender[0][5]
    print(username)
    print(sender)
    #message=sql_query2("select * from message_tb where recieverid=?",[username])
    message=sql_query2("select register_tb.username, message_tb.* from register_tb inner join message_tb on register_tb.id=message_tb.senderid where recieverid=? and message_tb.id not in (select messageid from trash_tb where userid=?) and status !=?",(senderid,senderid,'deleted by reciever'))
    return render_template('inbox.html',data=message,username=username)


@app.route('/inboxAction',methods=['post'])
def inboxAction():
    uid=session['id']
    sender=sql_query2("select * from register_tb where id=?",[uid])
    username=sender[0][5]
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H:%M")
    checkbox=request.form.getlist('checkbox')
    for inboxid in checkbox:
        
        inbox=sql_edit_insert("insert into trash_tb values(NULL,?,?,?,?)",(inboxid,uid,date,time))
    return redirect(url_for('inbox'))


@app.route('/viewTrash')
def viewTrash():
    uid=session['id']
    sender=sql_query2("select * from register_tb where id=?",[uid])
    username=sender[0][5]
    u=sql_query2("select register_tb.username,message_tb.*,trash_tb.date,trash_tb.time,trash_tb.messageid from (register_tb inner join message_tb on register_tb.id=message_tb.senderid) inner join trash_tb on message_tb.id=trash_tb.messageid where userid=?",[uid])
    return render_template('viewTrash.html',data=u)


@app.route('/deletet')
def deletet():
    uid=request.args.get('uid')
    print(uid)
    r=sql_edit_insert("delete from trash_tb where messageid=?",[uid])
    s=sql_query2("select * from message_tb where id=?",[uid])
    print(s)
    if len(s)>0:
        status=s[0][7]
        if status == "deleted by sender":
            x=sql_edit_insert("delete from message_tb where id=?",[uid])
        else:
            d=sql_edit_insert("update message_tb set status=? where id=?",('deleted by reciever',uid))
    return redirect(url_for('viewTrash'))


@app.route('/forward')
def forward():
    uid=request.args.get('uid')
    forward=sql_query2("select * from message_tb where id=?",[uid]) 
    return render_template('forward.html',data=forward)
            
    
@app.route('/forwardAction',methods=['post'])
def forwardAction():
    senderid=session['id']
    
    recievername=request.form['recieverid']
    reid=sql_query2("select * from register_tb where username=?",[recievername])
    rid=reid[0][0]
    subject=request.form['subject']
    message=request.form['message']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H:%M")
    f=sql_edit_insert("insert into message_tb values(NULL,?,?,?,?,?,?,?)",(senderid,rid,message,date,time,subject,'pending'))
    flash("message forwarded")
    return redirect(url_for('inbox'))

@app.route('/reply')
def reply():
    uid=request.args.get('uid')
    reply=sql_query2("select * from message_tb where id=?",[uid])
    recievermailid=reply[0][2]
    r=sql_query2("select * from register_tb where id=?",[recievermailid])
    username=r[0][5]
    return render_template('reply.html',data=username)



@app.route('/replyAction',methods=['post'])
def replyAction():
    senderid=session['id']
    recievername=request.form['recieverid']
    reid=sql_query2("select * from register_tb where username=?",[recievername])
    rid=reid[0][0]
    subject=request.form['subject']
    message=request.form['message']
    date=datetime.date.today()
    time=datetime.datetime.now().strftime("%H:%M")
    r=sql_edit_insert("insert into message_tb values(NULL,?,?,?,?,?,?,?)",(senderid,rid,message,date,time,subject,'pending'))
    flash("message replied")
    return redirect(url_for('inbox'))


@app.route('/editProfile')
def editProfile():
    uid=session['id']
    x=sql_query2("select * from register_tb where id=?",[uid])
    username=x[0][5]
    y=username.split('@')
    z=y[0]
    print(z)
    return render_template('editProfile.html',z=z,x=x)

@app.route('/editProfileAction',methods=['post'])
def editProfileAction():
    uid=session['id']
    name=request.form['name']
    gender=request.form['gender']
    dob=request.form['dob']
    phone=request.form['phone']
    username=request.form['username']
    password=request.form['password']
    r=sql_edit_insert("update register_tb set name=?,gender=?,dob=?,phone=?,username=?,password=? where id=?",(name,gender,dob,phone,username+'@mymail.com',password,uid))
    flash("Updated Successfully")
    return redirect(url_for('editProfile'))

@app.route('/forgotPassword')
def forgotPassword():
    return render_template('forgotPassword.html')


@app.route('/forgotPasswordAction',methods=['post'])
def forgotPasswordAction():
    username=request.form['username']
    s=sql_query2("select * from register_tb where username=?",[username])
    if len(s)>0:
        return render_template('forgotp.html')
    else:
        flash("username doesn't match")
    return redirect('forgotPassword')

@app.route('/forgotpAction',methods=['post'])
def forgotpAction():
    name=request.form['name']
    print(name)
    dob=request.form['dob']
    print(dob)
    phone=request.form['phone']
    print(phone)
    s=sql_query2("select * from register_tb where name=? and dob=? and phone=?",(name,dob,phone))
    print(s)
    if len(s)>0:
        return render_template('confirmation.html')
    else:
        flash("It doesn't match")
    return redirect(url_for('forgotPassword'))

@app.route('/confirmationAction',methods=['post'])
def confirmationAction():
    uid=session['id']
    print(uid)
    newpassword=request.form['newpassword']
    confirmpassword=request.form['confirmpassword']
    if newpassword == confirmpassword:
        user=sql_edit_insert("update register_tb set password=? where id=?",(newpassword,uid))
        flash("Password succesfully reset")
        return redirect(url_for('login'))
    
        
    
    




if __name__=='__main__':
    app.run(debug=True)
