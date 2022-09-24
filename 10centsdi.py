import urllib.request, json, operator, os, time, datetime, random
from os.path import exists
from datetime import datetime
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
EBAY_PRICE = "ebay_price"
AMAZON_PRICE = "amazon_price"
COOLSTUFFINC_PRICE = "coolstuffinc_price"
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
PROJECTED_STATUS = 'projected_status'
PRICE = 'price'
LAST_PRICE = 'last_price'
PREVIOUS_RUNS = 'previousRuns'
PROJECTED_FINAL_PRICE = 'projectedPrice'

CARD_TYPE_KEY = "cardType"
CARD_TYPE_NORMAL_MONSTER = 1
CARD_TYPE_EFFECT_MONSTER = 2
CARD_TYPE_RITUAL_MONSTER = 3
CARD_TYPE_FUSION_MONSTER = 4
CARD_TYPE_LINK_MONSTER = 5
CARD_TYPE_SYNCHRO_MONSTER = 6
CARD_TYPE_XYZ_MONSTER = 7
CARD_TYPE_SPELL = 98
CARD_TYPE_TRAP = 99

#Banlist status
BANNED = 'Banned'
LIMITED = 'Limited'
SEMI = 'Semi-Limited'
UNLIMITED = 'Unlimited'
FORCE_LEGAL = "ForceLegal"
FORCE_ILLEGAL = "ForceIllegal"
NEW_SET_CARDS = "NewSetCards"
GOOD_PRICES = "UseOnlyGoodPrices"
ADDITIONAL_REMOVED_IDS = "RemovedAnimeShit"
REPETITIONS = "Repetitions"
FORCE_0 = "Force0"
FORCE_10 = "Force10"
FORCE_20 = "Force20"
FORCE_30 = "Force30"
FORCE_40 = "Force40"
SET_TO_CHECK = "SetToCheck"

diBanlistPath = 'json/banlist/di_banlist.json'

jsonData = {}

cutoffPoint = 0.1

repetitions = 1

today = datetime.now()
rotationTime = datetime.strptime("2022/10/06", "%Y/%m/%d")
formatted = today.strftime("%Y/%m/%d, %H:%M:%S")
runsLeft = 0
banlistPath = 'banlist/ongoing/disco_inferno_ongoing.lflist.conf'
jsonPath = 'json/current.json'
previousDataPath = 'json/previous.json'
differencesPath = 'docs/differences.md'
closePricesPath = 'docs/closeprices.md'
legalityPath = 'docs/legality.md'
secretWebsitePath = 'docs/dd.md'
banlistHits = 'logs/banlistHistory.txt'
ongoingBanlist = 'docs/ongoingBanlist.md'
nextBanlistName = "Structure Deck: Legend of the Crystal Beasts"


banlist = []
additionalForbidden = []
additionalLimited = []
additionalSemiLimited = []
additionalUnlimited = []
forceLegal = []
forceIllegal = []
additionalRemovedIds = []
newSetCards = []
useOnlyGoodPrices = []
lastSetIllegal = []
force0 = []
force10 = []
force20 = []
force30 = []
force40 = []
lastSet = []

changes = []

