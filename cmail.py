import smtplib 
# from Email.Message import email_message
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('taneemk14@gmail.com','glzm sdsd efvt ipzv')
    msg=EmailMessage()
    msg['FROM']='taneemk14@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg) 
    server.close()   