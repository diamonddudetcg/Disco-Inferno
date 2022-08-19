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
PRICE = 'price'
PREVIOUS_RUNS = 'previousRuns'

#Banlist status
BANNED = 'Banned'
LIMITED = 'Limited'
SEMI = 'Semi-Limited'
UNLIMITED = 'Unlimited'

today = date.today()

jsonPath = 'json/%s.json'%today.strftime("%Y_%m")
banlistPath = 'banlist/ongoing/disco_inferno_%s.lflist.conf'%today.strftime("%Y_%m")
ongoingBanlistSite = 'docs/ongoing.md'
diBanlistPath = 'json/banlist/di_banlist.json'
jsonData = {}

cutoffPoint = 0.50


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

			images = card.get(CARD_IMAGES)
			cardPrices = card.get(CARD_PRICES)[0]
			tcgplayerPrice = float(cardPrices.get(TCGPLAYER_PRICE))
			cardmarketPrice = float(cardPrices.get(CARDMARKET_PRICE))
			avgPrice = min(tcgplayerPrice, cardmarketPrice)
			if (avgPrice == 0):
				avgPrice = max(tcgplayerPrice, cardmarketPrice)

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

			if (avgPrice == 0):
				# Something fucked is going on
				banTcg = -1
			if card.get(NAME) in additionalForbidden:
				banTcg = 0
			if card.get(NAME) in additionalLimited:
				banTcg = 1
			if card.get(NAME) in additionalSemiLimited:
				banTcg = 2

			if runs == 0:
				newAverage = avgPrice
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

	cards = jsonData.get(DATA)

	for card in cards:
		if card[PRICE] > cutoffPoint:
			card[STATUS] = -1

	with open(banlistPath, 'w', encoding="utf-8") as outfile:
			outfile.write("#[Disco Inferno]\n")
			outfile.write("!Disco Inferno %s\n\n" % today.strftime("%m_%Y"))
			outfile.write("\n$whitelist\n\n")
			for card in cards:
				for cardId in card.get(CARD_IDS):
					try:
						outfile.write("%d %d -- %s\n" % (cardId, card.get(STATUS), card.get(NAME)))
					except TypeError:
						print(card)

	with open(jsonPath, 'w') as file:
		json.dump(jsonData, file, indent=4)

	with open(ongoingBanlistSite, 'w', encoding="utf-8") as outfile:
		outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
		outfile.write("\n\nThis is the current status for every card for next month as it stands right now. This is not binding, but it gets more accurate as the month goes on.")
		outfile.write("\n\nTo avoid market manipulation, we regularly check the prices for every card in both CardMarket and TCGPlayer. Instead of looking at the prices of the market once, we compound the average for the entire month to define legality during the next one.")
		outfile.write("\n\nNote that these prices might not (and probably will not) reflect reality at any single point except the first run of the month. These are average prices for an entire month, not a snapshot of any single moment in time.")
		outfile.write("\n\n| Card name | Average Price | Status |")
		outfile.write("\n| :-- | :-- | :-- |")

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

			outfile.write("\n| [%s](%s) | %s | %s |"%(card.get(NAME), cardUrl, "{:.2f}".format(card.get(PRICE)), cardStatusAsText))

		outfile.write("\n\n###### [Back home](index)")

	print("Executed a run", flush=True)

buildEverything()

sched = BlockingScheduler()
sched.daemonic = False
sched.add_job(buildEverything, 'interval', minutes=60)
sched.start()