cardsFromAPI = []

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
	ebayPrice = float(cardPrices.get(EBAY_PRICE))
	amazonPrice = float(cardPrices.get(AMAZON_PRICE))
	csiPrice = float(cardPrices.get(COOLSTUFFINC_PRICE))
	cardName = card.get(NAME)

	avgPrice = min(tcgplayerPrice, cardmarketPrice, ebayPrice, amazonPrice, csiPrice)
	goodPrices = min(tcgplayerPrice, cardmarketPrice)

	if cardName in useOnlyGoodPrices:
		avgPrice = goodPrices

	if (goodPrices > cutoffPoint and avgPrice <= cutoffPoint and avgPrice > 0):
		if not card.get(NAME) in useOnlyGoodPrices:
			if (avgPrice / goodPrices > 2):
				print("%s %f %f"%(cardName, goodPrices, avgPrice), flush=True)

	if avgPrice == 0:
		avgPrice = goodPrices



	if avgPrice == 0:
		avgPrice = (tcgplayerPrice + cardmarketPrice)/2

	if cardName in force0:
		if avgPrice > cutoffPoint:
			avgPrice = random.uniform(0, 0.1)
		else:
			print("You can remove %s from force0"%cardName, flush=True)
	if cardName in force10:
		if avgPrice > cutoffPoint:
			avgPrice = random.uniform(0.1, 0.2)
		else:
			print("You can remove %s from force10"%cardName, flush=True)
	if cardName in force20:
		if avgPrice > cutoffPoint:
			avgPrice = random.uniform(0.2, 0.3)
		else:
			print("You can remove %s from force20"%cardName, flush=True)
	if cardName in force30:
		if avgPrice > cutoffPoint:
			avgPrice = random.uniform(0.3, 0.4)
		else:
			print("You can remove %s from force30"%cardName, flush=True)
	if cardName in force40:
		if avgPrice > cutoffPoint:
			avgPrice = random.uniform(0.4, 0.5)
		else:
			print("You can remove %s from force40"%cardName, flush=True)
	if cardName in forceLegal:

		if avgPrice <= cutoffPoint and avgPrice > 0:
			print("You can remove %s, it's at %f"%(cardName, avgPrice), flush=True)
		
		avgPrice /=2
		
		if avgPrice < 0.51 and avgPrice > 0.49:
			avgPrice = 0.48

		if (avgPrice > cutoffPoint):
			print("Still not enough to make %s legal"%cardName, flush=True)

	if cardName in newSetCards:
		if (avgPrice > cutoffPoint):
			while (avgPrice > cutoffPoint/2):
				avgPrice /= 2
		else:
			print("You can remove %s, it's at %f"%(cardName, avgPrice), flush=True)
		newSetCards.remove(cardName)
	if cardName in forceIllegal:
		avgPrice = -1
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
	global newSetCards
	global repetitions
	global today
	global formatted
	global runsLeft
	global useOnlyGoodPrices
	global force0
	global force10
	global force20
	global force30
	global force40
	global lastSet
	
	today = datetime.now()
	formatted = today.strftime("%Y/%m/%d, %H:%M:%S")

	timeLeft = rotationTime - today
	minutes = timeLeft.total_seconds() / 60
	runsLeft = int(minutes / 5)

	with open(diBanlistPath) as banlistFile:
		banlist = json.load(banlistFile)
		additionalForbidden = banlist.get(BANNED)
		additionalLimited = banlist.get(LIMITED)
		additionalSemiLimited = banlist.get(SEMI)
		additionalUnlimited = banlist.get(UNLIMITED)
		forceLegal = banlist.get(FORCE_LEGAL)
		forceLegalCopy = banlist.get(FORCE_LEGAL)
		forceIllegal = banlist.get(FORCE_ILLEGAL)
		additionalRemovedIds = banlist.get(ADDITIONAL_REMOVED_IDS)
		newSetCards = banlist.get(NEW_SET_CARDS)
		repetitions = banlist.get(REPETITIONS)
		useOnlyGoodPrices = banlist.get(GOOD_PRICES)
		force0 = banlist.get(FORCE_0)
		force10 = banlist.get(FORCE_10)
		force20 = banlist.get(FORCE_20)
		force30 = banlist.get(FORCE_30)
		force40 = banlist.get(FORCE_40)
		lastSet = banlist.get(SET_TO_CHECK)

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
		cardPrice = card.get(PRICE)
		cardLastPrice = card.get(LAST_PRICE)
		if cardPrice > cutoffPoint:
			card[STATUS] = -1
		if cardName in forceIllegal:
			card[STATUS] = -1


def isBannedByKonami(card):
	banInfo = card.get(BANLIST_INFO)
	if banInfo != None:
		if banInfo.get(BAN_TCG) == BANNED:
			return True
	return False

