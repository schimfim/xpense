# Importer

import csv
import hashlib
import string
import shelve
import logging
logging.basicConfig(level=logging.INFO)
from dboximp import import_dropbox
from re import match
pat = '0?([0-9]+)\.([0-9]+)\.([0-9]+)'

dbname = 'xpense.db'

def str2f(s):
	# remove 1000 sep
	s1 = s.replace('.', '')
	# change dec sep
	s2 = s1.replace(',', '.')
	return s2

def import_file(lines):
	imported = 0
	skipped = 0
	# Import one csv file
	reader = csv.DictReader(lines, delimiter = ';')
	db = shelve.open(dbname)
	for row in reader:
		# gather data
		amt = str2f(row['Soll']) + str2f(row['Haben'])
		(date, note) = row['Buchungstag'], row['Verwendungszweck']
		rep = match(pat, date)
		(dy,mo,yr) = rep.groups()
		key = hashlib.md5(date + amt + note).hexdigest()
		d = dict(year=yr, orig_year=yr, month=mo, orig_month=mo, orig_day=dy, day=dy, amount=float(amt), note=note, type='', subtype='', category='')
		# write to db
		if db.has_key(key):
			logging.warning('Skipping duplicate %s', note[0:8])
			skipped += 1
		else: 
			db[key] = d
			imported += 1
			
	logging.info('Imported: %i', imported)
	logging.info('Skipped: %i', skipped)
	db.close()
	
def import_all(force = False):
	files = import_dropbox(force)
	for f in files:
		import_file(f)

def load():
	db = shelve.open(dbname, writeback=True)
	return db

if __name__ == '__main__':
	import_all()
