import spider

repo_name='my_net' #table name prefix
user='jiekunyang@gmail.com' #renren account
passwd=None #renren passwd

tt=spider.spider(repo_name,user,passwd)
my_rid,login_info=tt.login()
if my_rid is None:
	print('spider login error.detail:{}'.format(login_info))
else:
	print('spider login success.rid={}'.format(my_rid))

	tt.getProfile_friend(my_rid)
