import urllib.request, json, operator, os, time, datetime
from os.path import exists
from datetime import date
from apscheduler.schedulers.background import BlockingScheduler

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
PREVIOUS_RUNS = 'previousRuns'

#Banlist status
BANNED = 'Banned'
LIMITED = 'Limited'
SEMI = 'Semi-Limited'
UNLIMITED = 'Unlimited'


ongoingBanlistSite = 'docs/ongoing.md'
diBanlistPath = 'json/banlist/di_banlist.json'
jsonData = {}

cutoffPoint = 0.50

forceMonth = True

month = 9
previousMonth = 8
year = 2022
jumpYear = False


today = date.today()

if not forceMonth:
	formatted = today.strftime("%Y/%m/%d, %H:%M:%S")
	stableHiddenSite = 'docs/hidden/banlist_%s.md'%(today.strftime("%Y_%m"))
	jsonPath = 'json/%s.json'%(today.strftime("%Y_%m"))
	banlistPath = 'banlist/ongoing/disco_inferno_%s.lflist.conf'%today.strftime("%Y_%m")

	month = int(today.strftime("%m"))
	if (month == 1):
		previousMonth = 12
		jumpYear = True
	else:
		previousMonth = month - 1

	year = int(today.strftime("%Y"))
	if (jumpYear):
		year -=1

	previousMonth = date.today()
	previousMonth = date(year, previousMonth, today.day)

	previousDataPath = 'json/%s.json'%(previousMonth.strftime("%Y_%m"))

else:
	formatted = "%s%s%s"%(today.strftime("%Y/"),  f'{month:02d}', today.strftime("/%d, %H:%M:%S"))
	stableHiddenSite = 'docs/hidden/banlist_%s%s.md'%(today.strftime("%Y_"),  f'{month:02d}')
	jsonPath = 'json/%s%s.json'%(today.strftime("%Y_"),  f'{month:02d}')
	banlistPath = 'banlist/ongoing/disco_inferno_%s%s.lflist.conf'%(today.strftime("%Y_"), f'{month:02d}')

	previousDataPath = 'json/%s_%s.json'%(f'{year:04d}',f'{previousMonth:02d}')

differencesPath = 'docs/differences.md'

def getCardStatusAsString(cardStatus):
	cardStatusAsText = "Unlimited"
	if (cardStatus == -3):
		cardStatusAsText = "Card did not exist in the last banlist"
	if (cardStatus == -2):
		cardStatusAsText = "Illegal (no price data)"
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
	return "https://db.ygoprodeck.com/card/?search=%s"%cardName.replace(" ", "%20").replace("&", "%26")

