import urllib.request, json, operator, os, time, datetime, random
from os.path import exists
from datetime import date
from apscheduler.schedulers.background import BlockingScheduler
import sys
import subprocess
sys.stdout.reconfigure(encoding='utf-8')

header= {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
			'AppleWebKit/537.11 (KHTML, like Gecko) '
			'Chrome/23.0.1271.64 Safari/537.11',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
			'Accept-Encoding': 'none',
			'Accept-Language': 'en-US,en;q=0.8',
			'Connection': 'keep-alive'}
url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
request = urllib.request.Request(url, None, header)

#YGOPRODECK API keys
DATA = 'data'
CARD_SETS = 'card_sets'
SET_CODE = 'set_code'
SET_RARITY_CODE = 'set_rarity_code'
BANLIST_INFO = 'banlist_info'
BAN_TCG = 'ban_tcg'
CARD_IMAGES = 'card_images'
CARD_TYPE = 'type'
CARD_PRICES = 'card_prices'
TCGPLAYER_PRICE = 'tcgplayer_price'
CARDMARKET_PRICE = 'cardmarket_price'
BANLIST_INFO = 'banlist_info'
BAN_TCG = 'ban_tcg'

#Token stuff
TOKEN = 'Token'
SKILL = 'Skill Card'

#My keys
NAME = 'name'
CARD_ID = 'id'
CARD_IDS = 'ids'
STATUS = 'status'
PREVIOUS_STATUS = 'previous_status'
PRICE = 'price'
LAST_PRICE = 'last_price'
PREVIOUS_RUNS = 'previousRuns'

#Banlist status
BANNED = 'Banned'
LIMITED = 'Limited'
SEMI = 'Semi-Limited'
UNLIMITED = 'Unlimited'
FORCE_LEGAL = "ForceLegal"
FORCE_ILLEGAL = "ForceIllegal"
ADDITIONAL_REMOVED_IDS = "RemovedAnimeShit"

diBanlistPath = 'json/banlist/di_banlist.json'

jsonData = {}

cutoffPoint = 0.50

today = date.today()
formatted = today.strftime("%Y/%m/%d, %H:%M:%S")
banlistPath = 'banlist/ongoing/disco_inferno_ongoing.lflist.conf'
jsonPath = 'json/current.json'
previousDataPath = 'json/previous.json'
differencesPath = 'docs/differences.md'
closePricesPath = 'docs/closeprices.md'

banlist = []
additionalForbidden = []
additionalLimited = []
additionalSemiLimited = []
additionalUnlimited = []
forceLegal = []
forceIllegal = []
additionalRemovedIds = []

def getCardStatusAsString(cardStatus):
	cardStatusAsText = "Unlimited"
	if (cardStatus == -3):
		cardStatusAsText = "Didn't exist"
	if (cardStatus == -2):
		cardStatusAsText = "Illegal"
	elif (cardStatus == -1):
		cardStatusAsText = "Illegal"
	elif (cardStatus == 0):
		cardStatusAsText = "Forbidden"
	elif (cardStatus == 1):
		cardStatusAsText = "Limited"
	elif (cardStatus == 2):
		cardStatusAsText = "Semi-Limited"
	return cardStatusAsText

def getCardUrl(cardName):
	sanitizedCardName = cardName.replace(" ", "%20").replace("&", "%26")
	return "https://db.ygoprodeck.com/card/?search=%s"%sanitizedCardName

def getBanInfo(card):
	banTcg = 3
	banInfo = card.get(BANLIST_INFO)
	if (banInfo == None):
		banTcg = 3	
	if (banInfo != None):
		banlistStatus = banInfo.get(BAN_TCG)
		if (banlistStatus == None):
			banTcg = 3
		if (banlistStatus == BANNED):
			banTcg = 0
		if (banlistStatus == LIMITED):
			banTcg = 1
		if (banlistStatus == SEMI):
			banTcg = 2
		if (banlistStatus == UNLIMITED):
			banTcg = 3

	cardName = card.get(NAME)

	if cardName in additionalForbidden:
		banTcg = 0
	if cardName in additionalLimited:
		banTcg = 1
	if cardName in additionalSemiLimited:
		banTcg = 2
	if cardName in additionalUnlimited:
		banTcg = 3
	if cardName in forceIllegal:
		banTcg = -1

	return banTcg

