import sys, pickle
import spider

def run(email, password):
	spider.set_repo('repo_file')
	bot = spider.spider('my_friends', email, password)
	bot.log.setLevel(20)
	rid, login_info = bot.login()
	if rid is None:
		print('spider login error. detail:{}'.format(login_info))
		return
	else:
		print('spider login success. rid={}'.format(rid))
	spider.spider.getNet2(bot, rid)

def main(argv):
	if len(argv) != 3:
		print('Usage: python3 %s useremail password' % argv[0])
		return
	else:
		email, password = argv[1], argv[2]
		run(email, password)
		friends = pickle.load(open('my_friends_friendList.p','rb'))
		for p in friends.keys():
			print (friends[p].keys())

if __name__ == '__main__':
	main(sys.argv)