def buildEverything():

	with open(diBanlistPath) as banlistFile:
		banlist = json.load(banlistFile)
		additionalForbidden = banlist.get(BANNED)
		additionalLimited = banlist.get(LIMITED)
		additionalSemiLimited = banlist.get(SEMI)
		additionalUnlimited = banlist.get(UNLIMITED)

	jsonData = {PREVIOUS_RUNS:0, DATA:[]}
	if os.path.exists(jsonPath):
		with open(jsonPath) as file:
			jsonData = json.load(file)

	runs = jsonData.get(PREVIOUS_RUNS)
	jsonData[PREVIOUS_RUNS] = (runs + 1)

	with urllib.request.urlopen(request) as url:
		
		cards = json.loads(url.read().decode()).get(DATA)
		
		for card in cards:

			if card.get(CARD_SETS) == None:
				continue
			if card.get(CARD_TYPE) == SKILL or card.get(CARD_TYPE) == TOKEN:
				continue

			isLDSColoredUltra = False

			for cardSet in card.get(CARD_SETS):
				if cardSet.get(SET_CODE).startswith('LDS'):
					if cardSet.get(SET_RARITY_CODE) == "(UR)":
						isLDSColoredUltra = True

			images = card.get(CARD_IMAGES)
			cardPrices = card.get(CARD_PRICES)[0]
			tcgplayerPrice = float(cardPrices.get(TCGPLAYER_PRICE))
			cardmarketPrice = float(cardPrices.get(CARDMARKET_PRICE))
			avgPrice = min(tcgplayerPrice, cardmarketPrice)
			if (cardmarketPrice + tcgplayerPrice > 2):
				# This prevents errors like Blue-Eyes Alternative Dragon
				avgPrice = max(tcgplayerPrice, cardmarketPrice)
			if (isLDSColoredUltra):
				avgPrice = min(tcgplayerPrice, cardmarketPrice)

			banInfo = card.get(BANLIST_INFO)

			banTcg = 3
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

			if card.get(NAME) in additionalForbidden:
				banTcg = 0
			if card.get(NAME) in additionalLimited:
				banTcg = 1
			if card.get(NAME) in additionalSemiLimited:
				banTcg = 2
			if card.get(NAME) in additionalUnlimited:
				banTcg = 3


			if runs == 0:
				newAverage = avgPrice
				if (newAverage == 0):
					# Something fucked is going on
					banTcg = -2
				ids = []
				for variant in images:
					ids.append(variant.get(CARD_ID))
				entry = {}
				entry[NAME] = card.get(NAME)
				entry[CARD_IDS] = ids
				entry[PRICE] = newAverage
				entry[STATUS] = banTcg
				jsonData[DATA].append(entry)

			else:
				for entry in jsonData.get(DATA):
					if entry.get(NAME) == card.get(NAME):
						previousAverage = entry.get(PRICE)
						newAverage = (previousAverage * runs + avgPrice)/(runs+1)
						entry[PRICE] = newAverage
						entry[STATUS] = banTcg

	cards = jsonData.get(DATA)

	for card in cards:
		if card[PRICE] > cutoffPoint:
			card[STATUS] = -1

	with open(banlistPath, 'w', encoding="utf-8") as outfile:
			outfile.write("#[Disco Inferno]\n")
			outfile.write("!Disco Inferno %s\n\n" % today.strftime("%m_%Y"))
			outfile.write("\n$whitelist\n\n")
			for card in cards:
				cardBanlistStatus = card.get(STATUS)
				if cardBanlistStatus < -1:
					cardBanlistStatus = -1
				for cardId in card.get(CARD_IDS):
					try:
						outfile.write("%d %d -- %s\n" % (cardId, cardBanlistStatus, card.get(NAME)))
					except TypeError:
						print(card)

	with open(jsonPath, 'w', encoding="utf-8") as file:
		json.dump(jsonData, file, indent=4)

	with open(previousDataPath) as file:
		previousPriceData = json.load(file)

	with open(differencesPath, 'w', encoding="utf-8") as outfile:
		cardDifferences = []
		for cardData1 in jsonData.get(DATA):
			found = False
			
			for cardData2 in previousPriceData.get(DATA):
				if (cardData1.get(NAME) == cardData2.get(NAME)):
					previousStatus = cardData2.get(STATUS)
					currentStatus = cardData1.get(STATUS)
					if (previousStatus != currentStatus):
						diffCard = {}
						diffCard[NAME] = cardData1.get(NAME)
						diffCard[STATUS] = cardData1.get(STATUS)
						diffCard[PREVIOUS_STATUS] = cardData2.get(STATUS)
						cardDifferences.append(diffCard)
						found = True
					break
			
			if not found:
				if cardData1.get(STATUS) > 0:
					diffCard = {}
					diffCard[NAME] = cardData1.get(NAME)
					diffCard[STATUS] = cardData1.get(STATUS)
					diffCard[PREVIOUS_STATUS] = -3


		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThese are the projected changes between the current banlist and the next one.")
		outfile.write("\n\nPlease keep in mind these changes are not definitive and are only based on past prices. We cannot predict the future changes in the market.")
		outfile.write("\n\n| Card name | Previous Status | New Status |")
		outfile.write("\n| :-- | :-- | :-- |")

		for card in sorted(cardDifferences, key=operator.itemgetter(STATUS)):
			cardStatus = card.get(STATUS)
			cardStatusAsText = getCardStatusAsString(cardStatus)
			previousCardStatus = card.get(PREVIOUS_STATUS)
			previousCardStatusAsText = getCardStatusAsString(previousCardStatus)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)

			outfile.write("\n|[%s](%s) | %s | %s |"%(cardName, cardUrl, previousCardStatusAsText, cardStatusAsText))

		outfile.write("\n\n###### [Back home](index)")

	with open(ongoingBanlistSite, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThis is the current status for every card for next month as it stands right now. This is not binding, but it gets more accurate as the month goes on.")
		outfile.write("\n\nTo avoid market manipulation, we regularly check the prices for every card in both CardMarket and TCGPlayer. Instead of looking at the prices of the market once, we compound the average for the entire month to define legality during the next one.")
		outfile.write("\n\nNote that these prices might not (and probably will not) reflect reality at any single point except the first run of the month. These are average prices for an entire month, not a snapshot of any single moment in time.")
		outfile.write("\n\n| Card name | Status | Average Price |")
		outfile.write("\n| :-- | :-- | :-- |")

		for card in sorted(cards, key=operator.itemgetter(STATUS)):
			cardStatus = card.get(STATUS)
			cardStatusAsText = getCardStatusAsString(cardStatus)
			cardName = card.get(NAME)
			cardUrl = getCardUrl(cardName)

			outfile.write("\n| [%s](%s) | %s | %s |"%(cardName, cardUrl, cardStatusAsText, "{:.2f}".format(card.get(PRICE))))

		outfile.write("\n\n###### [Back home](index)")

	with open(stableHiddenSite, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\n## Disco Inferno F&L list for %s"%today.strftime("%B %Y"))
		outfile.write("\n\n[You can find the EDOPRO banlist here](https://drive.google.com/file/d/1DJHIE40SD25ICctEbBVulGPetKiE9kTT/view?usp=sharing). Open the link, click on the three dots in the top right and then click Download.")
		outfile.write("\n\nThe banlist file goes into the lflists folder in your EDOPRO installation folder. Assuming you use Windows, it usually is C:/ProjectIgnis/lflists")
		outfile.write("\n\nEDOPRO will not recognize a change in banlists while it is open. You will have to restart EDOPRO for the changes to be reflected.")
		outfile.write("\n\n| Card name | Status |")
		outfile.write("\n| :-- | :-- |")

		for card in sorted(cards, key=operator.itemgetter(STATUS)):
			cardStatus = card.get(STATUS)
			cardStatusAsText = "Unlimited"
			if (cardStatus == -1):
				cardStatusAsText = "Illegal"
			elif (cardStatus == 0):
				cardStatusAsText = "Forbidden"
			elif (cardStatus == 1):
				cardStatusAsText = "Limited"
			elif (cardStatus == 2):
				cardStatusAsText = "Semi-Limited"

			cardUrl = "https://db.ygoprodeck.com/card/?search=%s"%card.get(NAME).replace(" ", "%20").replace("&", "%26")

			outfile.write("\n| [%s](%s) | %s |"%(card.get(NAME), cardUrl, cardStatusAsText))

		outfile.write("\n\n###### [Back home](index)")

	print("Executed a run", flush=True)

	os.system('git add .')
	os.system('git commit -m \"%s\"'%formatted)
	os.system('git push')

buildEverything()

sched = BlockingScheduler()
sched.daemonic = False
sched.add_job(buildEverything, 'interval', minutes=60)
sched.start()