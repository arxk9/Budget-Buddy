"""
This bot listens to port 5002 for incoming connections from Facebook. It takes
in any messages that the bot receives and echos it back.
"""
from flask import Flask, request, send_file
from pymessenger.bot import Bot
import requests as req, os, sqlite3, datetime, pickle, random, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random, pprint
app = Flask(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'db', 'main.db'), SECRET_KEY='key_Nf2pcQCFfljQorbqc2jF', USERNAME='user_H3ASmhvLlFqUGYLV20OT', PASSWORD='pass_ZREW9p59FK8Go303pY3h'))
ACCESS_TOKEN = 'EAAF3bT1uUmwBAGGYp6ivkaIe3oP0UXlb1lgXChawqWZArjpb2YQR0PJxO7RZC01XacSNQGj5ltp84ozklwJZA86kAVdCabx3f03CkjLNbkHltfP2ab1CnhhVQL82K0ArZCOba70oYkIwaGcRBuzKLjp8xXT7MXNf1Bno6u5IFAqIZACO3AJst'
VERIFY_TOKEN = 'my_voice_is_my_password_verify_me'
bot = Bot(ACCESS_TOKEN)
USERINFO = {'name': 'Alan Zheng',
 'percent_savings': 10,
 'saved': 10000,
 'incomes': [{'title': 'Tutoring','hourly_pay': 7.25},
             {'title': 'McDonalds','monthly_pay': 1120}],

 'category_savings': {'housing': 500,
                      'utility': 200,
                      'clothing': 50,
                      'food': 300,
                      'misc': 100,
                      'transportation': 50,
                      'entertainment': 30}
 }
WIT_ACCESS_TOKEN = 'FWUYKGJQUBZI4O5D7KQEPFZGA5OB4OEK'

def parseIntent(msg):
    """ Queries wit.ai to find the intent. """
    headers = {'Authorization': 'Bearer ' + WIT_ACCESS_TOKEN}
    r = req.get('https://api.wit.ai/message', headers=headers, params={'q': msg}).json()
    return r


def format_parse(r):
    if r['entities'].get('intent'):
        msg = ''
        for intt in r['entities']['intent']:
            msg += ('Intent: {}, confidence: {:.2f}%\n').format(intt['value'], intt['confidence'] * 100)

        for entity in [x for x in r['entities'] if x != 'intent']:
            if r['entities'][entity][0].get('unit'):
                msg += ('{}: {} {}, confidence: {:.2f}%\n').format(entity, r['entities'][entity][0]['value'], r['entities'][entity][0]['unit'], r['entities'][entity][0]['confidence'] * 100)
            else:
                msg += ('{}: {}, confidence: {:.2f}%\n').format(entity, r['entities'][entity][0]['value'], r['entities'][entity][0]['confidence'] * 100)

        return msg.strip()
    else:
        return ('No intent found. I got: {}').format(pprint.pformat(r, indent=4))


def init_db():
    pickle.dump([], open(os.path.join(app.root_path, 'db.pk'), 'wb'))


def ledge(user_id, purchase_time, item_name, amount, category):
    db = pickle.load(open(os.path.join(app.root_path, 'db.pk'), 'rb'))
    db.append([str(user_id), str(purchase_time), str(item_name), str(amount), str(category)])
    pickle.dump(db, open(os.path.join(app.root_path, 'db.pk'), 'wb'))


