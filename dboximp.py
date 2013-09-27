# dropbox test
from dropboxlogin import get_client
import codecs
import shelve
import logging
logging.basicConfig(level=logging.INFO)

def import_dropbox(force = False):
	'''
	Returns list of arrays of cvs lines
	Lines are preprocessed according to bank's format.
	'''
	db = shelve.open('dropboxfiles.db')
	client = get_client()
	meta = client.metadata('/xpense')
	files = meta['contents']
	res = []
	for f in files:
		if f['is_dir']: continue 
		path = f['path']
		if path in db:
			logging.info('Already imported file %s',
			             path)
			if not force:
				logging.info('... skipping')
				continue
			else: 
				logging.info('... forcing import')
		db[path] = True
		file, meta = client.get_file_and_metadata(path)
		lines = file.read().splitlines()
		file.close()
		logging.info('Read file %s with %i bytes',
		             path, len(lines))
		# Preprocess
		del lines[0:4]
		del lines[-1]
		
		res.append(lines)
		
	db.close()
	return res
	
if __name__ == '__main__':
	# caution: this will set files to imported!
	f = import_dropbox()

