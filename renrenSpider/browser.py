"""provide interface to browser data of a certain pageStyle of someone from www.renren.com"""
import urllib.request
from urllib.parse import urlencode
import http.cookiejar

import socket

import re
import time

import parse

run_level='info'
timeout=3
max_timeout=5
resend_n=3
urls={
	'login':"http://www.renren.com/PLogin.do",
	'friendList':"http://friend.renren.com/GetFriendList.do?curpage={}&id={}",
	'profile_detail':"http://www.renren.com/{}/profile?v=info_ajax",
	'homepage':"http://www.renren.com/{}/profile",
	'status':'http://status.renren.com/status?curpage={}&id={}&__view=async-html'
	}
itemReg={
	'status':re.compile(r'<li data-wiki = "" id="status-\d+">.*?</li>',re.DOTALL),
	'friendList':re.compile(r'<dd><a\s+href="http://www.renren.com/profile.do\?id=\d+">[^<]*</a>'),
	'profile_detail':re.compile(r'<dl\sclass="info">.*?</dl>',re.DOTALL),
	'profile_tl':re.compile(r'<ul class="information-ul".*?</ul>',re.DOTALL),
	'safety':re.compile(r'<title>.*?安全.*?</title>'),
	'profile_basic':re.compile(r'<ul class="user-info clearfix">.*?</ul>',re.DOTALL)}

def format_time(runtime,req_time):
	if isinstance(req_time,list):
		import numpy as np
		tm=np.float32(req_time)
		return '%.2f,max/min/ave:%.2f/%.2f/%.2f'%(runtime,tm.max(),tm.min(),tm.mean())
	else:
		return 'timecost should be list'

_url2fileprog=None
def url2file(url):
	global _url2fileprog
	if _url2fileprog is None:
		import re
		_url2fileprog=re.compile(r'http://(\w+).renren.com/(?:\D+)?(\d+)\D+(\d+)?')
	m=_url2fileprog.search(url)
	if m is None:
		return 'test_data/timeout.html'
	else:
		if m.group(3) is None:
			return 'test_data/{}_{}_profile.html'.format(m.group(1),m.group(2))
		else:
			return 'test_data/{}_{}_{}.html'.format(m.group(1),m.group(3),m.group(2))

