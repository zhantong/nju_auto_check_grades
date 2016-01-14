import subprocess
from io import BytesIO
import urllib.request
from PIL import Image
import http.cookiejar
from urllib.parse import urlencode
from urllib.parse import urljoin
import re
import private
from email.mime.text import MIMEText
import smtplib
import logging
logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
					datefmt='%a,%d %b %Y %H:%M:%S',
					filename='app.log')
def image_to_string(img):
	res=subprocess.Popen(['tesseract',img,'stdout','-l eng', '-psm 6'],shell=False,stdout=subprocess.PIPE).communicate()[0]  # 生成同名txt文件
	return res.decode().strip().replace(' ','')
def get_verify_code(opener,url):
	threshold=(100,100,100)
	with opener.open(url) as f:
		imgBuf=BytesIO(f.read())
		img=Image.open(imgBuf)
		pix=img.load()
		for y in range(img.size[1]):
			for x in range(img.size[0]):
				if pix[x,y]>threshold:
					pix[x,y]=(255,255,255,255)
				else:
					pix[x,y]=(0,0,0,255)
	img.save('temp.png')
	text=image_to_string('temp.png')
	return text
def get_verify_code_auto_try(opener,url):
	try_count=10
	code_length=4
	while try_count:
		code=get_verify_code(opener,url)
		logging.debug('verify code:%s'%code)
		if len(code)==code_length:
			logging.info('verify code success (cannot make sure)')
			return code
		try_count-=1
		logging.debug('verify code failed')
	return -1
def login(opener):
	regular=re.compile(r'<input\s*type="hidden"\s*name="(.*?)"\s*value="(.*?)"\s*/?>')
	with opener.open('http://pyb.nju.edu.cn/') as f:
		content=f.read().decode()
		login_url=re.findall(r'<form id="login_form".*?action="(.*?)"\s*>',content)[0]
		login_form=regular.findall(content)
		login_form=dict(login_form)
	url='%s?%s'%(login_url,urlencode(login_form))
	with opener.open(url) as f:
		con=f.read().decode()
		verify_code_url=re.findall(r'<img id="vcodeimg" src="(.*?)"/>',con)[0]
		verify_code_url=urljoin(login_url,verify_code_url)
		r=regular.findall(con)
		r=dict(r)
	code=get_verify_code_auto_try(opener,verify_code_url)
	r['IDToken1'],r['IDToken2']=private.get_account_pwd()
	r['inputCode']=code
	with opener.open(login_url,data=urlencode(r).encode()) as f:
		content=f.read().decode()
		if content.find('验证码错误')==-1:
			return 0
		return -1
def login_auto_try(opener):
	try_count=10
	while try_count:
		if login(opener)==0:
			logging.info('login success')
			return 0
		try_count-=1
		logging.debug('login failed')
	return -1
def get_score(opener):
	reg_tr=re.compile(r'<tr.*?>\s*(.*?)\s*</tr>',re.S)
	reg_td=re.compile(r'<td.*?>\s*(.*?)\s*</td>',re.S)
	score_table=[]
	with opener.open('http://pyb.nju.edu.cn/student/queryScoreInfo.action') as f:
		con=f.read().decode()
		r=reg_tr.findall(con)
		for row in r:
			score_table.append(reg_td.findall(row))
	return score_table
def send_mail(score_table):
	text=''
	for row in score_table:
		for item in row:
			text+=item+'\t'
		text+='\n'
	msg=MIMEText(text)
	msg['Subject']='新的成绩信息'
	msg['From']='zhantong1994@163.com'
	msg['To']='zhantong1994@163.com'
	s=smtplib.SMTP(host='smtp.163.com')
	s.ehlo()
	s.starttls()
	s.ehlo()
	s.login(private.get_email_account(),private.get_email_password())
	s.send_message(msg)
	s.quit()
if __name__=='__main__':
	cj=http.cookiejar.CookieJar()
	opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
	login_auto_try(opener)
	score_table=get_score(opener)
	logging.info(score_table)
#	if len(score_table)!=2:
#		send_mail(score_table)