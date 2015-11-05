##Changes for V1.6 include
##- Add new deck libraries (Includes reading a PDF file [finished by hand])
##- Get Statistics (thinking)
##- New categorization of words to review faster (thinking)
##Changes for V1.5 include
##- Test to write word
##Changes for V1.4 include
##- Special request of words (by alphabet)
##Changes for V1.3 include
##- Limit the number of words per session
##- Used words can be loaded from external file
##- Add repeat function using REPEAT_QUESTION tag
##- Select by static probability which quiz to test according to current random words
##Changes for V1.2 include
##- Words are used as classes

##Requires:
##- ColorMessage

##Generates:
##- Word lists on /data/wordlist/ (can create its own lists)
##- Word sentences on /data/sentences/ (can create its own lists)
##- Word progress on /data/progress/ (can create its own lists)

import json
import urllib
import requests

##from PyPDF2 import PdfFileWriter, PdfFileReader

import random
from datetime import datetime

import os
import time

from StringIO import StringIO

import ColorMessage as CM

CHANGE_SENTENCE     =   -1
QUIT_TEST           =   -2
SHOW_DEFINITIONS    =   -3
SKIP_QUESTION       =   -4
USAGE_EXAMPLES      =   -5
USAGE_WORD_EXAMPLES =   -6
REPEAT_QUESTION     =   -7
STRING_SOLUTION     =   -8

STATUS_NEW      =   1
STATUS_MISTAKEN =   2
STATUS_LEARNING =   3
STATUS_LEARNED  =   4
STATUS_SKIPPED  =   5

TEST_NEW        =   1
TEST_LEARNED    =   2
TEST_LEARNING   =   3

QUIZ_SHOW       =   0
QUIZ_WORD       =   1
QUIZ_WRITE_WORD =   2
QUIZ_MEANING    =   3
QUIZ_SENTENCE   =   4

TRUE    =   1
FALSE   =   0

q   =   QUIT_TEST
c   =   CHANGE_SENTENCE
d   =   SHOW_DEFINITIONS
s   =   SKIP_QUESTION
r   =   REPEAT_QUESTION
u   =   USAGE_EXAMPLES
uu  =   USAGE_WORD_EXAMPLES
y   =   TRUE
n   =   FALSE

TOP_HARD_WORDS_PRIORITY =   10
TOP_LESS_SEEN_WORDS     =   10
NEW_WORDS_PER_SESSION   =   10
OPTIONS_PER_QUESTION    =   5
ENABLE_SENTENCES_SEARCH =   0.1#FALSE

class newWord:
    def __init__(self,newDataEntry,state=None,viewed=None,avg_time=None):
        self.word=newDataEntry[0].lower()
        self.meaning=[]
        if type(newDataEntry[1])==str:
            if len(newDataEntry[1])>0:
                self.meaning.append(newDataEntry[1].encode('ascii','ignore'))
        else:
            #list type
            for each in newDataEntry[1]:
                self.meaning.append(each)
        if state==None:
            self.state=STATUS_NEW
        else:
            self.state=state
        if viewed==None:
            self.viewed=0
        else:
            self.viewed=viewed
        if avg_time==None:
            self.avg_time=0
        else:
            self.avg_time=avg_time
    def setTag(self,tag):
        self.tag=tag
    def addMeaning(self,newDataEntry):
        if len(newDataEntry[1])>0:
            if newDataEntry[1] not in self.meaning:
                self.meaning.append(newDataEntry[1])
    def getStatus(self):
        return self.state
    def getMeaning(self):
        if len(self.meaning)>0:
            return random.choice(self.meaning)
        else:
            #TASK: find a way that the user input new meaning
            return "No avaiable meaning"
    def convertArray(self):
        return [[self.word,self.meaning],self.state,self.viewed,round(self.avg_time,2)]
    def addNewAnswer(self,newAnswer):
        if newAnswer:
            if self.state==STATUS_NEW:
                self.state=STATUS_LEARNED
            elif self.state==STATUS_MISTAKEN:
                self.state=STATUS_LEARNING
            elif self.state==STATUS_LEARNING:
                if self.viewed>2:
                    self.state=STATUS_LEARNED
            elif self.state==STATUS_LEARNED:
                self.state=STATUS_LEARNED
        else:
            self.state=STATUS_MISTAKEN
            self.viewed=0
            self.avg_time=0
    def addNewTime(self,newTime):
        self.avg_time=((self.avg_time*self.viewed)+newTime)/(self.viewed+1)
        self.viewed+=1
    def updateResult(self,Answer,Time):
        self.addNewAnswer(Answer)
        if Answer:
            self.addNewTime(Time)
        