def intentToLedge(user_id, msg):
    parsed = parseIntent(msg)
    if not parsed.get('entities') or not parsed['entities'].get('intent'):
        return "I'm sorry, I don't understand!"
    intent = parsed['entities']['intent'][0]['value']
    if intent in frozenset({'sold', 'buy', 'regular payment', 'sell', 'earned', 'bought'}):
        r = -1 if intent in frozenset({'regular payment', 'buy', 'bought'}) else 1
        if parsed['entities'].get('category'):
            category = parsed['entities']['category'][0]['value']
        else:
            category = 'Miscellaneous'
        try:
            value = parsed['entities']['amount_of_money'][0]['value'] * r
            units = parsed['entities']['amount_of_money'][0]['unit']
            item = parsed['entities']['agenda_entry'][0]['value']
            ledge(user_id, datetime.datetime.now(), item, value, category)
            return random.choice(['Your transaction has been accounted for.', "Ok, got it."])
        except:
            return "I'm not quite sure what you meant. (Uncertainty above 50%)"

        if intent == 'question/buy':
            item = parsed['entities']['agenda_entry'][0]['value']
            if parsed['entities']['category'][0]['value']:
                category = parsed['entities']['category'][0]['value']
            else:
                category = 'Miscellaneous'
            msg = 'You have {} money left in the {} category.'
            if random.random() > 0.5:
                msg += ('\nYou can afford the {}').format(item)
            else:
                msg += ('\nYou should probably save money and abstain from buying the {}').format(item)
            return msg
        if intent == 'save' or intent == 'question/save':
            if parsed['entities']['category'][0]['value']:
                category = parsed['entities']['category'][0]['value']
            else:
                category = 'Miscellaneous'
            msg = ('So you want to save more in the {} category.').format(category)
            msg += ('\nIt seems you are not using a lot of the money in the {} category. Maybe you can reduce the budget value there.').format('Miscellaneous')
            return msg
        if intent == 'change':
            if parsed['entities'].get('category'):
                category = parsed['entities']['category'][0]['value']
            else:
                category = 'Miscellaneous'
            msg = ('So you want to change the way you spend in the {} category.').format(category)
            msg += '\nTake a look at your spending. Which categories are you spending more or less than what your budget allows? Try accomodating all these changes in a new budget.'
            return msg
        if intent == 'monthly_graph':
            plt.rcdefaults()
            objects = ('Food', 'Housing', 'Entertainment', 'Miscellaneous', 'Clothing',
                      'Transportation', 'Utility')
            y_pos = np.arange(len(objects))
            expenditures = [0, 0, 0, 0, 0, 0, 0]
            for line in get_ledger():
                expenditures[objects.index(line[4])] += int(line[3])

            plt.bar(y_pos, expenditures, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            plt.tick_params(labelsize=12)
            plt.ylabel('$')
            plt.title('Money spent by category')
            plt.savefig('temp.png')
            bot.send_image_url(user_id, 'https://hackybot.sites.tjhsst.edu/img')


def user_in_db(user_id):
    db = get_db()
    cur = db.execute('select * from users where user_id=?', [user_id])
    return len(cur.fetchall()) != 0


def parseMessages(output):
    """ Converts raw output to (recipient_id, message) """
    for event in output['entry']:
        messaging = event['messaging']
        for x in messaging:
            if x.get('message'):
                recipient_id = x['sender']['id']
                if x['message'].get('text'):
                    message = x['message']['text']
                    yield (recipient_id, message)


@app.route('/img', methods=['GET'])
def img():
    return send_file('temp.png', mimetype='image/png')


@app.route('/img2', methods=['GET'])
def img2():
    return send_file('img2.png', mimetype='image/png')

@app.route('/', methods=['GET', 'POST'])
def messenger_parser():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return 'Invalid verification token'
    if request.method == 'POST':
        output = request.get_json()
        for uid, msg in parseMessages(output):
            if 'expenditure' in msg.lower():
                mess = (
                 'Your net expenditure is', sum([int(thing[3]) for thing in get_ledger()]))
            else:
                if msg.lower().startswith("raw "):
                    mess = format_parse(parseIntent(msg[4:]))
                elif "hey" in msg.lower() or "hello" in msg.lower():
                    mess = "Hi, what can I do for you?"
                elif "tutor" in msg.lower():
                    ledge(uid, datetime.datetime.now(), "Tutoring", 32, "Miscellaneous")
                    mess = "Ok, added."
                elif 'clear' in msg.lower():
                    init_db()
                    mess = 'Ledger cleared.'
                elif "graph" in msg.lower():
                    mess = "Okay, here you go! https://hackybot.sites.tjhsst.edu/img2"
                elif 'ledger' in msg.lower():
                    mess = ''
                    if get_ledger() is []:
                        mess = 'Ledger is empty.'
                    else:
                        for thing in get_ledger():
                            if float(thing[3]) < 0:
                                mess += ('On {} you spent {} for {}. Category: {}\n').format(thing[1], -float(thing[3]), thing[2], thing[4])
                            else:
                                mess += ('On {} you bought/earned {} for {}. Category: {}\n').format(thing[1], thing[3], thing[2], thing[4])
                else:
                    mess = intentToLedge(uid, msg)
                bot.send_text_message(uid, mess)

        return 'Success'


def get_ledger():
    db = pickle.load(open(os.path.join(app.root_path, 'db.pk'), 'rb'))
    return db


if __name__ == '__main__':
    init_db()
    app.run()
