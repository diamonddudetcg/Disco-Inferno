import urllib.request, json, operator
from datetime import datetime
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

#Token stuff
token = 'Token'

#My keys
name = 'name'
cardId = 'id'
status = 'status'
price = 'price'

#Filenames for banlist file
banlistFilename = 'banlist/disco_inferno.lflist.conf'

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
		outfile.write("!Disco Inferno %s.%s\n\n" % (datetime.now().month, datetime.now().year))
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

				if (tcgplayerPrice == 0):
					# Something fucked is going on
					banTcg = -1
				if card.get(name) in additionalForbidden:
					banTcg = -1
				if card.get(name) in additionalLimited:
					banTcg = 1
				if card.get(name) in additionalSemiLimited:
					banTcg = 2

				if tcgplayerPrice >= cutoffPoint:
					banTcg = -1

				for variant in images:
					simpleCard = {}
					simpleCard[name] = card.get(name)
					simpleCard[status] = banTcg
					simpleCard[cardId] = variant.get(cardId)
					simpleCards.append(simpleCard)



generateArrays()
printBanlist()