'''
Created on 2017.7.30
断句;分词;词性标注;主题词提取;关键词提取;
@author: HDE He na
Vesion 0.0.1
Tips:
需要添加stopwords，词云直接采用TFIDF关键词提取算法
'''
import json
import sys
import re
import traceback

import jieba.posseg as pseg
import jieba.analyse

def loadDictDataSet(filename):
	import json
	AllData = []
	try:
		with open(filename) as load_f:
			load_dict = json.load(load_f)
			for item in load_dict:
				AllData.append(item)
	except:
		traceback.print_exc()
	return AllData

def grabTxtData(filename):
	data = []
	with open(filename,'r') as f:
		for line in f.readlines():
			data.append(line.strip())
	return data

POINTSLIST = grabTxtData('points.txt')
POINTSLIST.append('\xa0')
#SpaceLIST = []
#SpaceLIST.append('\xa0')
CNnegComentWords = grabTxtData('./PolarWords/中文负面评价词语.txt')
CNnegSentimentWords = grabTxtData('./PolarWords/中文负面情感词语.txt')
#CNposComentWords = grabTxtData('./PolarWords/中文正面评价词语.txt')
CNposComentWords = []
#CNposSentimentWords = grabTxtData('./PolarWords/中文正面情感词语.txt')
CNposSentimentWords = []
#CNadvocateWords = grabTxtData('./PolarWords/中文主张词语.txt')
CNadvocateWords = []

#CNpolarWords = CNadvocateWords + CNnegComentWords + CNnegSentimentWords +CNposComentWords + CNposSentimentWords

# 副词强度
ADMOST = grabTxtData('./PolarWords/most.txt') # 权重是2
ADVERY = grabTxtData('./PolarWords/very.txt') # weight=1.7
ADMORE = grabTxtData('./PolarWords/more.txt') # weight=0.9
ADLITTLE = grabTxtData('./PolarWords/little.txt') # weight=0.7

def ScoreOfAD(ad, mostDict=ADMOST, veryDict=ADVERY, moreDict=ADMORE, littleDict=ADLITTLE):
	try:
		if ad in mostDict:
			return 2
		if ad in veryDict:
			return 1.7
		if ad in moreDict:
			return 0.9
		if ad in littleDict:
			return 0.7
	except:
		print("副词 %s 不在副词词典库中，请人工判断并添加" %(str(ad)))
		return 1 

def ScoreOfPolar(word, negDict1=CNnegComentWords, negDict2=CNnegSentimentWords, posDict1=CNposComentWords, posDict2=CNposSentimentWords):
	try:
		if word in negDict1 or word in negDict2:
			return -1
		if word in posDict1 or word in posDict2:
			return 1
	except:
		print("词 %s 不在情感词典库中，请人工判断并添加" %(str(word)))
		return 0

def getCommentSingleData(alldata, key='具体评论'):
	CommentData = []
	for i in range(len(alldata)):
		if key in alldata[i]:
			CommentData.append(alldata[i][key])
	return CommentData

def findAllPointsIndex(x,y=POINTSLIST):
	ans = [i for i,a in enumerate(x) if a in y]
	return ans

# 对一个句子分词并词性标注
def TaggingWordSegmentation(sentence):
	words = pseg.cut(sentence)
	Word, Flag = [], []
	for word, flag in words:
		Word.append(word)
		Flag.append(flag)
	return Word,Flag

# 获取句子中的形容词的位置
def getAdjIndex(sentence):
	words = pseg.cut(sentence)
	Word, Flag = [], []
	AdjIndex = []
	#DorADIndex = [] #副词
	i = 0
	for word, flag in words:
		if flag == 'a':
			AdjIndex.append(i)
		'''
		if flag == 'd' or flag == 'ad':
			DorADIndex.append(i)
		'''
		Word.append(word)
		Flag.append(flag)
		i += 1
	return Word, Flag, AdjIndex

