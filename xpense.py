import csv
import pprint
import hashlib
import string
import importer
import json
from logging import warning, error, info, debug

def fdate(i,yr,mo):
	b = i['year'] == yr
	if mo:
		b &= i['month'] == mo
	return b
		
def by_date(items, yr, mo=None):
	res = []
	for i in items:
		if fdate(i,yr,mo):
			res.append(i)
	return res

def print_items(items):
	for i in items:
		print '#' * 10
		fmt = '{day}.{month}.{year} {amount:.2f} EUR ({subtype})'
		print fmt.format(**i)
		if not i['subtype']:
			print i['note']

cat_def = {
	'Variabel' : {
			'Lebenshaltung' : {
				'Supermarkt' : ['EDEKA', 'REWE', 'ERDKORN', 'BUDNI', 'METRO', 'M.SIMON', 'GUT WULKSFELDE', 'FAMILA', 'IHR REAL', 'GETRAENKE', 'SKY MARKT', 'NETTO'],
				'Benzin' : ['SHELL']
				},
			'Bar' : {
				'GA-City' : ['HH-SPEI'],
				'GA-Vdorf' : ['HH-VOLK', 'GA NR06006361'],
				'Kreditarte' : ['KREDITKARTE']
				},
			'Konsum' : {
				'Diverse' : ['PFLKOELLE', 'HAGEL HAIRCOMPANY AEZ']
			  },
			'Freizeit' : {
				'Restaurant' : ['RESTAURANT',
				                 'BLOCK HOUSE']
				}
			},
	'Fix' : {
		  'Monat' : {
		  	'Haus' : ['WASSERABSCHLAG', 'HAUPTDARLEHENSNR', 'VATTENFALL', 'E.ONHANSE'],
				'Kinder' : ['FAM.ANTEIL KITA', 'MUSIKALISCHE FRUEHERZIEHUNG', 'BETREUUNGSENTGELT', 'RWsoft', 'RWSOFT'],
				'Versicherungen' : ['SIGNAL KRANKENVERS', 'HDI LEBENSVERSICHERUNG'],
				'Auto' : ['LASTSCHRIFT ING-DIBA'],
				'Einkommen' : ['VERDIENSTABRECHNUNG', 'BARBARA DOERING'],
				'Telekom' : ['TELEKOM']
				},
			'Quartal' : {
				'Steuer' : ['GRUNDST'],
				'Haus1' : ['GEBUEHRENBESCHEID STADTREINIGUNG'],
				'Diverse1' : ['BLAU-WEISS-ROT']
				}
			},
	'Sonder' : {
	  	'Sonder' : {
	    	'Einmal' : ['REINE,DR. AUSZAHLUNG REINE']
	    	},
	    'Erstattet' : {
	    	'Arzt' : ['LOGOPAEDIE', 'MEDISERV', 'DGPAR']
	   	 }
		}
	}

def icats(cdef):
	'''
	icats(cdef)
	Subtypes must be unique!
	'''
	cats = {}
	rules = {}
	for ck in cdef:
		for sk in cdef[ck]:
			for st in cdef[ck][sk]:
				if st in cats:
					warning('Duplicate subtype %s', st)
				cats[st] = [sk, ck]
				rules[st] = cdef[ck][sk][st]
	return cats, rules

def match(s):
	for k in rules.keys():
		for v in rules[k]:
			if s.find(v) >= 0:
				return k
	return ''

def insert(tree, item, mo, cat, type, sub):
	if mo not in tree:
		tree[mo] = {}
	cats = tree[mo]
	if cat not in cats:
		cats[cat] = {'_sum':0.0}
	tipes = cats[cat]
	if type not in tipes:
		tipes[type] = {'_sum':0.0}
	subs = tipes[type]
	if sub not in subs:
		subs[sub] = {'items':[], '_sum':0.0}
	items = subs[sub]
	items['items'].append(item)
	items['_sum'] += item['amount']
	subs['_sum'] += item['amount']
	tipes['_sum'] += item['amount']

def apply_rules(items, tree = None):
	for i in items:
		s = match(i['note'])
		mo = i['month']
		if s:
			t = cats[s]
			i['subtype'] = s
			i['type'] = t[0]
			i['category'] = t[1]
			if tree != None:
				insert(tree, i, mo, t[1], t[0], s)
		else:
			i['subtype'] = 'Ohne'
			i['type'] = 'Ohne'
			i['category'] = 'Ohne'
			if tree != None:
				insert(tree, i, mo, 'Ohne', 'Ohne', 'Ohne')

def print_all(tree, details=False):
	for mo in sorted(tree.keys()):
		# what about years?
		print '*** Month: ' + mo
		cats = tree[mo]
		for cat in cats:
			tipes = cats[cat]
			print cat, '=', str(tipes['_sum'])
			for type in tipes:
				if type[0] == '_': continue 
				subs = tipes[type]
				print '  ', type, '=', str(subs['_sum'])
				for sub in subs:
					if sub[0] == '_': continue 
					items = subs[sub]
					print '    ', sub, '=', str(items['_sum'])
					if details:
						for i in items['items']:
							print '      * ' + str(i['amount'])

def print_missing(tree):
	for mo in sorted(tree.keys()):
		# what about years?
		print '*** Month: ' + mo
		cats = tree[mo]
		try:
			tipes = cats['Ohne']
		except KeyError: continue 
		subs = tipes['Ohne']
		items = subs['Ohne']
		for i in items['items']:
			print 'note:', str(i['note'])

db = importer.load()
#aug = by_date(items, '2013', '07')

(cats, rules) = icats(cat_def)
#with open('categories.py', 'w') as f:
#	json.dump(cat_def, f, indent=2)
#print cats
#print rules
tree = {}
apply_rules(db.itervalues(), tree)
#print_items(db.itervalues())
db.close()
print_all(tree, False  )
#print_missing(tree)