class MyTest:
    def __init__(self):
        self.name                   =   "Get Sample test for GRE by J.Sanchez"
        self.version                =   "v1.6"
        self.wordListPath           =   "\\data\\wordlist\\"
        self.sentencesPath          =   "\\data\\sentences\\"
        self.saveProgressPath       =   "\\data\\progress\\"
        self.currentQuerryHTML      =   ""
        self.sentenceExamples       =   []
        self.word                   =   ''
        self.currentWordDetailts    =   None
        self.wordList               =   []
        self.randomNumbers          =   []
        self.Nsolution              =   0
        self.tries                  =   0
        self.skipped                =   0
        self.limitWordsPerSession   =   NEW_WORDS_PER_SESSION
        self.quizMode               =   None
        self.Intents                =   1       
        self.options                =   OPTIONS_PER_QUESTION
        self.prob_test_new          =   0.5
        self.prob_learned           =   0.3
        self.prob_learning          =   0.2
        random.seed(datetime.now())
        print CM.CORRECT+self.name,self.version
        self.separatingLine()
    def separatingLine(self):
        print CM.NORMAL+35*'+'
    def getWordsList_wordsinasentence_web(self):
        page = requests.get("http://wordsinasentence.com/vocabulary-word-list/")
        newWordListDef=page.text.split("</a> ")[1:]
        del page
        newWordList=[]
        for i in range(len(newWordListDef)-1):
            newWordListDef[i]=newWordListDef[i].split("<a href=\"")[-1]
            link=newWordListDef[i].split("\"")[0]
            newWordListDef[i]=newWordListDef[i].split("<p style=\"font-family:arial;font-size:16px;\">")[1]
            text=requests.get(link).text.split("bottom:1px;line-height:140%;\">")[1]
            newWordList.append([newWordListDef[i],text.split("</p>")[0]])
            print [newWordListDef[i],text.split("</p>")[0]]
        return newWordList
    def getWordsList_wordsinasentence(self):
        label="getWordsList_wordsinasentence"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_wordsinasentence_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Words in a Sentence"
    def getWordsList_crunchprep101_web(self):
        page = requests.get("https://crunchprep.com/gre/2014/101-high-frequency-gre-words")
        newWordListDef=page.text.split("<p><strong>")[1:-2]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("</strong>")
            newWordList.append([newWordListDef[i][0],newWordListDef[i][1].split("</p><p>")[0]])
            #newWordList.append([newWordListDef[i][0],newWordListDef[i][1].split("</p><p>")[0]+" Ex.:"+newWordListDef[i][1].split("</p><p>")[1][:-5]])
        return newWordList
    def getWordsList_crunchprep101(self):
        label="getWordsList_crunchprep101"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_crunchprep101_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from crunchprep101"
    def getWordsList_kaplan200_web(self):
        page = requests.get("https://quizlet.com/7586859/kaplan-revised-gre-top-200-words-mnemonicsimages-flash-cards/")
        newWordListDef=page.text.split("<span class='TermText qWord lang-en'>")[1:-19]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("<span class='TermText qDef lang-en'>")
            newWordListDef[i][0]=newWordListDef[i][0].split('<')[0]
            newWordListDef[i][1]=newWordListDef[i][1].split('<')[0]
            newWordList.append([newWordListDef[i][0],newWordListDef[i][1]])
            #newWordList.append([newWordListDef[i][0],newWordListDef[i][1].split("</p><p>")[0]+" Ex.:"+newWordListDef[i][1].split("</p><p>")[1][:-5]])
        return newWordList
    def getWordsList_kaplan200(self):
        label="getWordsList_kaplan200"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_kaplan200_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Kaplan 200"
    def getWordsList_barron17th_web(self):
        page = requests.get("http://www.vocabulary.com/lists/194479#view=notes")
        newWordListDef=page.text.split("<a class=\"word dynamictext\" href=\"/dictionary/")[1:]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("</a>")
            newWordList.append([newWordListDef[i][0].split(">")[1],newWordListDef[i][1].split("</div")[0].split(">")[1]])
        return newWordList
    def getWordsList_barron17th(self):
        label="getWordsList_barron17th"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_barron17th_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from barron17th (http://www.vocabulary.com/)"
    def correctAscii(self,text):
        text=text.encode('ascii','ignore')
        text=text.split("&quot;")
        newText=""
        for each in text:
            newText+="\""+each
        newText=newText[1:]
        return newText
    def removeBlanks(self,text):
        text=text.encode('ascii','ignore')
        text=text.split()
        newText=""
        for each in text:
            newText+=" "+each
        newText=newText[1:]
        return newText
    def removeTags(self,text):
        text=text.encode('ascii','ignore')
        #Remove HTML tags
        newText=''
        iniTag=text.find('<')
        while iniTag>=0:
            newText+=text[:iniTag]
            endTag=text.find('>')
            text=text[endTag+1:]
            iniTag=text.find('<')
        #Remove &nbsp; tags
        text=newText
        iniTag=text.find('&')
        caseT=False
        if iniTag>=0:
            caseT=True
        while iniTag>=0:
            text=text[:iniTag]+text[(iniTag+6):]
            iniTag=text.find('&')
        if caseT:
            print text
        newText=text
        #Remove space trails
        while newText[0]==' ':
            newText=newText[1:]
        while newText[-1]==' ':
            newText=newText[:-1]
        return newText
    def getWordsList_flashCard180_web(self):
        page = requests.get("http://www.flashcardmachine.com/gre-180-frequentlyusedwords.html")
        newWordListDef=page.text.split("<tr valign=\"top\">")[2:]
        newWordList=[]
        for each in newWordListDef:
            definition=each.split("<td align=\"center\"><b><p>")[1:3]
            try:
                label=definition[0].split("\n")[0]
                definition=definition[1].split("\n")[0]
                label=self.removeTags(label)
                definition=self.removeTags(definition)
            except:
                print "ERROR"#each
            newWordList.append([label,definition])
        return newWordList
    def getWordsList_flashCard180(self):
        label="getWordsList_flashCard180"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_flashCard180_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from flashCard180 (http://www.flashcardmachine.com/)"
    def getWordsList_top1000_web(self):
        page = requests.get("http://www.vocabulary.com/lists/52473#view=notes")
        newWordListDef=page.text.split("<a class=\"word dynamictext\" href=\"/dictionary/")[1:]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("</a>")
            newWordList.append([newWordListDef[i][0].split(">")[1],newWordListDef[i][1].split("</div")[0].split(">")[1]])
        return newWordList
    def getWordsList_top1000(self):
        label="getWordsList_top1000"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_top1000_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Top1000 (http://www.vocabulary.com/)"        
    def getWordsList_michiganStateUniversity_web(self):
        page = requests.get("https://msu.edu/~defores1/gre/vocab/gre_vocab.htm")
        newWordListDef=page.text.split("</span></p>")[:-1]
        lenList = len(newWordListDef)/3
        newWordList=[]
        for i in range(lenList):
            label=newWordListDef[3*i].split('>')[-1]
            kind=newWordListDef[3*i+1].split('>')[-1]
            definition=newWordListDef[3*i+2].split('>')[-1]
            definition=self.correctAscii(self.removeBlanks(definition))
            try:                
                newWordList.append([label,"("+kind+") "+definition])
            except:
                print "ERROR",i#each
        return newWordList
    def getWordsList_michiganStateUniversity(self):
        label="getWordsList_michiganStateUniversity"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_michiganStateUniversity_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Michigan State University (https://msu.edu/)"
    def getWordsList_magooshFlashcards(self,level='easy'):
        label="getWordsList_magooshFlashcards_"+level
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
##            newWordList=self.getWordsList_top1000_web()
##            text_file = open(filename, "w")
##            text_file.write(json.dumps(newWordList))
##            text_file.close()
            print "There should be an error, this is done manually"
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Magoosh Flashcards"
    def getWordsList_barron4k_web_page(self,page):
        page = requests.get(page)
        newWordListDef=page.text.split("<a class=\"word dynamictext\" href=\"/dictionary/")[1:]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("</a>")
            newWordList.append([newWordListDef[i][0].split(">")[1],newWordListDef[i][1].split("</div")[0].split(">")[1]])
        return newWordList
    def getWordsList_barron4k_web(self):
        categories=["151577","151580","151589","151653"]
        newWordList=[]
        for i in range(len(categories)):
            newWordList.extend(self.getWordsList_barron4k_web_page("http://www.vocabulary.com/lists/"+categories[i]+"#view=notes"))
        return newWordList
    def getWordsList_barron4k(self):
        label="getWordsList_barron4k"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_barron4k_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Barron4k (http://www.vocabulary.com/)"
    def getWordsList_barron800_web_page(self,page):
        page = requests.get(page)
        newWordListDef=page.text.split("<div class=\"text\">")[1:]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("</div>")[0]
        for i in range(len(newWordListDef)/2):
            newWordList.append([newWordListDef[2*i],newWordListDef[2*i+1]])
        return newWordList
    def getWordsList_barron800_web(self):
        page = requests.get("http://www.memrise.com/course/121215/barrons-800-essential-word-list-gre/")
        newPage=page.text.split("\" class=\"level clearfix\">")[:-1]
        del page
        newWordList=[]
        for i in range(len(newPage)):
            newPage[i]=newPage[i].split("<a href=\"")[-1]
            newWordList.extend(self.getWordsList_barron800_web_page("http://www.memrise.com"+newPage[i]))
        return newWordList
    def getWordsList_barron800(self):
        label="getWordsList_barron800"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_barron800_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from barron800"
    def getWordsList_barron333_web_page(self,page):
        page = requests.get(page)
        newWordListDef=page.text.split("<div class=\"text\">")[1:]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("</div>")[0]
        for i in range(len(newWordListDef)/2):
            newWordList.append([newWordListDef[2*i],newWordListDef[2*i+1]])
        return newWordList
    def getWordsList_barron333_web(self):
        page = requests.get("http://www.memrise.com/course/116505/barrons-333-high-frequency-word-list-gre/")
        newPage=page.text.split("\" class=\"level clearfix\">")[:-1]
        del page
        newWordList=[]
        for i in range(len(newPage)):
            newPage[i]=newPage[i].split("<a href=\"")[-1]
            newWordList.extend(self.getWordsList_barron800_web_page("http://www.memrise.com"+newPage[i]))
        return newWordList
    def getWordsList_barron333(self):
        label="getWordsList_barron333"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_barron333_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from barron333"
    def getWordsList_graduateshotline_web_page(self,page):
        page = requests.get(page)
        newWordListDef=page.text.split("</td></tr>")[:-1]
        newWordList=[]
        for i in range(len(newWordListDef)):
            newWordListDef[i]=newWordListDef[i].split("?word=")[1]
            newWordList.append([newWordListDef[i].split("</a>")[0].split(">")[1],newWordListDef[i].split("<td>")[1]])
        return newWordList
    def getWordsList_graduateshotline_web(self):
        newWordList=[]
        for i in range(5):
            newWordList.extend(self.getWordsList_graduateshotline_web_page("http://www.graduateshotline.com/gre/load.php?file=list"+str(i+1)+".html"))
        return newWordList
    def getWordsList_graduateshotline(self):
        label="getWordsList_graduateshotline"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_graduateshotline_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Graduates Hotline"
    def getWordsList_majortests_web_page(self,page):
        page = requests.get(page)
        newWordList=page.text.split("<tr><th>")[1:]
        for i in range(len(newWordList)):
            newWordList[i]=newWordList[i].split("</t")[:2]
            newWordList[i][1]=newWordList[i][1][6:]
        return newWordList
    def getWordsList_majortests_web(self):
        newWordList=[]
        for i in range(15):
            number=str(i+1)
            if len(number)==1:
                number='0'+number
            newWordList.extend(self.getWordsList_majortests_web_page("http://www.majortests.com/gre/wordlist_"+number))
        return newWordList
    def getWordsList_majortests(self):
        label="getWordsList_majortests"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename)==False:
            #WEB method
            newWordList=self.getWordsList_majortests_web()
            text_file = open(filename, "w")
            text_file.write(json.dumps(newWordList))
            text_file.close()
        else:
            #FILE method
            text_file = open(filename, "r")
            newWordList=json.loads(text_file.read())
            text_file.close()
        self.wordList.extend(newWordList)
        print CM.ATTENTION+"# Imported",len(newWordList),"words from Major Tests"
    def addYourDictionarySentences(self,word=None):
        if word!=None:
            self.word=word
        self.currentQuerryHTML="http://sentence.yourdictionary.com/"+self.word
        page = requests.get(self.currentQuerryHTML)
        sentenceLines=[]
        if "<div class='li_content'>" in page.text:
            sentenceLines=page.text.split("<div class='li_content'>")[1:]
            for i in range(len(sentenceLines)):
                sentence=sentenceLines[i].split("</div></li>")[0]
                sentence=sentence.split("b>")
                if len(sentence)>=3:
                    sentence=sentence[0][:-1]+"________"+sentence[2].split('<')[0]
                    self.sentenceExamples.append(sentence)
        print CM.ATTENTION+"# Imported",len(sentenceLines),"sentences from YourDictionary"
    def addWebsterDictionarySentences(self,word=None):
        if word!=None:
            self.word=word
        self.currentQuerryHTML="http://webstersdictionary.facts.co/dictionary/define/"+self.word+"meaning.php"
        page = requests.get(self.currentQuerryHTML)
        sentenceLines=[]
        if "usage examples" in page.text:
            sentenceLines=page.text.split("usage examples")[1]
            sentenceLines=sentenceLines.split("<div class=\"dictionarysentence\">")[1:]
            for i in range(len(sentenceLines)):
                sentence=sentenceLines[i].split("</p></div>")[0]
                sentence=sentence.split("strong>")
                sentence=sentence[0][:-1]+"________"+sentence[2].split('<')[0]
                self.sentenceExamples.append(sentence)
        print CM.ATTENTION+"# Imported",len(sentenceLines),"sentences from WebsterDictionary"
    def addWordsInSentenceSentences(self,word=None):
        if word!=None:
            self.word=word
        self.currentQuerryHTML="http://wordsinasentence.com/"+self.word+"-in-a-sentence/"
        page = requests.get(self.currentQuerryHTML)
        sentenceLines=page.text.split("<li><p>")[1:]
        for i in range(len(sentenceLines)):
            sentence=sentenceLines[i].split("</li></p>")[0]
            sentence=sentence.split(self.word[1:])
            sentence=sentence[0][:-1]+"________"+sentence[1]
            self.sentenceExamples.append(sentence)
        print CM.ATTENTION+"# Imported",len(sentenceLines),"sentences from Words In a Sentence"
    def addGraduatesHotlineSentences(self,word=None):
        if word!=None:
            self.word=word
        self.currentQuerryHTML="http://gre.graduateshotline.com/a.pl?word="+self.word.lower()
        page = requests.get(self.currentQuerryHTML)
        sentenceLines=page.text.split("<b>...</b>")[:-1]
        for i in range(len(sentenceLines)):
            sentence=sentenceLines[i].split("<br>")[-1]
            sentence=sentence.split("b>")
            if len(sentence)>=3:
                    sentence=sentence[0][:-1]+"________"+sentence[2].split('<')[0]
                    self.sentenceExamples.append(sentence)
        print CM.ATTENTION+"# Imported",len(sentenceLines),"sentences from Graduates Hotline"
    def addWordnikSentences(self,word=None):
        if word!=None:
            self.word=word
        self.currentQuerryHTML="https://www.wordnik.com/words/"+self.word.lower()
        page = requests.get(self.currentQuerryHTML)
        sentenceLines=[]
        if "<li class=\"exampleItem\">" in page.text:
            sentenceLines=page.text.split("<p class=\"text\">")[1:]
            for i in range(len(sentenceLines)):
                sentence=sentenceLines[i].split("</p>")[0]
                sentence=sentence.split(self.word[1:])
                sentence=sentence[0][:-1]+"________"+sentence[1]
                self.sentenceExamples.append(sentence)
        print CM.ATTENTION+"# Imported",len(sentenceLines),"sentences from Graduates Hotline"
    def showRandomSentence(self):
        if len(self.sentenceExamples)>0:
            sentence=self.sentenceExamples[random.randint(0,len(self.sentenceExamples)-1)]
            print CM.QUESTION+sentence
    def showDefinition(self):
        print CM.INCORRECT+"+Definition:",self.wordList[self.Nsolution][1]
    def showOptionsWords(self):
        for each in self.randomQuiz:
            print CM.OPTIONS+str(self.randomQuiz[each].tag)+")",self.randomQuiz[each].word
        self.separatingLine()
    def showOptionsMeanings(self):
        for each in self.randomQuiz:
            print CM.OPTIONS+str(self.randomQuiz[each].tag)+")",self.randomQuiz[each].getMeaning()
        self.separatingLine()
    def showOptionsDefinitions(self):
        for each in self.randomQuiz:
            print CM.NORMAL+str(self.randomQuiz[each].tag)+")",self.randomQuiz[each].word,":",self.randomQuiz[each].getMeaning()
        self.separatingLine()
    def showCurrentStatus(self):
        print "STATUS:",len(self.wordListLearned),"learned,",len(self.wordListLearning),"learning and",len(self.wordListNew),"to be learned now out of",self.totalNewNotLimited
    def reintegrateQuizWords(self):
        for each in self.randomQuiz:
            if self.randomQuiz[each].state==STATUS_LEARNED:
                self.wordListLearned[each]=self.randomQuiz[each]
            elif self.randomQuiz[each].state==STATUS_NEW:
                self.wordListNew[each]=self.randomQuiz[each]
            else:
                self.wordListLearning[each]=self.randomQuiz[each]
        del self.randomQuiz
        self.showCurrentStatus()
    def showSolution(self,userSolution=None):
        if userSolution!=None:
            self.total+=1
            veredict=False
            if type(userSolution)==str:
                veredict=(userSolution==self.word)
            else:
                veredict=(self.word==self.mappingAnswer[userSolution])
            if veredict:
                self.currentWordDetailts.addNewAnswer(True)
                print CM.CORRECT+"Correct.",CM.QUESTION+self.word,CM.CORRECT+"::",CM.OPTIONS+self.currentWordDetailts.getMeaning()
                self.reintegrateQuizWords()
                self.correct+=1
                return True
            else:
                self.tries+=1
                self.currentWordDetailts.addNewAnswer(False)
                if self.tries==self.Intents:
                    print CM.INCORRECT+"Incorrect. Solution:",CM.QUESTION+self.word,CM.INCORRECT+"::",CM.OPTIONS+self.currentWordDetailts.getMeaning()
                    self.reintegrateQuizWords()
                    return True
                else:
                    print CM.INCORRECT+"Incorrect. Still",self.Intents-self.tries,"oportunities."
                return False
        else:
            print "Solution:",self.word
            return True
    def verifyUnderstanding(self):
        incomplete=True
        while incomplete==True:
            try:
                userSolution = int(input(CM.NORMAL+"Write something to continue or (q) to exit: "+CM.USER))
                self.reintegrateQuizWords()
            except:
                print CM.NORMAL+"Wrong command, please try again, or press (q) to exit"
                self.separatingLine()
                continue
            if userSolution==QUIT_TEST:
                self.separatingLine()
                self.incompleteTest=False
            incomplete=False
    def verifyAnswer(self):
        incomplete=True
        self.tries=0
        start = time.time()
        while incomplete==True:
            try:
                userSolutionRaw=input(CM.NORMAL+"Write your solution: "+CM.USER)
                if type(userSolutionRaw)==int:
                    userSolution = int(userSolutionRaw)
                else:
                    userSolution = userSolutionRaw
            except:
                print CM.NORMAL+"Wrong command, please try again, or press (q) to exit"
                self.separatingLine()
                continue
            if userSolution==0:
                #TASK: check all the different cases Word, Meaning, Sentence
                self.showDefinition()
            elif userSolution==USAGE_WORD_EXAMPLES:
                word=""
                try:
                    self.emptyExamples()
                    word = input(CM.NORMAL+"Write the word to exemplify: "+CM.USER)
                    self.addSentences(word)
                    print CM.EXAMPLE+random.choice(self.sentenceExamples)+CM.END
                except:
                    print CM.NORMAL+"Something wrong searching",word+", please try again"
            elif userSolution==USAGE_EXAMPLES:
                try:
                    #Basically the user don't know how to use the word
                    self.currentWordDetailts.addNewAnswer(False)
                    if len(self.sentenceExamples)==0:
                        self.addSentences()
                    print CM.EXAMPLE+random.choice(self.sentenceExamples)+CM.END
                except:
                    print CM.NORMAL+"Searching current word emit an error"
            elif userSolution==REPEAT_QUESTION:
                self.thisquiz()
            elif userSolution==SKIP_QUESTION:
                print CM.ATTENTION+"Last solution:",CM.QUESTION+self.word,CM.ATTENTION+"::",CM.OPTIONS+self.currentWordDetailts.getMeaning()
                self.separatingLine()
                self.skipped+=1
                incomplete=False
            elif userSolution==QUIT_TEST:
                self.reintegrateQuizWords()
                print CM.ATTENTION+"Last solution:",CM.QUESTION+self.word,CM.ATTENTION+"::",CM.OPTIONS+self.currentWordDetailts.getMeaning()
                self.separatingLine()
                self.incompleteTest=False
                incomplete=False
            elif userSolution==CHANGE_SENTENCE:
                self.showQuizSentence()
            elif userSolution==SHOW_DEFINITIONS:
                self.showOptionsDefinitions()
            else:
                if type(userSolution)==int:
                    if userSolution>self.options:
                        print "Wrong selection, please try again"
                        self.separatingLine()
                        continue
                if self.showSolution(userSolution):
                    delta=round(time.time()-start,1)
                    print CM.TIME+"Spend time:",delta,"seconds"+CM.END
                    self.currentWordDetailts.addNewTime(delta)
                    incomplete=False
    def shuffleWord(self):
        tmp=[]
        word=self.word[:(len(self.word)/3)]
        for each in self.word[(len(self.word)/3):]:
            tmp.append(each)
        random.shuffle(tmp)
        for each in tmp:
            word+=each
        return word
    def emptyExamples(self):
        self.sentenceExamples=[]
    def showQuizSentence(self):
        self.showRandomSentence()
        self.separatingLine()
        self.showOptionsWords()
    def showQuizMeaning(self):
        print CM.QUESTION+self.currentWordDetailts.getMeaning()
        self.separatingLine()
        self.showOptionsWords()
    def showQuizWord(self):
        print CM.QUESTION+self.word
        self.separatingLine()
        self.showOptionsMeanings()
    def showQuizWriteWord(self):
        print CM.QUESTION+self.currentWordDetailts.getMeaning()
        print CM.OPTIONS+self.shuffleWord()
        self.separatingLine()
        
    def showQuizShow(self):
        self.showOptionsDefinitions()

    def loadProgressLearning(self):
        label="wordListLearning"
        filename = os.path.dirname(os.path.realpath(__file__))+self.saveProgressPath+label+".txt"
        path = os.path.dirname(filename)
        if os.path.exists(path):
            if os.path.isfile(filename):
                text_file = open(filename, "r")
                dataDump=json.loads(text_file.read())
                text_file.close()
                for each in dataDump:
                    self.wordListLearning[each[0][0]]=newWord(each[0],each[1],each[2],each[3])
                print "Loading",len(dataDump),"learning word"
    def saveProgressLearned(self):
        label="wordListLearned"
        filename = os.path.dirname(os.path.realpath(__file__))+self.saveProgressPath+label+".txt"
        path = os.path.dirname(filename)
        dataDump=[]
        for each in self.wordListLearned.keys():
            dataDump.append(self.wordListLearned[each].convertArray())
        if not os.path.exists(path):
            os.makedirs(path)
        text_file = open(filename, "w")
        text_file.write(json.dumps(dataDump))
        text_file.close()
        
    def addSentences(self,word=None):
        self.emptyExamples()
        if word!=None:
            label=word[0]+"\\"+word
        else:
            label=self.word[0]+"\\"+self.word
        filename = os.path.dirname(os.path.realpath(__file__))+self.sentencesPath+label+".txt"
        path = os.path.dirname(filename)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.isfile(filename):
            text_file = open(filename, "r")
            self.sentenceExamples=json.loads(text_file.read())
            text_file.close()
            print CM.ATTENTION+"# Imported",len(self.sentenceExamples),"sentences from previous cases"
        else:
            self.addYourDictionarySentences(word)
            self.addWebsterDictionarySentences(word)
            self.addWordsInSentenceSentences(word)
            self.addGraduatesHotlineSentences(word)
            self.addWordnikSentences(word)
            text_file = open(filename, "w")
            text_file.write(json.dumps(self.sentenceExamples))
            text_file.close()
        self.separatingLine()
    def loadLearningWordsByWord(self):
        self.wordList=[]
        #TASK:Load from file in format learned[word]=newWord class#
        #Separate which are learned and which are learning
        self.wordListLearned={}
        self.wordListLearning={}
        self.wordListNew={}
        self.loadProgress()
    def standardFormat_sortWords(self):        
        for i in range(len(self.wordList)):
            #only lowercase word
            self.wordList[i][0]=self.wordList[i][0].lower()
            self.wordList[i][1]=self.wordList[i][1].lower()
            #eliminate unusefull spaces or blanks
            while self.wordList[i][0][0]==' ':
                self.wordList[i][0]=self.wordList[i][0][1:]
            while self.wordList[i][0][-1]==' ':
                self.wordList[i][0]=self.wordList[i][0][:-1]
            if len(self.wordList[i][1])>0:
                if self.wordList[i][1][-1]=='\n':
                    self.wordList[i][1]=self.wordList[i][1][:-1]
            #ignore unicode
            self.wordList[i][1]=self.wordList[i][1].encode('ascii','ignore')
            #sort into pre-established groups (will check if meaning is repeated)
            if self.wordList[i][0] in self.wordListLearned.keys():
                self.wordListLearned[self.wordList[i][0]].addMeaning(self.wordList[i])
            elif self.wordList[i][0] in self.wordListLearning:
                self.wordListLearning[self.wordList[i][0]].addMeaning(self.wordList[i])
            else:
                self.wordListNew[self.wordList[i][0]]=newWord(self.wordList[i])
        print "There are",len(self.wordListNew),"new words from those sources"
    def limitNewWords(self):
        self.totalNewNotLimited=len(self.wordListNew)
        if self.totalNewNotLimited>self.limitWordsPerSession:
            newList={}
            for i in range(self.limitWordsPerSession):
                sel=random.choice(self.wordListNew.keys())
                newList[sel]=self.wordListNew[sel]
                del(self.wordListNew[sel])
            self.wordListNew=newList
    def specialWordFilter(self,filterLetter=None):
        if filterLetter==None:
            filterLetter=chr(random.choice(range(26))+0x61)
        print "Filter Letter:",filterLetter,"limited new words to",
        newList={}
        for each in self.wordListNew.keys():
            if each[0]==filterLetter:
                newList[each]=self.wordListNew[each]
        self.wordListNew=newList
        print len(self.wordListNew)
    def showStatistics(self):
        print "showStatistics UNDER DEVELOPMENT"
    def loadVocabulary(self):
        self.loadLearningWordsByWord()
        ##Select which list to load
       
        #Easy
        self.getWordsList_crunchprep101()
        self.getWordsList_michiganStateUniversity()
        self.getWordsList_flashCard180()
        self.getWordsList_kaplan200()
        self.getWordsList_barron333()
        self.getWordsList_barron17th()        
        self.getWordsList_barron800()
        self.getWordsList_top1000()      

        #Medium
##        self.getWordsList_magooshFlashcards("easy")
##        self.getWordsList_magooshFlashcards("medium")
##        self.getWordsList_magooshFlashcards("hard")
##        self.getWordsList_graduateshotline()
##        self.getWordsList_majortests()

        #Hard
##        self.getWordsList_wordsinasentence()
##        self.getWordsList_barron4k()
        
        ##Sort, give format and check new words
        self.standardFormat_sortWords()
        
        ##Special request of new words
##        self.specialWordFilter('c')
        
        ##Limit the number of new words per session
        self.limitNewWords()
        self.separatingLine()
    def initQuizConditions(self):
        self.loadVocabulary()
        self.showStatistics()
        self.correct=0
        self.total=0
        self.skipped=0
        self.incompleteTest=True
    def printResult(self):
        print CM.RESULTS+"Success ratio:",round(100.0*self.correct/self.total,1),"% ("+str(self.correct),"out of",self.total,"tries and",self.skipped,"skipped)"+CM.END
        self.separatingLine()
    def saveProgress(self):
        self.saveProgressLearned()
        self.saveProgressLearning()
    def loadProgress(self):
        self.loadProgressLearned()
        self.loadProgressLearning()
        self.separatingLine()
    def loadProgressLearned(self):
        label="wordListLearned"
        filename = os.path.dirname(os.path.realpath(__file__))+self.saveProgressPath+label+".txt"
        path = os.path.dirname(filename)
        if os.path.exists(path):
            if os.path.isfile(filename):
                text_file = open(filename, "r")
                dataDump=json.loads(text_file.read())
                text_file.close()
                for each in dataDump:
                    self.wordListLearned[each[0][0]]=newWord(each[0],each[1],each[2],each[3])
                print "Loading",len(dataDump),"learned word"
    def loadProgressLearning(self):
        label="wordListLearning"
        filename = os.path.dirname(os.path.realpath(__file__))+self.saveProgressPath+label+".txt"
        path = os.path.dirname(filename)
        if os.path.exists(path):
            if os.path.isfile(filename):
                text_file = open(filename, "r")
                dataDump=json.loads(text_file.read())
                text_file.close()
                for each in dataDump:
                    self.wordListLearning[each[0][0]]=newWord(each[0],each[1],each[2],each[3])
                print "Loading",len(dataDump),"learning word"
    def saveProgressLearned(self):
        label="wordListLearned"
        filename = os.path.dirname(os.path.realpath(__file__))+self.saveProgressPath+label+".txt"
        path = os.path.dirname(filename)
        dataDump=[]
        for each in self.wordListLearned.keys():
            dataDump.append(self.wordListLearned[each].convertArray())
        if not os.path.exists(path):
            os.makedirs(path)
        text_file = open(filename, "w")
        text_file.write(json.dumps(dataDump))
        text_file.close()
    def saveProgressLearning(self):
        label="wordListLearning"
        filename = os.path.dirname(os.path.realpath(__file__))+self.saveProgressPath+label+".txt"
        path = os.path.dirname(filename)
        dataDump=[]
        for each in self.wordListLearning.keys():
            dataDump.append(self.wordListLearning[each].convertArray())
        if not os.path.exists(path):
            os.makedirs(path)
        text_file = open(filename, "w")
        text_file.write(json.dumps(dataDump))
        text_file.close()
    def selectWordTest(self):
        x=random.random()
        #No need to search for new words when we enter the quiz to write the word
        #would only need to search the words learned and under learning
        if x<self.prob_test_new and self.quizMode!=QUIZ_WRITE_WORD:
            return TEST_NEW
        elif x<(1-self.prob_learning):
            return TEST_LEARNED
        else:
            return TEST_LEARNING
    def getRandomQuiz(self):
        self.randomQuiz={}
        countNew=0
        countLearned=0
        countLearning=0
        selectedMethod=None
        #Random kind of selection
        if random.random()<0.4:
            print CM.ATTENTION+"From normal set of learned words"
            selectedMethod=self.wordListLearned.keys
        else:
            if random.random()<0.5:
                print CM.ATTENTION+"From top less seen words"
                selectedMethod=self.getTopLessSeenLearnedWords
            else:
                print CM.ATTENTION+"From top hard words"
                selectedMethod=self.getTopHardLearnedWords
        #Get random elements with some probability
        for i in range(self.options):
            incomplete=True
            while incomplete:
                selectedWord=None
                selectedObject=None
                typeWord=self.selectWordTest()
                if typeWord==TEST_LEARNED:
                    if len(self.wordListLearned)>0:
                        selectedWord=random.choice(selectedMethod())
                        selectedObject=self.wordListLearned[selectedWord]
                        countLearned+=1
                        del(self.wordListLearned[selectedWord])
                if typeWord==TEST_LEARNING:
                    if len(self.wordListLearning)>0:
                        selectedWord=random.choice(self.wordListLearning.keys())
                        selectedObject=self.wordListLearning[selectedWord]
                        countLearning+=1
                        del(self.wordListLearning[selectedWord])
                if typeWord==TEST_NEW:
                    if len(self.wordListNew)>0:
                        selectedWord=random.choice(self.wordListNew.keys())
                        selectedObject=self.wordListNew[selectedWord]
                        countNew+=1
                        del(self.wordListNew[selectedWord])
                if selectedWord!=None:
                    incomplete=False
                    self.randomQuiz[selectedWord]=selectedObject
        #Initialize word to work with during quiz
        self.currentWordDetailts=self.randomQuiz[random.choice(self.randomQuiz.keys())]
        #Select one solution among the options
        self.word=self.currentWordDetailts.word
        wordState=self.currentWordDetailts.state
        #Set a map for the answers
        i=1
        self.mappingAnswer={}
        for each in self.randomQuiz:
            self.randomQuiz[each].setTag(i)
            self.mappingAnswer[i]=self.randomQuiz[each].word
            i+=1
        #Recommend what kind of quiz depending on the current words selected
        ##                          Selected Word
        ##                      Ld      Lg      N
        ##muchos Learned(A)      Swm     WMs     Wms
        ##muchos Learning(B)     WMs     Wms     Mws
        ##muchos New(C)          Wms     Mws     Show
        Probabilities=[1,0,0,0]#[show,meaning,word,sentence]
        if countLearned+countLearning>countNew:
            if countLearned>countLearning:#Case A
                if wordState==STATUS_LEARNED:
                    Probabilities=[0,8,25,72*ENABLE_SENTENCES_SEARCH]
                elif wordState==STATUS_LEARNING:
                    Probabilities=[0,30,75,10*ENABLE_SENTENCES_SEARCH]
                else:
                    Probabilities=[0,15,65,5*ENABLE_SENTENCES_SEARCH]
            else:#Case B
                if wordState==STATUS_LEARNED:
                    Probabilities=[5,30,75,10*ENABLE_SENTENCES_SEARCH]
                elif wordState==STATUS_LEARNING:
                    Probabilities=[5,15,65,0]
                else:
                    Probabilities=[5,65,15,0]
        else:#Case C
            if wordState==STATUS_LEARNED:
                Probabilities=[5,15,65,0]
            elif wordState==STATUS_LEARNING:
                Probabilities=[5,65,15,0]
            else:
                Probabilities=[90,5,5,0]
        value=random.random()
        Probabilities[1]+=Probabilities[0]
        Probabilities[2]+=Probabilities[1]
        Probabilities[3]+=Probabilities[2]*1.0
        Probabilities[0]/=Probabilities[3]
        Probabilities[1]/=Probabilities[3]
        Probabilities[2]/=Probabilities[3]
        Probabilities[3]=1
        if value<Probabilities[0]:
            return QUIZ_SHOW
        if value<Probabilities[1]:
            return QUIZ_MEANING
        if value<Probabilities[2]:
            value=random.random()
            if value<0.5:
                return QUIZ_WRITE_WORD
            return QUIZ_WORD
        return QUIZ_SENTENCE
    def getTopHardLearnedWords(self):
        topHard=[]
        for each in self.wordListLearned:
            topHard.append([self.wordListLearned[each].avg_time,self.wordListLearned[each].word])
        topHard.sort()
        del(topHard[:-TOP_HARD_WORDS_PRIORITY])
        for i in range(len(topHard)):
            topHard[i]=topHard[i][1]
        return topHard
    def getTopLessSeenLearnedWords(self):
        topLessSeen=[]
        for each in self.wordListLearned:
            topLessSeen.append([self.wordListLearned[each].viewed,self.wordListLearned[each].word])
        topLessSeen.sort()
        del(topLessSeen[TOP_LESS_SEEN_WORDS:])
        for i in range(len(topLessSeen)):
            topLessSeen[i]=topLessSeen[i][1]
        return topLessSeen
    def readPdf(self):
        # Read each line of the PDF
        label="magoosh-gre-1000-words_oct01"
        filename = os.path.dirname(os.path.realpath(__file__))+self.wordListPath+label+".pdf"
        inputRaw = PdfFileReader(open(filename, "rb"))

        # print how many pages input1 has:
        num_pages=inputRaw.getNumPages()

        #70 on 1st page to get the first useful line
        #35 after 1st page to get the first useful line
        text=''
        print "Finished pages:",
        for page in range(0,num_pages):            
            pageRaw=inputRaw.getPage(page).extractText().encode('ascii','ignore')+'\n'
            if page==0:
                pageRaw=pageRaw[70:]
            else:
                pageRaw=pageRaw[35:]
            for line in pageRaw:
                text+=line
            print page+1,",",
        print "\nFinished step A"
        text=text.split('\n')
        for i in range(len(text))[::-1]:
            if text[i]==' ' or text[i]=='':
                del(text[i])
        for i in range(len(text)):
            if text[i]=="unflappable":
                print "location of unflappable at ",i
                break
        print "Finished step B"
        for i in range(len(text))[::-1]:
            if text[i]=='(':
                text[i]="#("
                text[i+2]=")#"
                j=i+4
                search=True
                while search:
                    try:
                        if text[j][0].isupper():
                            text[j]='#'+text[j]
                            search=False
                        else:
                            j+=1
                    except:
                        print "ERROR",j,text[i-1],text[i],text[i+1],text[i+2],text[i+3],text[i+4]
                j=i-1
                search=True
                while search:
                    if text[j-1][-1]=='.':
                        search=False
                        text[j]='#'+text[j]
                    else:
                        j-=1
        print "Finished step C"
        newText=''
        for each in text:
            newText+=each
        text=newText.split('#')[1:]
        data=[]
        print "Finished step D"
        for i in range(len(text)/4):
            data.append([text[4*i],text[4*i+1]+' '+text[4*i+2]])
        print "Finished step E"
    def quickTest(self,quizType=None):
        #Shows a word, have to search the meaning of the word
        self.quizMode=quizType
        self.initQuizConditions()
        while self.incompleteTest:
            self.emptyExamples()
            #Auto select quick according to defined status
            quizType=self.getRandomQuiz()
            if quizType==QUIZ_SHOW:
                self.thisquiz=self.showQuizShow
            elif quizType==QUIZ_WORD:
                self.thisquiz=self.showQuizWord
            elif quizType==QUIZ_WRITE_WORD:
                self.thisquiz=self.showQuizWriteWord
            elif quizType==QUIZ_MEANING:
                self.thisquiz=self.showQuizMeaning
            elif quizType==QUIZ_SENTENCE:
                self.addSentences()
                self.thisquiz=self.showQuizSentence
            self.thisquiz()
            if quizType==QUIZ_SHOW:
                self.verifyUnderstanding()
            else:
                self.verifyAnswer()
                self.saveProgress()
                if self.total>0:
                    self.printResult()
                else:
                    if self.incompleteTest==False:
                        print CM.INCORRECT+"You didn't even try..."
        print CM.CORRECT+"Saving Progress..."
        self.saveProgress()

##Simple application
thisTest=MyTest()
##thisTest.readPdf()##Only to extract words (inside various cases, done by hand)
thisTest.quickTest()#QUIZ_WRITE_WORD

##thisTest.quickTestWord()
time.sleep(1.5)