def IsNoun2Phrasses(flag,index):
	# 后面可以试试 后面加的n词也是名词短语的情况 第一版就按n去辨别
	# 如水煮牛肉和红烧排骨 目前只能识别出 牛肉和排骨
	# adj+n
	if flag[index] == 'a' and flag[index+1] == 'n':
		return True
	# n+v
	if flag[index] == 'n' and flag[index+1] == 'v':
		return True
	# 区别词+n 副书记
	if flag[index] == 'b' and flag[index+1] == 'n':
		return True
	# n+n
	if flag[index] == 'n' and flag[index+1] == 'n':
		return True
	# if flag[index] == 'v' and flag[index+1] == 'n':
	return False

def IsNoun3Phrasses(flag,index):
	# n+连词（c）+n
	if flag[index] == 'n' and flag[index+1] == 'c' and flag[index+2] == 'n':
		return True
	# n+的（uj）+n
	if flag[index] == 'n' and flag[index+1] == 'uj' and flag[index+2] == 'n':
		return True
	# 动名词组合 这个不知道主要组成暂定
	return False

所有的极性词有
def SentenceSegmentation(comment,pointslist=POINTSLIST):
	'''
	sentence segmentation:comment(str) -->sentence(list)
	'''
	Sentence = []
	Indeterminate = ''
	PointsIndex = findAllPointsIndex(comment)
	breakpoints = len(PointsIndex) # 切割点的大小为了得到后一个
	#SpaceIndex = findAllPointsIndex(comment,SpaceLIST)
	#sort(PointsIndex)
	# 如果句子长度小于6或者里面没有特定的符号的话，认为这就是一个不能分割的最短的句子了
	SentBasic = 7
	if len(comment) <= SentBasic or breakpoints <=1:
		return [comment]
	# 符号间的间距小于6（这个值需要研究或修改）的归入下一条句子
	for i in range(breakpoints):
		endS = PointsIndex[i]
		if i == 0:
			if endS < SentBasic:
				Indeterminate = comment[:endS+1]
			else:
				Sentence.append(comment[:endS+1])
		else:
			beginS = PointsIndex[i-1]
			LenOfSentence = endS - beginS
			#if breakpoints-i > 1 and LenOfSentence < SentBasic:
			if LenOfSentence < SentBasic:
				Indeterminate += comment[beginS+1:endS+1]
			else:
				addSentence = Indeterminate + comment[beginS+1:endS+1]
				Indeterminate = ''
				Sentence.append(addSentence)
	# 对最后一个符号做特殊处理，是归入上一条
	addSentence = Indeterminate + comment[PointsIndex[-1]+1:]
	if len(comment) - PointsIndex[-1] < SentBasic:
		Sentence[-1] += addSentence
	else:
		Sentence.append(addSentence)
	
	return Sentence

def printSegmentation(sentencelist):
	# [a,...,b] --> a/.../b  
	for item in sentencelist:
		print(item + '/')

