from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
import mysql.connector
from cmail import sendmail
from otp import genotp
from tokens import encode,decode
from flask_session import Session
from io import BytesIO
import flask_excel as excel
import re
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
app.secret_key='taneem^11'
Session(app)
mydb=mysql.connector.connect(host='localhost',user='root',password='Taneem_2002',db='snmproject')
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        username=request.form['user_name']
        uemail=request.form['email']
        password=request.form['password']
        conformpassword=request.form['confirm_password']
        cursor=mydb.cursor()
        cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
        result=cursor.fetchone()
        print(result)
        if result[0]==0:
            gotp=genotp()
            # print(gotp)
            udata={'username':username,'useremail':uemail,'pword':password,'otp':gotp}
            subject='OTP for simple notes manager'
            body=f' otp for regrestation of simple notes manage {gotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('OTP has sent to ur mail')
            return redirect(url_for('otp',enudata=encode(data=udata)))
        elif result[0]>0:
            flash('email already exist use other email or login to ur account')
            return redirect(url_for('login'))
        else:
            return 'something went wrong'
    return render_template('create.html')

@app.route('/otp/<enudata>',methods=['GET','POST'])
def otp(enudata):
    if request.method=='POST':
        eotp=request.form['eotp']
        try:
            dudata=decode(data=enudata)
            
        except Exception as e:
            print(e)
            return 'something went wrong'
        else:
            if dudata['otp']==eotp:
                cursor=mydb.cursor()
                cursor.execute('insert into users(username,useremail,password) values(%s,%s,%s)',[dudata['username'],dudata['useremail'],dudata['pword']])
                mydb.commit()
                cursor.close()
                flash('registration successful')
                return redirect(url_for('login'))
            else:
                return 'wrong otp'
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if not session.get('user'):
        if request.method=='POST':
            uemail=request.form['email']
            pword=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
            bdata=cursor.fetchone()   # (1,) or (0,)
            if bdata[0]==1:
                cursor.execute('select password from users where useremail=%s',[uemail])
                bpassword=cursor.fetchone() #(password kya heyh ki o a place mayaata,)
                if bpassword[0].decode('utf-8')==pword:
                    # print(session)
                    session['user']=uemail
                    # print(session)
                    return redirect(url_for('dashboard'))
                else:
                    flash('password is wrong')
                    return redirect(url_for('login'))
            elif bdata[0]==0:
                flash('Email does not exist')
                return redirect(url_for('create'))
            else:
                return 'something went wrong please try after some time'
        # dudata=decode(data=enudata)
        # uname=request.form['user_name']
        # if dudata['username']==uname:

        return render_template('login.html')
    else:
        return redirect('dashboard')
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('home'))

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            if uid:
                try:
                    cursor.execute('insert into notes(title,n_description,user_id) values(%s,%s,%s)',[title,description,uid[0]])
                    mydb.commit()
                    cursor.close()
                except mysql.connector.errors.IntegrityError:
                    flash('Duplicate Title Entry')
                    return redirect(url_for('dashboard'))
                except mysql.connector.errors.ProgrammingError:
                    flash('could not add notes')
                    print(mysql.connector.errors.ProgrammingError)
                    return redirect(url_for('dashboard'))
                else:
                    flash('notes added succesfully')
                    return redirect(url_for('dashboard'))
            else:
                return 'something went wrong'
        return render_template('addnotes.html')
    else:
        return redirect(url_for('welcome'))
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select n_id,title,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall()  # aisa aata is ka output [(1,	python,	2024-12-14 12:37:18),(4,sql,2024-12-14 21:46:26)]
        except Exception as e:
            print(e)
            flash('no data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',ndata=ndata)
    else:
        return redirect(url_for('welcome'))
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select * from notes where n_id=%s',[nid])
            ndata=cursor.fetchone() # (1,python,'jhgvb',2024-12-14 12:37:18)
        except Exception as e:
            print(e)
            flash('no data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',ndata=ndata)
    else:
        return redirect(url_for('welcome'))

@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where n_id=%s',[nid])
        ndata=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update notes set title=%s,n_description=%s where n_id=%s',[title,description,nid])
            mydb.commit()
            cursor.close()
            flash('notes updated successfully')
            return redirect(url_for('viewnotes',nid=nid))
        return render_template('updatenotes.html',ndata=ndata)
    else:
        return redirect(url_for('welcome'))

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('delete from notes where n_id=%s',[nid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not delete notes')
            return redirect(url_for('viewallnotes'))
        else:
            flash('notes deleted succesfully')
            return redirect(url_for('viewallnotes'))
    else:
        return redirect(url_for('welcome'))
    
@app.route('/uplodefile',methods=['GET','POST'])
def uplodefile():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            # print(filedata)
            # print(filedata.read())
            fname=filedata.filename
            fdata=filedata.read()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
                mydb.commit()
            except Exception as e:
                print(e)
                flash('could not uplode the file')
                return redirect(url_for('dashboard'))
            else:
                flash('file uploded succesfully')
                return redirect(url_for('dashboard'))
        return render_template('fileup.html')
    else:
        return redirect(url_for('welcome'))

@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[uid[0]])
            fdata=cursor.fetchall()  # aisa aata is ka output [(1,	python,	2024-12-14 12:37:18),(4,sql,2024-12-14 21:46:26)]
            print(fdata)
        except Exception as e:
            print(e)
            flash('no data found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallfiles.html',fdata=fdata)
    else:
        return redirect(url_for('welcome'))
    
@app.route('/viewfile/<nid>')
def viewfile(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[nid])
            fdata=cursor.fetchone() # (1,python,'jhgvb',2024-12-14 12:37:18)
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
        except Exception as e:
            print(e)
            flash('cannot open file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('welcome'))
@app.route('/downloadfile/<nid>')
def downloadfile(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[nid])
            fdata=cursor.fetchone() # (1,python,'jhgvb',2024-12-14 12:37:18)
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash('cannot open file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('welcome'))

@app.route('/deletefile/<nid>')
def deletefile(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('delete from filedata where fid=%s',[nid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not delete file')
            return redirect(url_for('viewallfiles'))
        else:
            flash('file deleted succesfully')
            return redirect(url_for('viewallfiles'))
    else:
        return redirect(url_for('welcome'))

@app.route('/d=getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select n_id,title,n_description,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall()
            print('ndata',ndata)
        except Exception as e:
            print(e)
            flash('no data found')
            return redirect(url_for('dashboard'))
        else:
            array_data=[list(i) for i in ndata]
            columns=['Notesid','Title','content','created_time']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',file_name='notesdata')
    else:
        return redirect(url_for('welcome'))

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        redirect(url_for('login'))

@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
    #    print(request.form)
    #    return 'hi'
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE)
                if (pattern.match(sdata)):
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select * from notes where n_id like %s or title like %s or n_description like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('no data found')
                    return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Cantfind anything')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
# <a> tag just redirect kartaaa but action tag data kosa page may jana ki usay o page ku bhejtaa
app.run(use_reloader=True,debug=True)