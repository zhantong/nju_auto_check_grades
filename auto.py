import subprocess
from io import BytesIO
import urllib.request
from PIL import Image
import http.cookiejar
from urllib.parse import urlencode
from urllib.parse import urljoin
import re
import private

def image_to_string(img):
	res=subprocess.Popen(['tesseract',img,'stdout','-l eng', '-psm 6'],shell=True,stdout=subprocess.PIPE).communicate()[0]  # 生成同名txt文件
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
		if len(code)==code_length:
			return code
		try_count-=1
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
			return 0
		try_count-=1
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
	print(score_table)
if __name__=='__main__':
	cj=http.cookiejar.CookieJar()
	opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
	login_auto_try(opener)
	get_score(opener)