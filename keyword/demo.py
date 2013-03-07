import pymysql
import jieba

def getStatus(rid,table_pre='orig_renren'):
	tablename='{}_{}'.format(table_pre,'status')
	conn=pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='Kunth123', db='data_bang',charset='utf8')
	cur=conn.cursor()
	cur.execute("select timestamp,cur_content from {} where renrenId1='{}'".format(tablename,rid))
	res={}
	for content in cur.fetchall():
		res[content[0]]=content[1]
	cur.close()
	conn.close()
	return res

kword=dict()
for timestamp,status in getStatus('233330059').items():
	for word in jieba.cut(status,cut_all=False):
		try:
			kword[word]=kword.get(word,[])
			kword[word].append(timestamp)
		except AttributeError:
			print(u'{},{}'.format(timestamp,word))

print(len(kword))
