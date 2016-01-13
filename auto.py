import subprocess
from io import BytesIO
import urllib.request
from PIL import Image
import http.cookiejar
import urllib.parse
import re
import private
regular=re.compile(r'<input\s*type="hidden"\s*name="(.*?)"\s*value="(.*?)"\s*/?>')
def image_to_string(img):
	res=subprocess.Popen(['tesseract',img,'stdout','-l eng', '-psm 6'],shell=True,stdout=subprocess.PIPE).communicate()[0]  # 生成同名txt文件
	return res.decode().strip().replace(' ','')
def get_verify_code_back():
	url='http://cer.nju.edu.cn/amserver/verify/image.jsp'
	r=urllib.request.urlopen(url)
	imgBuf=BytesIO(r.read())
	img=Image.open(imgBuf)
	#img=img.convert('RGBA')
	pix=img.load()
	for y in range(img.size[1]):
		for x in range(img.size[0]):
			if pix[x,y][0]>100 and pix[x,y][1]>100 and pix[x,y][2]>100:
				pix[x,y]=(255,255,255,255)
			else:
				pix[x,y]=(0,0,0,255)
	img.save('temp.png')
	text=image_to_string('temp.png')
	return text
def get_verify_code(opener,url):
	with opener.open(url) as f:
		imgBuf=BytesIO(f.read())
		img=Image.open(imgBuf)
		pix=img.load()
		for y in range(img.size[1]):
			for x in range(img.size[0]):
				if pix[x,y][0]>100 and pix[x,y][1]>100 and pix[x,y][2]>100:
					pix[x,y]=(255,255,255,255)
				else:
					pix[x,y]=(0,0,0,255)
	img.save('temp.png')
	text=image_to_string('temp.png')
	return text
def login(opener):
	params=urllib.parse.urlencode({
		'goto':'http://pyb.nju.edu.cn/loginredirect.action',
		'gotoOnFail':'http://pyb.nju.edu.cn/login.action'
		})
	url='http://cer.nju.edu.cn/amserver/UI/Login?%s'%params
	with opener.open(url) as f:
		con=f.read().decode()
		r=regular.findall(con)
		r=dict(r)
	code=get_verify_code(opener,'http://cer.nju.edu.cn/amserver/verify/image.jsp')
	r['IDToken1'],r['IDToken2']=private.get_account_pwd()
	r['inputCode']=code
	with opener.open('http://cer.nju.edu.cn/amserver/UI/Login',data=urllib.parse.urlencode(r).encode()) as f:
		print(f.read().decode())
def get_score(opener):
	reg_tr=re.compile(r'<tr.*?>\s*(.*?)\s*</tr>',re.S)
	reg_td=re.compile(r'<td.*?>\s*(.*?)\s*</td>',re.S)
	with opener.open('http://pyb.nju.edu.cn/student/queryScoreInfo.action') as f:
		con=f.read().decode()
		r=reg_tr.findall(con)
		print(reg_td.findall(r[0]))
		print(reg_td.findall(r[1]))
if __name__=='__main__':
	cj=http.cookiejar.CookieJar()
	opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
	login(opener)
	get_score(opener)