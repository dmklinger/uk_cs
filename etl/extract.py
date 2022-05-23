import bz2
import os
import io
import requests
import json
import lzma
import zipfile
from urllib import parse
from collections import defaultdict
from bs4 import BeautifulSoup, NavigableString

from dictionary import Word

os.makedirs('data', exist_ok=True)
session = requests.session()

def load_inflections(use_cache=True):
	dictionary = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [])))
	def get_data():
		if use_cache and os.path.exists('data/morphs.tsv'):
			return
		print('downloading latest morphological data data from MorfFlex')
		with session.get('https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3186/czech-morfflex-2.0.tsv.xz?sequence=1&isAllowed=y', stream=True) as f:
			data = lzma.open(f.raw).read()
		print('decompressing')
		with open('data/morphs.tsv', 'wb+') as f:
			f.write(data)
		print('decompressing finished')
	
	# https://ufal.mff.cuni.cz/pdt/Morphology_and_Tagging/Doc/hmptagqr.html

	def make_forms():
		def add_forms(dictionary, pos, subpos, gender, number, case, possgender, possnumber, person, tense, grade, negation, voice, reserve1, reserve2, var, word):
			# if pos == 'V' and (negation == 'A' or negation == '-') and var == '-':
			# print(properties, lemma, word)
			if var == '-' and (negation == 'A' or negation == '-') and reserve2 == '-':
				if number == 'D' and pos == 'N':
					number = 'P'
				case = {
					'1': 'nom',
					'2': 'gen',
					'3': 'dat',
					'4': 'acc',
					'5': 'voc',
					'6': 'loc',
					'7': 'ins'
				}[case] if case in ('1', '2', '3', '4', '5', '6', '7') else None 
				if case and pos != 'V':
					if grade == '1' or grade == '-':
						if gender in ('F', 'N', 'M'):
							dictionary[lemma][pos][f"{case} {gender}{number}".lower()].append(word)
						if gender == 'H':
							dictionary[lemma][pos][f"{case} f{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} n{number}".lower()].append(word)
						if gender == 'I':
							dictionary[lemma][pos][f"{case} i{number}".lower()].append(word)
						if gender == 'Q':
							dictionary[lemma][pos][f"{case} ms"].append(word)
							dictionary[lemma][pos][f"{case} np"].append(word)
						if gender == 'T':
							dictionary[lemma][pos][f"{case} i{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} f{number}".lower()].append(word)
						if gender == 'Y':
							dictionary[lemma][pos][f"{case} m{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} i{number}".lower()].append(word)
						if gender == '-':
							dictionary[lemma][pos][f"{case} {number}".lower()].append(word)
						if gender == 'X':
							dictionary[lemma][pos][f"{case} m{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} i{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} n{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} f{number}".lower()].append(word)
						if gender == 'Z':
							dictionary[lemma][pos][f"{case} m{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} i{number}".lower()].append(word)
							dictionary[lemma][pos][f"{case} n{number}".lower()].append(word)

					elif case == 'nom' and number == 'S' and gender in ('M', 'H', 'Y', 'I'):
						if grade == '2':
							dictionary[lemma][pos]["addl comp"].append(word)
						if grade == '3':
							dictionary[lemma][pos]["addl super"].append(word)
				if subpos == 'f':
					dictionary[lemma][pos]['inf'].append(word)
				if subpos == 'B':
					if reserve1 != 'I' or tense == 'F':
						this_tense = 'fut'
					else:
						this_tense = 'pres'
					dictionary[lemma][pos][f"{this_tense} {person}{number}".lower()].append(word)
				if subpos == 'i':
					dictionary[lemma][pos][f"imp {person}{number}".lower()].append(word)
				if subpos in ('p', 's') and not case:
					this_voice = 'act' if subpos == 'p' else 'pas'
					if gender == 'Q':
						dictionary[lemma][pos][f"{this_voice} pp fs"].append(word)
						dictionary[lemma][pos][f"{this_voice} pp np"].append(word)
					if gender == 'T':
						dictionary[lemma][pos][f"{this_voice} pp ip"].append(word)
						dictionary[lemma][pos][f"{this_voice} pp fp"].append(word)
					if gender == 'Y':
						dictionary[lemma][pos][f"{this_voice} pp as"].append(word)
						dictionary[lemma][pos][f"{this_voice} pp is"].append(word)
					if gender == 'N':
						dictionary[lemma][pos][f"{this_voice} pp n{number}".lower()].append(word)
					if gender == 'M':
						dictionary[lemma][pos][f"{this_voice} pp a{number}".lower()].append(word)

		if use_cache and os.path.exists('data/forms.json'):
			return
		with open('data/morphs.tsv', 'r', encoding='utf-8') as f:
			data = f.read()
		data = data.split('\n')
		n = len(data)
		denomination = 1000000
		for i, line in enumerate(data[:-1]):
			if i % denomination == 0:
				print(f"{i // denomination} of {n // denomination}")
			lemma, properties, word = line.split()
			lemma = lemma.split('_')[0]
			pos, subpos, gender, number, case, possgender, possnumber, person, tense, grade, negation, voice, reserve1, reserve2, var = [x for x in properties]
			add_forms(dictionary, pos, subpos, gender, number, case, possgender, possnumber, person, tense, grade, negation, voice, reserve1, reserve2, var, word)
			if lemma == 'můj':
				print(properties, lemma, word)
			if lemma == 'sám':
				print(properties, lemma, word)
			if lemma == 'jeho':
				print(properties, lemma, word)
			if lemma == 'sám':
				print(properties, lemma, word)
			if gender == 'F' and number == 'X' and case == 'X':
				for num in ('S', 'P'):
					for c in ('1', '2', '3', '4', '5', '6', '7'):
						add_forms(dictionary, pos, subpos, gender, num, c, possgender, possnumber, person, tense, grade, negation, voice, reserve1, reserve2, var, word)
			
		with open(f'data/forms.json', 'w+', encoding='utf-8') as f:
			f.write(json.dumps(dictionary, indent=2, ensure_ascii=False))
	
	get_data()
	make_forms()
	with open(f'data/forms.json', 'r', encoding='utf-8') as f:
		data = json.loads(f.read())
	return data

