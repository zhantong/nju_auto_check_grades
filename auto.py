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
def deal_with_image(file_path,file_name):
	threshold=(100,100,100)
	img=Image.open(file_path)
	pix=img.load()
	for y in range(img.size[1]):
		for x in range(img.size[0]):
			if pix[x,y]>threshold:
				pix[x,y]=(255,255,255,255)
			else:
				pix[x,y]=(0,0,0,255)
	img.save(file_name)
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
class Test:
	def __init__(self):
		cj=http.cookiejar.CookieJar()
		self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
		self.url='http://pyb.nju.edu.cn/'
	def get_verify_code(self,url):
		with self.opener.open(url) as f:
			imgBuf=BytesIO(f.read())
		deal_with_image(imgBuf,'temp.png')
		text=image_to_string('temp.png')
		return text
	def get_verify_code_auto_try(self,url):
		try_count=10
		code_length=4
		while try_count:
			code=self.get_verify_code(url)
			logging.debug('verify code:%s'%code)
			if len(code)==code_length:
				logging.info('verify code success (cannot make sure)')
				return code
			try_count-=1
			logging.debug('verify code failed')
		return -1
	def login(self):
		regular=re.compile(r'<input\s*type="hidden"\s*name="(.*?)"\s*value="(.*?)"\s*/?>')
		with self.opener.open(self.url) as f:
			content=f.read().decode()
			login_url=re.findall(r'<form id="login_form".*?action="(.*?)"\s*>',content)[0]
			login_form=regular.findall(content)
			login_form=dict(login_form)
		url='%s?%s'%(login_url,urlencode(login_form))
		with self.opener.open(url) as f:
			con=f.read().decode()
			verify_code_url=re.findall(r'<img id="vcodeimg" src="(.*?)"/>',con)[0]
			verify_code_url=urljoin(login_url,verify_code_url)
			r=regular.findall(con)
			r=dict(r)
		code=self.get_verify_code_auto_try(verify_code_url)
		r['IDToken1'],r['IDToken2']=private.get_account_pwd()
		r['inputCode']=code
		with self.opener.open(login_url,data=urlencode(r).encode()) as f:
			content=f.read().decode()
			if content.find('验证码错误')==-1:
				self.get_query_urls(content)
				return 0
			return -1
	def get_query_urls(self,content):
		base_url=re.findall(r'<base href="(.*?)">',content)[0]
		score_url=re.findall(r'<a href="(.*?)" title="成绩查看">',content)[0]
		score_url=urljoin(base_url,score_url)
		self.score_url=score_url
	def login_auto_try(self):
		try_count=10
		while try_count:
			if self.login()==0:
				logging.info('login success')
				return 0
			try_count-=1
			logging.debug('login failed')
		return -1
	def get_score(self):
		reg_tr=re.compile(r'<tr.*?>\s*(.*?)\s*</tr>',re.S)
		reg_td=re.compile(r'<td.*?>\s*(.*?)\s*</td>',re.S)
		score_table=[]
		with self.opener.open(self.score_url) as f:
			con=f.read().decode()
			r=reg_tr.findall(con)
			for row in r:
				score_table.append(reg_td.findall(row))
		return score_table
if __name__=='__main__':
	t=Test()
	t.login_auto_try()
	score_table=t.get_score()
	logging.info(score_table)
	if len(score_table)!=2:
		send_mail(score_table)