def getCardPrice(card):
	cardPrices = card.get(CARD_PRICES)[0]
	tcgplayerPrice = float(cardPrices.get(TCGPLAYER_PRICE))
	cardmarketPrice = float(cardPrices.get(CARDMARKET_PRICE))
	avgPrice = min(tcgplayerPrice, cardmarketPrice)
	if (avgPrice == 0):
		avgPrice = (tcgplayerPrice + cardmarketPrice)/2
	if card.get(NAME) in forceLegal:
		if (avgPrice > 1):
			avgPrice -=1
		else:
			avgPrice /=2
	return avgPrice

def loadConstants():
	global banlist
	global additionalForbidden
	global additionalLimited
	global additionalSemiLimited
	global additionalUnlimited
	global forceLegal
	global forceIllegal
	global additionalRemovedIds
	global jsonData

	with open(diBanlistPath) as banlistFile:
		banlist = json.load(banlistFile)
		additionalForbidden = banlist.get(BANNED)
		additionalLimited = banlist.get(LIMITED)
		additionalSemiLimited = banlist.get(SEMI)
		additionalUnlimited = banlist.get(UNLIMITED)
		forceLegal = banlist.get(FORCE_LEGAL)
		forceIllegal = banlist.get(FORCE_ILLEGAL)
		additionalRemovedIds = banlist.get(ADDITIONAL_REMOVED_IDS)

	jsonData = {PREVIOUS_RUNS:0, DATA:[]}
	if os.path.exists(jsonPath):
		with open(jsonPath) as file:
			jsonData = json.load(file)

def getCardsFromAPI():
	with urllib.request.urlopen(request) as url:
		cards = json.loads(url.read().decode()).get(DATA)
		return cards

def buildLflist():
	cards = jsonData.get(DATA)
	with open(banlistPath, 'w', encoding="utf-8") as outfile:
		outfile.write("#[Disco Inferno]\n")
		outfile.write("!Disco Inferno %s\n\n" % today.strftime("%m.%Y"))
		outfile.write("\n$whitelist\n\n")
		for card in cards:
			cardBanlistStatus = card.get(STATUS)
			try:
				if cardBanlistStatus < -1:
					cardBanlistStatus = -1
				for cardId in card.get(CARD_IDS):
					outfile.write("%d %d -- %s\n" % (cardId, cardBanlistStatus, card.get(NAME)))
			except TypeError:
				print(card.get(NAME), flush=True)
		outfile.write("\n\n#Here lies all the anime bullshit\n\n")
		for cardId in additionalRemovedIds:
			outfile.write("%s -1\n"%cardId)

def dumpJson():
	with open(jsonPath, 'w', encoding="utf-8") as file:
		json.dump(jsonData, file, indent=4)

def applyCutOff(cards):
	for card in cards:
		cardName = card.get(NAME)
		if card[PRICE] > cutoffPoint:
			card[STATUS] = -1
		if cardName in forceIllegal:
			card[STATUS] = -1

def generatePriceData(cards):
	runs = jsonData.get(PREVIOUS_RUNS)
	jsonData[PREVIOUS_RUNS] = (runs + 1)
	for card in cards:
		if card.get(CARD_SETS) == None:
			continue
		if card.get(CARD_TYPE) == SKILL or card.get(CARD_TYPE) == TOKEN:
			continue

		cardName = card.get(NAME)
		images = card.get(CARD_IMAGES)

		avgPrice = getCardPrice(card)
		banTcg = getBanInfo(card)

		if runs == 0:
			newAverage = avgPrice
			ids = []

			for variant in images:
				ids.append(variant.get(CARD_ID))
			entry = {}
			entry[NAME] = cardName
			entry[CARD_IDS] = ids
			entry[PRICE] = newAverage
			entry[LAST_PRICE] = newAverage
			entry[STATUS] = banTcg
			jsonData[DATA].append(entry)
		else:
			for entry in jsonData.get(DATA):
				if entry.get(NAME) == card.get(NAME):
					previousAverage = entry.get(PRICE)
					newAverage = (previousAverage * runs + avgPrice)/(runs+1)
					entry[PRICE] = float("{:.2f}".format(newAverage))
					entry[LAST_PRICE] = float("{:.2f}".format(avgPrice))
					entry[STATUS] = banTcg
					break


