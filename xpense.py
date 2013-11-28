import csv
import pprint
import hashlib
import string
import importer
import json
from logging import warning, error, info, debug


def fdate(i, yr, mo):
	"""
	Compares "year" and "month" fields of dict i to parameters yr and mo
	"""
	b = i['year'] == yr
	if mo:
		b &= i['month'] == mo
	return b


def by_date(items, yr, mo=None):
	"""
	Returns list of entries from items where yr and mo match the resp. "year" and "month" fields
	"""
	res = []
	for i in items:
		if fdate(i,yr,mo):
			res.append(i)
	return res


def print_items(items):
	"""
	print_items(items)
	Print all individual account entries from list items with subtypes.
	"""
	# TODO: really needed?
	for i in items:
		print '#' * 10
		fmt = '{day}.{month}.{year} {amount:.2f} EUR ({subtype})'
		print fmt.format(**i)
		if not i['subtype']:
			print i['note']


def load_cat_def():
	"""
	Load category definitions from categories.py
	"""
	with open('categories.py') as f:
		new_def = json.load(f)
		return new_def


def save_cat_def(new_def):
	"""
	Save category definitions in new_def to file categories.py.
	Format is json
	"""
	with open('categories.py', 'w') as f:
		json.dump(new_def, f, indent=2)


def icats(cdef):
	'''
	icats(cdef)
	Caluculates flat category list and rules from category definitions
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


def match(s, rules):
	"""
	Matches string s against rules in 'rules'.
	Returns matching subtype as defined in rules or empty string if no match
	Matching is performed by String.find()
	rules is a dict of the form { subtype(String) : [ pattern(String)* ] }
	"""
	# TODO: Use regexp instead of find
	for k in rules.keys():
		for v in rules[k]:
			if s.find(v) >= 0:
				return k
	return ''


def insert(tree, item, cat, type, sub):
	"""
	Insert account entry "item" into category tree "tree" at location { mo : cat : type : sub }.
	mo: month, cat: category, type: expense type, sub: subtype.
	At each node (cat/type/sub) the sum of the included account entries is maintained
	in field '_sum'.
	"""
	mo = item['month']
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

def align(item):
	"""
	Align date in item to month boundary.
	item is modified!
	"""
	mo = int(item['orig_month'])
	dy = int(item['orig_day'])
	yr = int(item['orig_year'])
	
	if dy > 15:
		# roll over to next month
		dy = 1
		mo += 1
		if mo == 13:
			mo = 1
			yr += 1
		dy = '{:02d}'.format(dy)
		mo = '{:02d}'.format(mo)
		yr = '{:d}'.format(yr)
		item.update(day=dy, month=mo, year=yr)
	

def apply_rules(items, item_tree, cats, rules):
	"""
	Matches account entries in 'items' against global 'rules'
	Sets resp. fields 'category', 'type' and 'subtype' => items is modified!
	Items are inserted into tree 'item_tree' at matching node
	"""
	for i in items:
		# Find subcategory for item i based on
		# field 'note'
		s = match(i['note'], rules)
		if s:
			# If found, derive type and category from
			# subcategory, based on 'cats'
			t = cats[s]
			sub = s
			type = t[0]
			cat = t[1]

		else:
			# No subtype found, assign to 'Variabel' category
			# TODO: use english types
			sub = 'Ohne'
			type = 'Ohne'
			cat = 'Variabel'
		
		# TODO: Align month/year for category 'Fix'
		align(i)
		
		if item_tree is not None:
				insert(item_tree, i, cat, type, sub)


def print_all(atree, details=False):
	"""
	Print all items in tree 'atree' down to subtypes, with sum of amounts
	If 'details' is True, individual amounts per subtype are printed
	"""
	for mo in sorted(atree.keys()):
		# TODO: display year
		print '*** Month: ' + mo
		cats = atree[mo]
		for cat in cats:
			tipes = cats[cat]
			print cat, '=', str(tipes['_sum'])
			for atype in tipes:
				if atype[0] == '_':
					continue
				subs = tipes[atype]
				print '  ', atype, '=', str(subs['_sum'])
				for sub in subs:
					if sub[0] == '_':
						continue
					items = subs[sub]
					print '    ', sub, '=', str(items['_sum'])
					if details:
						for i in items['items']:
							print '      * ' + str(i['amount'])


def print_missing(atree, save=True):
	"""
	Print all items in tree without subtype assignment
	Optionally save list to missing.py
	"""
	misses = []
	for mo in sorted(atree.keys()):
		# TODO: print years
		print '*** Month: ' + mo
		categories = atree[mo]
		try:
			tipes = categories['Variabel']
			subs = tipes['Ohne']
			items = subs['Ohne']
		except KeyError:
			continue
		for i in items['items']:
			s = str(i['note'])
			print 'note:', s
			misses.append('"' + s + '"\n')
	if save:
		with open('missing.py', 'w') as f:
			f.writelines(misses)

# CLI
import cmd


class XpenseCLI(cmd.Cmd):
	def __init__(self):
		"""
		Initialize CLI
		self.tree contains account entries in category structure
		"""
		cmd.Cmd.__init__(self)
		# Load account entries
		db = importer.load()
		# Load category definitions and transform to optimized format
		cat_def = load_cat_def()
		(cats, rules) = icats(cat_def)
		# Apply rules and build up tree
		self.tree = {}
		apply_rules(db.itervalues(), self.tree, cats, rules)
		# Finish
		db.close()

	def do_all(self, parms):
		print_all(self.tree)

	def do_missing(self, parms):
		print_missing(self.tree)

	def do_EOF(self, parms):
		return True


def run_cli():
	c = XpenseCLI()
	c.cmdloop()

# main: run CLI
if __name__ == '__main__':
	run_cli()
