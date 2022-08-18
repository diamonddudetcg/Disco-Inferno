import os
from datetime import date


print('Generating Disco Inferno banlist', flush=True)
os.system('python DiscoInferno.py')
print('Committing to Github', flush=True)

today = date.today()
formatted = today.strftime("%d/%m/%Y")

os.system('git add .')
os.system('git commit -m \"%s\"'%formatted)
os.system('git push')