form_data = load_inflections()

try:
	with open('data/wiktionary_raw_data.json', 'r', encoding='utf-8') as f:
		wiktionary_cache = json.loads(f.read())
except:  # does not exist yet
	wiktionary_cache = {}

def get_viewstate(bs=None):
	if bs is None:
		url = "https://lcorp.ulif.org.ua/dictua/dictua.aspx"
		req = session.get(url)
		data = req.text
		bs = BeautifulSoup(data, features='lxml')
	return (
		bs.find("input", {"id": "__VIEWSTATE"}).attrs['value'],
		bs.find("input", {"id": "__VIEWSTATEGENERATOR"}).attrs['value'],
		bs.find("input", {"id": "__EVENTVALIDATION"}).attrs['value'],
	)

vs, vsg, ev = get_viewstate()

try:
	with open('data/inflection_raw_data.json', 'r', encoding='utf-8') as f:
		inflection_cache = json.loads(f.read())
except:
	inflection_cache = {}


def get_ontolex(use_cache=True):
	if use_cache and os.path.exists('data/raw_dbnary_dump.ttl'):
		return
	print('downloading latest ontolex data from dbnary')
	with session.get('http://kaiko.getalp.org/static/ontolex/latest/en_dbnary_ontolex.ttl.bz2', stream=True) as f:
		data = bz2.BZ2File(f.raw).read()
	print('decompressing')
	with open('data/raw_dbnary_dump.ttl', 'wb+') as f:
		f.write(data)
	print('decompressing finished')


def get_inflection(w):
	results = []
	word = w.word
	print(word)
	if word in form_data:
		for x in form_data[word]:
			word_info = ''
			forms = form_data[word][x]
			if x != 'V':
				form = 'noun'
				genders = set()
				for f in forms: 
					has_gender = len(f.split()[-1]) == 2
					gender = f.split()[-1][0]
					genders.add(gender)
				if len(genders) > 1:
					form = 'adj'
				if form == 'noun':
					new_forms = {}
					for f in forms:
						gen_length = len(f.split()[-1])
						if gen_length <= 2:
							new_forms[f[0:4] + 'n' + f[5:]] = forms[f]
							if gen_length == 2:
								word_info += f" {f[4]}".lower()
						else:
							new_forms[f] = forms[f]
					forms = new_forms
					if 'acc ns' in forms and 'gen ns' in forms and 'nom ns' in forms:
						if len(set(forms['acc ns']) & set(forms['nom ns'])) > 0:
							word_info += ' inan'
						if len(set(forms['gen ns']) & set(forms['acc ns'])) > 0:
							word_info += ' animate'
			else:
				form = 'verb'
				if 'pres 1f' in forms:
					word_info += ' pf'
				else:
					word_info += ' impf'
			results.append([word, word_info.strip(), forms, form])
	return results

def dump_inflection_cache():
	with open(f'data/inflection_raw_data.json', 'w+', encoding='utf-8') as f:
		f.write(json.dumps(inflection_cache, ensure_ascii=False, indent=2))


def get_frequency_list():
	try:
		with open('data/frequencies.json', 'r', encoding='utf-8') as f:
			data = json.loads(f.read())
	except:  # does not exist yet	
		data = defaultdict(lambda: {})

		rows = []

		with session.get('https://wiki.korpus.cz/lib/exe/fetch.php/seznamy:syn2015_lemma_utf8.zip', stream=True) as f:
			with zipfile.ZipFile(io.BytesIO(f.content)) as zip_ref:
				with zip_ref.open('syn2015_lemma_utf8.tsv') as f:
					for line in io.TextIOWrapper(f, encoding='utf-8'):
						rows.append(line.split('\t'))
		for x in rows:
			if len(x[0]) > 0:
				data[
					x[1]  # word
				] = int(x[0])  # rank
		with open(f'data/frequencies.json', 'w+', encoding='utf-8') as f:
			f.write(json.dumps(data, indent=2, ensure_ascii=False))
	return data