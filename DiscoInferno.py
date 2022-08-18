import urllib.request, json, operator
from datetime import date
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

additionalForbidden = [
	"Amazoness Archer",
	"Artifact Scythe",
	"Cannon Soldier",
	"Cannon Soldier MK-2",
	"Fairy Tail - Snow",
	"Morphtronic Telefon",
	"Toon Cannon Soldier",
	
	"Gouki the Powerload Ogre",
	
	"Number 33: Chronomaly Machu Mech",
	
	"Hot Red Dragon Archfiend King Calamity",

	"Numeron Calling",
	
	"Anti-Spell Fragrance",
	"Dimensional Barrier",
	"Gozen Match"
	"Harpie's Feather Storm",
	"Rivalry of Warlords",
	"Summon Limit",
	"There Can Be Only One"
]

additionalLimited = [

]

additionalSemiLimited = [

]


cutoffPoint = 0.50

#Banlist status
banned = 'Banned'
limited = 'Limited'
semi = 'Semi-Limited'

#YGOPRODECK API keys
data = 'data'
card_sets = 'card_sets'
banlist_info = 'banlist_info'
ban_tcg = 'ban_tcg'
rarity_code = 'set_rarity_code'
card_images = 'card_images'
cardType = 'type'
card_prices = 'card_prices'
tcgplayer_price = 'tcgplayer_price'
cardmarket_price = 'cardmarket_price'

#Token stuff
token = 'Token'

#My keys
name = 'name'
cardId = 'id'
status = 'status'
price = 'price'


today = date.today()
formatted = today.strftime("_%m_%Y")

testFolder = ""

#Filenames for banlist file
historicBanlistFilename = '%sbanlist/disco_inferno%s.lflist.conf'%(testFolder,formatted)
banlistFilename = '%sbanlist/disco_inferno.lflist.conf'%(testFolder)
siteFilename = '%sdocs/banlist.md'%(testFolder)
siteHistoricFilename = '%sdocs/banlist%s.md'%(testFolder, formatted)

#Card arrays
siteCards = []
simpleCards = [] # List of all TCG legal cards for banlist generation
ocgCards = [] # List of all OCG exclusive cards for banlist generation.


def writeCardToBanlist(card, outfile):
	try:
		outfile.write("%d %d -- %s\n" % (card.get(cardId), card.get(status), card.get(name)))
	except TypeError:
		print(card)

def printBanlist():
	print("Writing banlist", flush=True)
	with open(banlistFilename, 'w', encoding="utf-8") as outfile:
		outfile.write("#[Disco Inferno]\n")
		outfile.write("!Disco Inferno %s\n\n" % today.strftime("%m_%Y"))
		outfile.write("\n$whitelist\n\n")
		for card in simpleCards:
			writeCardToBanlist(card, outfile)
	print("Writing historic banlist", flush=True)
	with open(historicBanlistFilename, 'w', encoding="utf-8") as outfile:
		outfile.write("#[Disco Inferno]\n")
		outfile.write("!Disco Inferno %s\n\n" % today.strftime("%m_%Y"))
		outfile.write("\n$whitelist\n\n")
		for card in simpleCards:
			writeCardToBanlist(card, outfile)

def generateArrays():
	with urllib.request.urlopen(request) as url:
		cards = json.loads(url.read().decode()).get(data)
		for card in cards:
			if card.get(card_sets) != None:
				images = card.get(card_images)
				banInfo = card.get(banlist_info)
				cardPrices = card.get(card_prices)[0]
				tcgplayerPrice = float(cardPrices.get(tcgplayer_price))
				cardmarketPrice = float(cardPrices.get(cardmarket_price))
				avgPrice = (tcgplayerPrice + cardmarketPrice)/2


				banInfo = card.get(banlist_info)
				banTcg = 3
				if (banInfo == None):
					banTcg = 3	
				if (banInfo != None):
					banlistStatus = banInfo.get(ban_tcg)
					if (banlistStatus == None):
						banTcg = 3
					if (banlistStatus == banned):
						banTcg = 0
					if (banlistStatus == limited):
						banTcg = 1
					if (banlistStatus == semi):
						banTcg = 2

				if (avgPrice == 0):
					# Something fucked is going on
					banTcg = -1
				if card.get(name) in additionalForbidden:
					banTcg = -1
				if card.get(name) in additionalLimited:
					banTcg = 1
				if card.get(name) in additionalSemiLimited:
					banTcg = 2

				if avgPrice >= cutoffPoint:
					banTcg = -1

				if card.get(cardType) == "Skill":
					banTcg = -1

				alreadyInSite = False
				for variant in images:
					simpleCard = {}
					simpleCard[name] = card.get(name)
					simpleCard[status] = banTcg
					simpleCard[cardId] = variant.get(cardId)
					simpleCards.append(simpleCard)
					if not alreadyInSite:
						siteCards.append(simpleCard)
						alreadyInSite = True

def writeCardToSite(card, outfile):
	cardStatus = card.get(status)
	cardStatusAsText = "Unlimited"
	if (cardStatus == -1):
		cardStatusAsText = "Illegal"
	elif (cardStatus == 0):
		cardStatusAsText = "Forbidden"
	elif (cardStatus == 1):
		cardStatusAsText = "Limited"
	elif (cardStatus == 2):
		cardStatusAsText = "Semi-Limited"

	cardUrl = "https://db.ygoprodeck.com/card/?search=%s"%card.get(name).replace(" ", "%20").replace("&", "%26")

	outfile.write("\n| [%s](%s) | %s |"%(card.get(name), cardUrl, cardStatusAsText))

def writeCardsToSite(cards, outfile):
	for card in sorted(cards, key=operator.itemgetter('status')):
		writeCardToSite(card,outfile)

def writeHeader(outfile):
	outfile.write("---\ntitle:  \"Disco Inferno\"\n---")
	outfile.write("\n\n## Disco Inferno F&L list for %s"%today.strftime("%B %Y"))
	outfile.write("\n\n[You can find the EDOPRO banlist here](https://drive.google.com/file/d/1DJHIE40SD25ICctEbBVulGPetKiE9kTT/view?usp=sharing). Open the link, click on the three dots in the top right and then click Download.")
	outfile.write("\n\nThe banlist file goes into the lflists folder in your EDOPRO installation folder. Assuming you use Windows, it usually is C:/ProjectIgnis/lflists")
	outfile.write("\n\nEDOPRO will not recognize a change in banlists while it is open. You will have to restart EDOPRO for the changes to be reflected.")
	outfile.write("\n\n| Card name | Status |")
	outfile.write("\n| :-- | :-- |")

def writeFooter(outfile):
	outfile.write("\n\n###### [Back home](index)")

def printSite():
	print("Writing default site", flush=True)
	with open(siteFilename, 'w', encoding="utf-8") as siteFile:
		writeHeader(siteFile)
		writeCardsToSite(siteCards, siteFile)
		writeFooter(siteFile)
	print("Writing historic site", flush=True)
	with open(siteHistoricFilename, 'w', encoding="utf-8") as siteFile:
		writeHeader(siteFile)
		writeCardsToSite(siteCards, siteFile)
		writeFooter(siteFile)

generateArrays()
printBanlist()
printSite()