def getTopicAndPolarWords(comment):
	# 返回的第一个是主题词对：[(主题词，极性词),(),...,()]
	# 返回的第二个是索引：[([3,2],1)] --> topic是index 3到5,polar是 1
	# 返回的第三个是整个评论的分数
	# NumOfPos:负极性词的个数
	# 第一版是严格按照语法来，第二版采用窗口的方式做对照
	TopicAndPolar = []
	TAPIndex = []
	NumOfPos, NumOfNeg = 0, 0
	ScoreOfPos, ScoreOfNeg = 0, 0
	ScoreOfSent = []
	Sentence = SentenceSegmentation(comment)
	print("=========================================================")
	print("断句结果为：")
	printSegmentation(Sentence)

	for s in Sentence:
		Word, Flag, AdjIndex = getAdjIndex(s)
		for adj in AdjIndex:
			S = ScoreOfPolar(Word[adj]) #这个词的极性
			AD1, AD2 = 1, 1
			# 根据评论中常用的语法模式提取主题词+极性词
			try: # adj+uj+n
				if Flag[adj+1] == 'uj':
					if IsNoun2Phrasses(Flag,adj+2):
						# 漂亮的摆饰
						addWord = Word[adj+2]+Word[adj+3]
						TopicAndPolar.append((addWord, Word[adj]))
						# [([3,2],1)] --> topic是index 3到5,polar是 1
						TAPIndex.append(([adj+2,2],adj))	
					else:
						if IsNoun3Phrasses(Flag,adj+2):
							addWord = Word[adj+2] + Word[adj+3] + Word[adj+4]
							TopicAndPolar.append((addWord, Word[adj]))
							TAPIndex.append(([adj+2, 3], adj))
						elif Flag[adj+2] == 'n':
							TopicAndPolar.append((Word[adj+2], Word[adj]))
							TAPIndex.append(([adj+2, 1], adj))
		    # n+adj
			except: 
				if IsNoun2Phrasses(Flag, adj-2):
					addTopic = Word[adj-2] + Word[adj-1]
					TopicAndPolar.append((addTopic, Word[adj]))
					TAPIndex.append(([adj-2, 2], adj))
				else:
					if IsNoun3Phrasses(Flag, adj-3):
						addTopic = Word[adj-3] + Word[adj-2] + Word[adj-1]
						TopicAndPolar.append((addTopic, Word[adj]))
						TAPIndex.append(([adj-3, 3], adj))
					else:
						if Flag[adj-1] == 'n':
							TopicAndPolar.append((Word[adj-1], Word[adj]))
							TAPIndex.append(([adj-1,1], adj))
			# n+adv+adj & n+adv+adv+adj
			try: 
				if Flag[adj-1] == 'd' or Flag[adj-1] == 'ad':
					AD1 = ScoreOfAD(Flag[adj-1])
					if Flag[adj-2] == 'd' or Flag[adj-2] == 'ad':
						AD2 = ScoreOfAD(Flag[adj-2]) # 第二个副词的程度
						if IsNoun2Phrasses(Flag, adj-4):
							addTopic = Word[adj-4] + Word[adj-3]
							TopicAndPolar.append((addTopic,Word[adj]))
							TAPIndex.append(([adj-4, 2], adj))
						else:
							if IsNoun3Phrasses(Flag, adj-5):
								addTopic = Word[adj-5]+Word[adj-4]+Word[adj-3]
								TopicAndPolar.append((addTopic, Word[adj]))
								TAPIndex.append(([adj-5, 3], adj))
							else:
								if Flag[adj-3] == 'n':
									TopicAndPolar.append((Word[adj-3], Word[adj]))
									TAPIndex.append(([adj-3, 1], adj))
					else:
						if IsNoun2Phrasses(Flag, adj-3):
							addTopic = Word[adj-3] + Word[adj-2]
							TopicAndPolar.append((addTopic, Word[adj]))
							TAPIndex.append(([adj-3, 2], adj))
						else:
							if IsNoun3Phrasses(Flag, adj-4):
								addTopic = Word[adj-4]+Word[adj-3]+Word[adj-2]
								TopicAndPolar.append((addTopic, Word[adj]))
								TAPIndex.append(([adj-4, 3], adj))
							else:
								if Flag[adj-2] == 'n':
									TopicAndPolar.append((Word[adj-2], Word[adj]))
									TAPIndex.append(([adj-2, 1], adj))
			except:
				print("形容词%s无匹配,原句为:%s" %(str(Word[adj]), str(s))) # 应该输出哪一个词没有匹配需要人工审查
			if S == 1:
				NumOfPos += 1
				ScoreOfPos += AD1 * AD2
			if S == -1:
				NumOfNeg += 1
				#ScoreOfNeg += (-1) * AD1 * AD2
			# ScoreOfSent += S * AD1 * AD2
	#return TopicAndPolar, TAPIndex, ScoreOfSent
	return TopicAndPolar, TAPIndex

def main():
	comment = input("请输入测试的评论：")
	keywordslist = jieba.analyse.extract_tags(comment, topK=6, withWeight=False, allowPOS=())
	print("整个评论中的关键词如下：", str(keywordslist))
	print("=========================================================")
	#print("=========================================================")
	#TopicAndPolar, TAPIndex, ScoreOfSent = getTopicAndPolarWords(comment)
	TopicAndPolar, TAPIndex = getTopicAndPolarWords(comment)
	#print("该评论的情感强烈程度分数为：")
	#print(ScoreOfSent)
	#print("=========================================================")
	print("具体意见有如下：", TopicAndPolar)
	print("=========================================================")


if __name__ == '__main__':
	main()