class browser:
	def __init__(self,user='yyttrr3242342@163.com',passwd=None):
		self.user=user
		self.passwd=passwd

	def friendList(self,renrenId='285060168',uppage=100):
		"""friendList(renrenId:str) --> (record:dict(),timecost:str)
		return (None,info) if error occurs, such as timeout or safetyPage"""
		#generate request list
		return self._iter_page('friendList',renrenId,None,range(0,uppage))
	def status(self,renrenId='285060168',uppage=100):
		"""status('285060168') --> 
		(statusId,cur_content,orig_content,timestamp)"""
		return self._iter_page('status',renrenId,None,range(0,uppage))

	def profile(self,renrenId):
		"""profile('234234') -->
		return {tag1:value1,...,tagn:valuen} in detail page if available
		return {tag1:value1,...,tagn:valuen} in homepage if detail page unavailable
		return None if timeout"""
		pageStyle='profile_detail'
		html_content=self._download(urls[pageStyle].format(renrenId))
		if html_content is None:
			return None,'profile'
		elif html_content[0:30].find('<div class="col-left">') > -1:
			return parse.profile_detail(itemReg[pageStyle].findall(html_content)),'pf_detail'
		elif html_content[0:30].find('<!doctype html><html>') > -1:#tl
			#TODO:check whether account safety
			return parse.homepage_tl(itemReg['profile_tl'].findall(html_content)),'mini_tl'
		else:
			return parse.homepage_basic_privacy(itemReg['profile_basic'].findall(html_content)),'mini_basic'

	def login(self,user=None,passwd=None):
		"""return (renrenId,'success') if login successfully.
		return (None,info) if failed."""
		if user is None:
			user=self.user
			passwd=self.passwd
		if passwd is None:
			import mytools #used to get passwd from personal mysql
			passwd=mytools.getPasswd('renren',user)
		data=urlencode({"email":user,"password":passwd}).encode(encoding='UTF8');
		hdlr_cookie=urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
		self.opener=urllib.request.build_opener(hdlr_cookie)
		self.opener.addheaders=[('User-agent','Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0')];
		try:
			rsp=self.opener.open(urls['login'],data,timeout=timeout)
			url=rsp.geturl()
		except socket.timeout as e:
			return None,'timeout'
		except urllib.error.URLError as e:
			return None,'timeout'
		else:
			#check whether login is successful. 
			m=re.compile(r'http://www.renren.com/(\d+)').match(url)
			if m is None:
				return None,'login failed,rsp={}'.format(url)
			else:
				return m.group(1),'login success'

	def process(self,pageStyle,renrenId='285060168',uppage=100):
		"""pageStyle browser handler.
		call _iter_page to request pages and detect items,
		parse record from items by parse module.runtime is logged."""
		runtime_start=time.time()
		req_time=[]
		items=self._iter_page(pageStyle,renrenId,range(0,uppage),req_time)
		meth_parse=getattr(parse,pageStyle)
		record=meth_parse(items)
		runtime=time.time()-runtime_start
		return record,format_time(runtime,req_time)

	def _download(self,url,request_time=None):
		"""onePage(url) --> html_content:str
		return None if timeout."""
		request_start=time.time()
		try:
			rsp=self.opener.open(url,timeout=timeout)
			html_content=rsp.read().decode('UTF-8','ignore')
			if request_time is not None:
				request_time.append(time.time()-request_start)
			if run_level == 'debug':
				print('debug.saved:{}'.format(url))
				f=open(url2file(url),'w')
				f.write(html_content)
				f.close()
		except socket.timeout as e:
			return None
		except urllib.error.URLError as e:
			return None
		else:
			return html_content

	def _iter_page(self,pageStyle,rid,req_time=None,pages=range(0,100),resend=None):
		"""_iter_page(pageStyle,rid)  --> items:set()
		return None if error"""
		if resend is None:
			resend=resend_n
		if resend<0:
			return None
		itemsAll=set()
		timeout_seq=list()
		#request pages until no more items detected
		for curpage in pages:
			html_content=self._download(urls[pageStyle].format(curpage,rid),req_time)
			if html_content is None:#add to timeout_seq to resend later.
				timeout_seq.append(curpage)
				#break when much more timeout than normal 
				if len(timeout_seq) > max_timeout:
					return None
			else:
				items_curpage=itemReg[pageStyle].findall(html_content)#detect items
				if len(items_curpage) > 0:
					itemsAll.update(items_curpage)
				else:#privacy/all pages requested/safety page
					break
		#deal with timeout_seq
		print('timeout list:{}'.format(timeout_seq))
		if timeout_seq:#resend
			item_re=self._iter_page(pageStyle,rid,req_time,timeout_seq,resend-1)
			print('pages: {}'.format(pages))
			if item_re is None:
				return None
			else:
				itemsAll.update(item_re)
		#_safety page check, if empty.
		print('{},{},{},resend={}'.format(len(itemsAll),rid,pageStyle,resend)) 
		if (len(itemsAll) ==0) and self._is_safety_page(html_content):
				return None
		return itemsAll

	def _is_safety_page(self,html_content):
		print('checked')
		if html_content is None:
			print('None html_content')
			return False
		pageStyle='safety'
		m=itemReg[pageStyle].search(html_content)
		if m is None:
			return False
		else:
			return True



	#@depraced
	def homepage(self,renrenId):
		pageStyle='homepage'
		html_content=self._download(urls[pageStyle].format(renrenId))
		if html_content is None:
			return set()
		elif html_content[0:30].find('<!doctype html><html>') > -1:#tl
			return parse.homepage_tl(itemReg[pageStyle+'_tl'].findall(html_content))
		else:
			return parse.homepage_basic(itemReg[pageStyle+'_basic'].findall(html_content))
	#@depraced