def generatePriceData(cards):
	global changes
	global lastSetIllegal
	runs = jsonData.get(PREVIOUS_RUNS)

	jsonData[PREVIOUS_RUNS] = (runs + repetitions)
	changes = []
	for card in cards:
		if card.get(CARD_SETS) == None:
			continue
		if card.get(CARD_TYPE) == SKILL or card.get(CARD_TYPE) == TOKEN:
			continue

		cardName = card.get(NAME)
		images = card.get(CARD_IMAGES)

		avgPrice = getCardPrice(card)
		banTcg = getBanInfo(card)
		banned = isBannedByKonami(card)
		cardTypeAsInt = getCardTypeAsInteger(card)

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
			entry[CARD_TYPE_KEY] = cardTypeAsInt
			jsonData[DATA].append(entry)
		else:
			found = False
			for entry in jsonData.get(DATA):
				if entry.get(NAME) == card.get(NAME):
					found = True
					runs = jsonData.get(PREVIOUS_RUNS)
					for a in range(0, repetitions):
						previousAverage = entry.get(PRICE)
						newAverage = (previousAverage * runs + avgPrice)/(runs+1)
						
						if entry.get(NAME) in forceLegal:
							forceLegal.remove(entry.get(NAME))

						if (avgPrice == -1):
							newAverage = -1
						elif (newAverage < 0):
							newAverage = avgPrice

						totalRuns = runs+runsLeft

						previousRunsPrice = newAverage * runs
						projectedRunsPrice = avgPrice * runsLeft

						projectedFinalPrice = (projectedRunsPrice + previousRunsPrice)/totalRuns

						entry[PRICE] = newAverage
						entry[LAST_PRICE] = avgPrice
						entry[STATUS] = banTcg
						entry[BANNED] = banned
						entry[CARD_TYPE_KEY] = cardTypeAsInt
						entry[PROJECTED_FINAL_PRICE] = projectedFinalPrice
						if (projectedFinalPrice <= cutoffPoint):
							entry[PROJECTED_STATUS] = banTcg
						else:
							entry[PROJECTED_STATUS] = -1

						if previousAverage <= cutoffPoint and newAverage > cutoffPoint:
							changes.append(entry)
						if previousAverage > cutoffPoint and newAverage <= cutoffPoint:
							changes.append(entry)

						if (newAverage > cutoffPoint):
							for variant in card.get(CARD_SETS):
								for setCode in lastSet:
									if variant.get(SET_CODE).startswith(setCode):
										print("%s is illegal"%cardName, flush=True)

						runs+=1
					break
			if not found:
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
				entry[CARD_TYPE_KEY] = cardTypeAsInt
				jsonData[DATA].append(entry)


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
							diffCard[CARD_TYPE_KEY] = cardData1.get(CARD_TYPE_KEY)
							priceDifferences.append(diffCard)
					found = True
					break
			
			if not found:
				if cardData1.get(STATUS) > 0:
					diffCard = {}
					diffCard[NAME] = cardData1.get(NAME)
					diffCard[STATUS] = cardData1.get(STATUS)
					diffCard[PREVIOUS_STATUS] = -3
					diffCard[CARD_TYPE_KEY] = cardData1.get(CARD_TYPE_KEY)
					priceDifferences.append(diffCard)
	return priceDifferences

def generateSecret():
	secretCards = []
	for card in jsonData.get(DATA):
		a = card.get(NAME) in additionalForbidden
		b = card.get(BANNED) == True
		if not (a or b):
			price = card.get(PRICE)
			if price > cutoffPoint:
				secretCards.append(card)
	return secretCards

def buildSecret():
	secretCards = generateSecret()
	with open(secretWebsitePath, 'w', encoding="utf-8") as outfile:
		outfile.write("\n\n| Card name | Avg $ |")
		outfile.write("\n| :-- | :-- |")

		for card in sorted(secretCards, key=operator.itemgetter(PRICE)):
			cardPrice = card.get(PRICE)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)
			cardStatus = card.get(STATUS)
			if cardStatus != 0:
				outfile.write("\n[%s](%s) | %s |"%(cardName, cardUrl, "{:.4f}".format(cardPrice)))

		outfile.write("\n\n###### [Back home](index)")

def buildPriceDifferencesPage(priceDifferences):
	with open(differencesPath, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThese are the projected changes between the current banlist and the next one.")
		outfile.write("\n\nPlease keep in mind these changes are not definitive and are only based on past prices. We cannot predict the future changes in the market.")
		outfile.write("\n\nFor a list of cards that are likely to move, go [HERE](closeprices)")
		outfile.write("\n\nEstimated number of changes: %d"% len(priceDifferences))
		outfile.write("\n\n| Card name | Previous Status | New Status |")
		outfile.write("\n| :-- |")

		for card in sorted(priceDifferences, key=operator.itemgetter(STATUS, CARD_TYPE_KEY)):
			cardStatus = card.get(STATUS)
			cardStatusAsText = getCardStatusAsString(cardStatus)
			previousCardStatus = card.get(PREVIOUS_STATUS)
			previousCardStatusAsText = getCardStatusAsString(previousCardStatus)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)
			ref = getImageRefStringFromJSONEntry(card)

			outfile.write("\n|%s [%s](%s) | %s | %s |"%(ref, cardName, cardUrl, previousCardStatusAsText, cardStatusAsText))

		outfile.write("\n\n###### [Back home](index)")

def generateCloseCards():
	closeCards = []
	for card in jsonData.get(DATA):
		price = card.get(PRICE)
		newPrice = card.get(LAST_PRICE)
		a = price > cutoffPoint
		b = newPrice <= cutoffPoint
		c = price <= cutoffPoint
		d = newPrice > cutoffPoint
		
		e = (a and b) or (c and d)

		if e:
			cardName = card.get(NAME)
			f = card.get(NAME) in additionalForbidden
			g = card.get(STATUS) == 0
			if not (f or g):
				h = a and card.get(PROJECTED_STATUS) != -1
				i = c and card.get(PROJECTED_STATUS) == -1
				if (h or i): 
					closeCards.append(card)

	return closeCards

