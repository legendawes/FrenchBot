import requests
import urllib
import urllib.parse
import random
import datetime
import time
import json
import re
from requests import get, post


import urllib
import urllib.parse
from bs4 import BeautifulSoup

from requests.packages.urllib3.exceptions import InsecureRequestWarning

TELEGRAM_KEY_FILE = 'telegram_api.key'
TRANSLATION_KEY_FILE = 'translation_api.key'

def read_key_file(service):
    if service == 'Telegram':
        key_file = TELEGRAM_KEY_FILE
    elif service == 'Translation':
        key_file = TRANSLATION_KEY_FILE
    else:
        raise Exception('Service name is not correct, cannot read keys')
        
    try:
        with open(key_file) as f:
            read_token = f.readline().strip()
    except FileNotFoundError:
        raise Exception('{0} key file not found, please place your {0} API token to {1} file'.format(service, key_file))
    
    return read_token
    
TELEGRAM_TOKEN = read_key_file('Telegram')
TRANSLATION_TOKEN = read_key_file('Translation')

URL = "https://api.telegram.org/bot{}/".format(TELEGRAM_TOKEN)

def get_url(url):
		try:
				response = get(url, verify=False)
		except:
				return -1
		if response.status_code != 200:
				return -1
		content = response.content.decode("utf8")
		return content

def get_json_from_url(url):
		content = get_url(url)
		if content == -1:
				return -1
		js = json.loads(content)
		return js

def get_updates(offset=None):
		url = URL + "getUpdates"
		if offset:
				url += "?offset={}".format(offset)
		js = get_json_from_url(url)
		return js

def get_last_update_id(updates):
		update_ids = []
		for update in updates["result"]:
				update_ids.append(int(update["update_id"]))
		if len(update_ids) > 0:
				return max(update_ids)
		else:
				return 0

def get_last_chat_id_and_text(updates):
		num_updates = len(updates["result"])
		last_update = num_updates - 1
		text = updates["result"][last_update]["message"]["text"]
		chat_id = updates["result"][last_update]["message"]["chat"]["id"]
		return (text, chat_id)


def build_keyboard(items, one_time=False):
		keyboard = [[item] for item in items]
		reply_markup = {"keyboard":keyboard, "one_time_keyboard": one_time}
		return json.dumps(reply_markup)

def send_message(text, chat_id, reply_markup=None, disable_notif = False):
		text = urllib.parse.quote_plus(text)
		url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
		if reply_markup:
				url += "&reply_markup={}".format(reply_markup)
		if disable_notif:
				url += "&disable_notification={}".format(disable_notif)
		get_url(url)

def send_location(long, lati, chat_id, reply_markup=None):
		url = URL + "sendLocation?latitude={}&longitude={}&chat_id={}".format(long, lati, chat_id)
		if reply_markup:
				url += "&reply_markup={}".format(reply_markup)
		get_url(url)

def send_sticker(chat_id):
		url = URL + "sendSticker?sticker={}&chat_id={}".format("BQADAgADggADpYkkAAGTevttSAtYLgI", chat_id)
		# if reply_markup:
		#     url += "&reply_markup={}".format(reply_markup)
		get_url(url)

def send_photo(link, chat_id, reply_markup=None):
		url = URL + "sendPhoto?photo={}&chat_id={}".format(link, chat_id)
		if reply_markup:
				url += "&reply_markup={}".format(reply_markup)
		get_url(url)

def handle_updates(updates, outfile):
		for update in updates["result"]:
				try:
						json.dump(update, outfile)

						if "text" in update["message"]:
								text_handler(update)
				except:
						pass


def translate(city_name, final_lang="en"):
		template = 'https://translate.yandex.net/api/v1.5/tr.json/translate?&key={}c&text={}&lang={}'
		url = template.format(TRANSLATION_TOKEN, city_name, final_lang)
		json_request = get(url).json()
		if json_request['text'][0].strip('"') == city_name.strip('"'):
			url = template.format(TRANSLATION_TOKEN, city_name, 'fr')
			json_request = get(url).json()
		return json_request['text'][0]