def generatePriceDifferences():
	priceDifferences = []
	with open(previousDataPath) as file:
		previousPriceData = json.load(file)
		previousPrice = 0
		newPrice = 0
		for cardData1 in jsonData.get(DATA):
			found = False
			for cardData2 in previousPriceData.get(DATA):
				if (cardData1.get(NAME) == cardData2.get(NAME)):
					previousStatus = cardData2.get(STATUS)
					currentStatus = cardData1.get(STATUS)
					if (cardData2.get(PRICE) < 1):
						previousPrice += cardData2.get(PRICE)
						newPrice += cardData1.get(PRICE)
					if (previousStatus < 0):
						previousStatus = -1
					if (currentStatus < 0):
						currentStatus = -1
					if (previousStatus > 0 or currentStatus > 0):
						if (previousStatus != currentStatus):
							diffCard = {}
							diffCard[NAME] = cardData1.get(NAME)
							diffCard[STATUS] = cardData1.get(STATUS)
							diffCard[PREVIOUS_STATUS] = cardData2.get(STATUS)
							diffCard[PRICE] = cardData1.get(PRICE)
							priceDifferences.append(diffCard)
					found = True
					break
			
			if not found:
				if cardData1.get(STATUS) > 0:
					diffCard = {}
					diffCard[NAME] = cardData1.get(NAME)
					diffCard[STATUS] = cardData1.get(STATUS)
					diffCard[PREVIOUS_STATUS] = -3
					priceDifferences.append(diffCard)
	return priceDifferences

def buildPriceDifferencesPage(priceDifferences):
	with open(differencesPath, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThese are the projected changes between the current banlist and the next one.")
		outfile.write("\n\nPlease keep in mind these changes are not definitive and are only based on past prices. We cannot predict the future changes in the market.")
		outfile.write("\n\nFor a list of cards that are likely to move, go [HERE](closeprices)")
		outfile.write("\n\nEstimated number of changes: %d"% len(priceDifferences))
		outfile.write("\n\n| Card name | Previous Status | New Status |")
		outfile.write("\n| :-- |")

		for card in sorted(priceDifferences, key=operator.itemgetter(STATUS)):
			cardStatus = card.get(STATUS)
			cardStatusAsText = getCardStatusAsString(cardStatus)
			previousCardStatus = card.get(PREVIOUS_STATUS)
			previousCardStatusAsText = getCardStatusAsString(previousCardStatus)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)

			outfile.write("\n|[%s](%s) | %s | %s |"%(cardName, cardUrl, previousCardStatusAsText, cardStatusAsText))

		outfile.write("\n\n###### [Back home](index)")

def generateCloseCards():
	closeCards = []
	for card in jsonData.get(DATA):
		price = card.get(PRICE)
		if price >= 0.47 and price <=0.60:
			cardName = card.get(NAME)
			a = card.get(NAME) in additionalForbidden
			b = card.get(STATUS) == 0
			if not (a or b):
				closeCards.append(card)
	return closeCards

def buildCloseCardsPage(closeCards):
	with open(closePricesPath, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThese are just cards that are bordering around the $0.50 limit. They are the closest to moving on the next banlist.")
		outfile.write("\n\n| Card name | Avg $ |")
		outfile.write("\n| :-- | :-- |")

		for card in sorted(closeCards, key=operator.itemgetter(PRICE)):
			cardPrice = card.get(PRICE)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)
			cardStatus = card.get(STATUS)
			if cardStatus != 0:
				outfile.write("\n[%s](%s) | %s |"%(cardName, cardUrl, "{:.2f}".format(cardPrice)))

		outfile.write("\n\n###### [Back home](index)")

def uploadToGit():
	subprocess.call('git add .', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
	subprocess.call('git commit -m \"%s\"'%formatted, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
	subprocess.call('git push', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def buildEverything():

	print("Loading constants...")

	loadConstants()

	print("Getting cards from API...", flush=True)
	cards = getCardsFromAPI()

	print("Generating price data...", flush=True)
	generatePriceData(cards)

	cards = jsonData.get(DATA)

	print("Applying price cutoff...", flush=True)
	applyCutOff(cards)

	print("Dumping json file...", flush=True)
	dumpJson()

	print("Building lflist file...", flush=True)
	buildLflist()

	print("Building price differences page...", flush=True)
	priceDifferences = generatePriceDifferences()
	buildPriceDifferencesPage(priceDifferences)

	print("Building close cards page...", flush=True)
	closeCards = generateCloseCards()
	buildCloseCardsPage(closeCards)

	print("Uploading to git...", flush=True)
	uploadToGit()

	print("Done", flush=True)

buildEverything()


sched = BlockingScheduler()
sched.daemonic = False
sched.add_job(buildEverything, 'interval', minutes=5)
sched.start()