def buildCloseCardsPage(closeCards):
	with open(closePricesPath, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThis is a list of cards that are likely to change legality before the next rotation.")
		outfile.write("\n\n| Card name | Average | Last | Projected legality |")
		outfile.write("\n| :-- |")

		for card in sorted(closeCards, key=operator.itemgetter(PRICE)):
			cardPrice = card.get(PRICE)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)
			cardStatus = card.get(STATUS)
			cardLastPrice = card.get(LAST_PRICE)
			projectedLegality = card.get(PROJECTED_STATUS)
			legalityAsString = getCardStatusAsString(projectedLegality)
			if cardStatus != 0:
				outfile.write("\n[%s](%s) | %s | %s | %s |"%(cardName, cardUrl, "{:.4f}".format(cardPrice), "{:.2f}".format(cardLastPrice), legalityAsString))

		outfile.write("\n\n###### [Back home](index)")

def writeLogs():
	with open(banlistHits, 'a', encoding="utf-8") as file:
		for change in changes:
			if not change[STATUS] == 0:
				if change[PRICE] <= cutoffPoint:
					message = "\n> %s became legal at %d"%(change[NAME], change[STATUS])
				else:
					message = "\n> %s became illegal"%(change[NAME])
			file.write(message)


def uploadToGit():
	subprocess.call('git add .')
	subprocess.call('git commit -m \"%s\"'%formatted)
	subprocess.call('git push')

def buildChangesToLegalityPage():
	with open(legalityPath, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle: \"Disco Inferno Forbidden & Limited List\"\n---")
		outfile.write("\n\nThese are the changes we've implemented in addition to the original Forbidden and Limited list.")
		outfile.write("\n\nCards are still subject to the $0.50 cutoff point and, unless listed here, to the original F&L status.")

		if len(additionalForbidden)>0:
			outfile.write("<br>\n\n### Forbidden:\n\n| Card name | Status |")
			outfile.write("\n| :-- | --: |")
			for card in sorted(jsonData.get(DATA), key=operator.itemgetter(CARD_TYPE_KEY)):
				cardName = card.get(NAME)
				if (cardName in additionalForbidden):
					cardUrl = getCardUrl(cardName)
					ref = getImageRefFromCardName(cardName)
					outfile.write("\n%s [%s](%s) | Forbidden |"%(ref, cardName, cardUrl))

		
		if len(additionalLimited)>0:
			outfile.write("<br>\n\n### Limited:\n\n| Card name | Status |")
			outfile.write("\n| :-- | --: |")
			for card in sorted(jsonData.get(DATA), key=operator.itemgetter(CARD_TYPE_KEY)):
				cardName = card.get(NAME)
				if (cardName in additionalLimited):
					cardUrl = getCardUrl(cardName)
					ref = getImageRefFromCardName(cardName)
					outfile.write("\n%s [%s](%s) | Limited |"%(ref, cardName, cardUrl))

		if len(additionalSemiLimited)>0:
			outfile.write("<br>\n\n### Semi-Limited:\n\n| Card name | Status |")
			outfile.write("\n| :-- | --: |")
			for card in sorted(jsonData.get(DATA), key=operator.itemgetter(CARD_TYPE_KEY)):
				cardName = card.get(NAME)
				if (cardName in additionalSemiLimited):
					cardUrl = getCardUrl(cardName)
					ref = getImageRefFromCardName(cardName)
					outfile.write("\n%s [%s](%s) | Semi-Limited |"%(ref, cardName, cardUrl))

		if len(additionalUnlimited)>0:
			outfile.write("<br>\n\n### Unlimited:\n\n| Card name | Status |")
			outfile.write("\n| :-- | --: |")
			for card in sorted(jsonData.get(DATA), key=operator.itemgetter(CARD_TYPE_KEY)):
				cardName = card.get(NAME)
				if (cardName in additionalUnlimited):
					cardUrl = getCardUrl(cardName)
					ref = getImageRefFromCardName(cardName)
					outfile.write("\n%s [%s](%s) | No Longer Limited |"%(ref, cardName, cardUrl))

		outfile.write("\n\n###### [Back home](index)")