def verb_handler(verb):
		times = ['Présent', 'Passé composé', 'Imparfait', 'Futur simple', 'Plus-que-parfait']

		if (verb.count(' ') > 0):
				verb = verb.replace(' ', '_')
		template = 'http://la-conjugaison.nouvelobs.com/du/verbe/{}.php'
		url = template.format(verb)
		req = get(url)

		inc_ind = {'Indicatif':0, 'Conditionnel':1, 'Subjonctif':2}

		assert req.status_code == 200, 'request failed'
		soup = BeautifulSoup(req.text, "lxml")
		tempstab = soup.findAll('div', attrs={'class': 'tempstab'})
		result = ''
		for time in times:
				hey = []
				for temp in tempstab:
						if (temp.findAll('img', attrs={'alt': time}) != []):
								hey.append(temp)

				if (len(hey) == 0):
						print('Conjugation not found for verb {}, try:'.format(verb))
						print(url)
				else:
						hey = hey[0].find('div', attrs={'class': 'tempscorps'})
						text = re.sub(r"(\w*)(je|tu|il|elle|nous|vous|ils)", r"\1; \2", hey.get_text())[2:]
						result += '{} : {}\n'.format(time, text)

		time = 'Présent'
		for inc in ['Conditionnel','Subjonctif']:
				hey = []
				for temp in tempstab:
						if (temp.findAll('img', attrs={'alt': time}) != []):
								hey.append(temp)

				if (len(hey) == 0):
						print('Conjugation not found for verb {}, try:'.format(verb))
						print(url)
				else:
						hey = hey[inc_ind[inc]].find('div', attrs={'class': 'tempscorps'})
						if inc == 'Subjonctif':
							text = hey.get_text()
							text = re.sub(r"(\w*)(qu)", r"\1; \2", text)
						else:
							text = re.sub(r"(\w*)(je|tu|il|elle|nous|vous|ils)", r"\1; \2", hey.get_text())[2:]
						result += '{} : {}\n'.format(inc + ' '+ time, text[2:])       

		# Subjonctif



		# pronouns = ['tu ', 'il ', 'elle ', 'nous ', 'vous ', 'ils ']

		# backup = result
		# was_wrong = False
		# for test in pronouns:
			 #  index = 0
			 #  counter = 0
			 #  while index != -1:
			 #      counter += 1
			 #      if counter > 20:
			 #          print('wrong')
			 #          was_wrong = True
			 #          break
			 #      index = result.find(test)
			 #      if index != -1:
			 #          result = result[:index] + ' ' + test[0].upper() + result[index+1:]
		# if was_wrong:
		#   return backup
		return result

def text_handler(update):
    phrase = update["message"]["text"]
    chat = update["message"]["chat"]["id"]
    if phrase == "/start":
            name = update["message"]["chat"]["first_name"]

            send_message("God bless you, {}".format(name), chat)
            return
    answer = ''
    if (phrase.count(' ') == 0):
            phrase = phrase.replace(' ', '-')
    noun = phrase
    try:
        answer += '{} means {}\n'.format(noun, translate(noun, final_lang='fr-en'))
    except:
        answer += 'translations failed'
    template = 'http://www.linternaute.com/dictionnaire/fr/definition/{}/'
    try:
            url = template.format(noun)
            req = get(url)

            soup = BeautifulSoup(req.text, "lxml")
            word = soup.select('.dico_title_1')[0]
            word_str = word.get_text()
            genre = soup.select('.dico_title_definition')[0]
            genre_str = genre.get_text().replace('\n', '').replace('\t', '').strip()
            answer += '{} is {}\n'.format(word_str, genre_str)
    except:
            pass
            # answer += '(genre detection failed)'

    send_message(answer, chat)
    try:
            send_message(verb_handler(noun), chat)
    except:
            pass


def main():
		try:
				outfile = open('log.json', 'w+')

				requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

				last_update_id = None
				updates = get_updates(last_update_id)
				last_update_id = get_last_update_id(updates) + 1
				while True:
						updates = get_updates(last_update_id)
						if updates != -1:
								if len(updates["result"]) > 0:
										last_update_id = get_last_update_id(updates) + 1
										print(updates)
										handle_updates(updates, outfile)
								time.sleep(0.1)
		except:
				pass

if __name__ == '__main__':
		main()
