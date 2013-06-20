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
	return rid

def main(argv):
	if len(argv) != 5:
		print('Usage: python3 %s useremail password adjacency_list_filename id_list_filename' % argv[0])
		return
	else:
		email, password, adjacency_list_fn, id_list_fn = argv[1], argv[2], argv[3], argv[4]
		adjacency_list_f = open(adjacency_list_fn, 'w')
		id_list_f = open(id_list_fn, 'w')
		my_rid = run(email, password)
		friends = pickle.load(open('my_friends_friendList.p','rb'))
		for p in friends.keys():
			print (p, end=" ", file=adjacency_list_f)
			print (' '.join(friends[p].keys()), file=adjacency_list_f)
		print (my_rid, 'Me', file=id_list_f)
		for rid, name in friends[my_rid].items():
			print (rid, name, file=id_list_f)

if __name__ == '__main__':
	main(sys.argv)