def buildNextBanlist():
	with open(ongoingBanlist, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle: \"Disco Inferno Forbidden & Limited List\"\n---")
		outfile.write("\n\nThis is the %s Disco Inferno banlist."%(nextBanlistName))
		outfile.write("\n\nYou can find the most recent banlist file [HERE](https://drive.google.com/file/d/1E6Y4P6NovTzc6q9uiefR8b2fd3g6mbR2/view)")
		outfile.write("\n\nKeep in mind this is very much subject to changes up until the last minute.")
		outfile.write("\n\n|Card name | Status |")
		outfile.write("\n| :-- | --: |")
		for card in sorted(jsonData.get(DATA), key=operator.itemgetter(STATUS, CARD_TYPE_KEY)):
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)
			ref = getImageRefStringFromJSONEntry(card)
			status = card.get(STATUS)
			statusAsString = getCardStatusAsString(status)
			outfile.write("\n%s [%s](%s) | %s |"%(ref, cardName, cardUrl, statusAsString))
		outfile.write("\n\n###### [Back home](index)")


def getCardFromCardName(cardName):
	for card in cardsFromAPI:
		if (cardName == card.get(NAME)):
			return card
	return None

def getImageRefFromCardName(cardName):
	card = getCardFromCardName(cardName)
	return getImageRefStringFromInteger(getCardTypeAsInteger(card))


def getImageRefStringFromInteger(cType):
	if cType == CARD_TYPE_NORMAL_MONSTER:
		return "<img src=\"assets/vanilla.png\" alt=\"Normal Monster\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_EFFECT_MONSTER:
		return "<img src=\"assets/effect.png\" alt=\"Effect Monster\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_RITUAL_MONSTER:
		return "<img src=\"assets/ritual.png\" alt=\"Ritual Monster\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_FUSION_MONSTER:
		return "<img src=\"assets/fusion.png\" alt=\"XYZ Fusion\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_LINK_MONSTER:
		return "<img src=\"assets/link.png\" alt=\"Link Monster\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_SYNCHRO_MONSTER:
		return "<img src=\"assets/synchro.png\" alt=\"Synchro Monster\" width=\"12\" height=\"12\"/>"	
	if cType == CARD_TYPE_XYZ_MONSTER:
		return "<img src=\"assets/xyz.png\" alt=\"XYZ Monster\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_SPELL:
		return "<img src=\"assets/spell.png\" alt=\"Spell\" width=\"12\" height=\"12\"/>"
	if cType == CARD_TYPE_TRAP:
		return "<img src=\"assets/trap.png\" alt=\"Trap\" width=\"12\" height=\"12\"/>"

def getImageRefStringFromJSONEntry(card):
	cType = card.get(CARD_TYPE_KEY)
	return getImageRefStringFromInteger(cType)
	

def getCardTypeAsInteger(card):
	cType = card.get(CARD_TYPE)
	if ("Monster" in cType):
		cardType = "Monster"
		if "XYZ" in cType:
			return CARD_TYPE_XYZ_MONSTER
		elif "Synchro" in cType:
			return CARD_TYPE_SYNCHRO_MONSTER
		elif "Fusion" in cType:
			return CARD_TYPE_FUSION_MONSTER
		elif "Normal" in cType:
			return CARD_TYPE_NORMAL_MONSTER
		elif "Link" in cType:
			return CARD_TYPE_LINK_MONSTER
		elif "Ritual" in cType:
			return CARD_TYPE_RITUAL_MONSTER
		else:
			return CARD_TYPE_EFFECT_MONSTER
	elif ("Spell" in cType):
		return CARD_TYPE_SPELL
	elif ("Trap" in cType):
		return CARD_TYPE_TRAP


def buildEverything():
	loadConstants()

	cards = getCardsFromAPI()
	for card in cards:
		cardsFromAPI.append(card)

	generatePriceData(cards)

	cards = jsonData.get(DATA)

	applyCutOff(cards)

	dumpJson()

	buildLflist()

	priceDifferences = generatePriceDifferences()
	buildPriceDifferencesPage(priceDifferences)

	closeCards = generateCloseCards()
	buildCloseCardsPage(closeCards)

	buildSecret()

	writeLogs()

	buildChangesToLegalityPage()
	buildNextBanlist()

	if len(forceLegal)>0:
		print(forceLegal)

	if len(newSetCards)>0:
		print(newSetCards)

def buildAndUpload():
	buildEverything()
	print("Uploading to git...", flush=True)
	uploadToGit()
	print("Uploaded\n", flush=True)

buildAndUpload()

schedule = True
if (schedule):
	sched = BlockingScheduler()
	sched.daemonic = False
	sched.add_job(buildAndUpload, 'interval', minutes=5)
	sched.start()