import json, time, requests, urllib, re
from dbhelper import DBHelper
from collections import defaultdict
import datetime
import schedule 
db = DBHelper()

TOKEN = "1678774174:AAHmFP4s7mbbk2iMt3wkGFEzXO1z__mWQTY"
URL  = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf")
    return(content)

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return(js)

def get_updates(offset=None):
    url = URL + "getUpdates?"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def get_last_chat_id_and_text(updates):
    num_updates = len(updates['result'])
    last_update = num_updates-1
    text = updates['result'][last_update]['message']['text']
    chat_id = updates['result'][last_update]['message']['chat']['id']
    return(text,chat_id)

def send_message(text, chat_id,reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    if(reply_markup):
        url+="&reply_markup={}".format(reply_markup)
    get_url(url)

def sendmessage(text,chat_id,reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    if(reply_markup):
        url+="&reply_markup={}".format(reply_markup)
    get_url(url)
    return schedule.CancelJob


def check(a):
    regex = "^([01]?[0-9]|2[0-3]):[0-5][0-9]$";  
    p = re.compile(regex)
    if(a==""):
        return(False)
    m = re.search(p,a)
    if m is None:
        return(False)
    else:
        return(True)
    
#schedule.every().day.at(str(text)).do(send_message,text=text,chat_id=chat,scheduled = True)
def handle_updates(updates):
    #print('test')
    #print(len(updates))
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
        except:
            continue
        chat = update["message"]["chat"]["id"]
        first_name = update['message']['from']['first_name']
        items = db.get_items(chat)  ##
        if text == "/start":
            message = "Welcome {},\nI can remeber things for you.\nType /info to know about this bot.\nType /help to learn how to communicate with me.\nType text for adding it to the list".format(first_name)
            send_message(message, chat)
        elif text == '/info':
            message = "Hello {},\n This bot can be used to keep track of your to do list. You can also add time to get reminded.\nPlease note that you will get reminded only once. Also scheduled remainders cannot be cancelled.\nThis bot is still under development and will be developed soon.\nThanks for using this bot!!!".format(first_name)
            send_message(message,chat)
        elif text == "/delete":
            keyboard = build_keyboard(items)
            message = "Please select one task from the below"
            send_message(message,chat,keyboard)
        elif text == '/help':
            message = '/info to know about this bot.\n/new - to add a new item\n/list - to get list of all tasks\n/addtime - to schedule a message \n/end - to end a task \n/help - to get list of all commands\n/delete - to delete a tast.\n/deleteall - to delete all to do tasks.\n/time - to know the server time'
            send_message(message,chat)
        elif text == "/deleteall":
            for i in items:
                db.delete_item(i,chat)
            message = "to do list is cleared"
            send_message(message,chat)
        elif text=="/time":
            current_time = datetime.datetime.now()
            message = str(current_time.hour)+":"+str(current_time.minute)
            send_message(message,chat)
        elif text == "/list":
            for i in range(len(items)):
                if(items[i].startswith("l4sts3l3ct3d_")):
                    items[i] = items[i][13:]
            message = ""
            options = ['/delete','/deleteall']
            keyboard = build_keyboard(options)
            for i in range(len(items)):
                items[i]=str(i+1)+") "+items[i]
            message = message = "\n".join(items)
            if(message == ""):
                message = "your to do list is empty.\nType text to add remainders"
            send_message(message,chat,keyboard)
        elif(text=="/addtime"):
            message = "take_time_as_input"
            if(message not in items):
                db.add_item(message,chat)
            message = "Plese enter time in 24 hrs format (HH:MM) else select /end. \nAlso please note that the server currently follows USA time. Type /time to know the server time.\nSo you can't schedule messages according to local time. This will be fixed soon.!!!"
            options = ['/list','/end','/time']
            keyboard = build_keyboard(options)
            send_message(message,chat,keyboard)
        elif(text=="/end"):
            if("take_time_as_input" in items):
                db.delete_item("take_time_as_input",chat)
        elif text.startswith("/"):
            message = "{} command doesn't exist. \nType /help to see list of available commands".format(text)
            options = ['/help','info']
            send_message(message, chat)
        else:
            mess = ""
            for i in items:
                if(i.startswith("l4sts3l3ct3d_")):
                    mess = i[13:]
            if("take_time_as_input" in items):
                istime = check(text)
                if(istime):
                    mess = "remainder for --> "+mess 
                    schedule.every().day.at(str(text)).do(sendmessage,text=mess,chat_id=chat)
                    db.delete_item("take_time_as_input",chat)
                    message = "scheduled successfully"
                    send_message(message,chat)
                else:
                    message = "Plese enter time in 24 hrs format (HH:MM) else select /end \n. Also please note that the server currently follows USA time. Type /time to know the server time.\n. So you can't schedule messages according to local time. This will be fixed soon.!!!"
                    options = ['/new','/list','/end']
                    keyboard = build_keyboard(options)
                    send_message(message,chat,keyboard)
            else:
                if(text in items):
                    db.delete_item(text,chat)
                    message = "Task deleted."
                    options = ['/list','/delete','/deleteall','/help','info']
                    keyboard  = build_keyboard(options)
                    send_message(message,chat,keyboard)
                else:
                    for i in range(len(items)):
                        if(items[i].startswith("l4sts3l3ct3d_")):
                            a = items[i][13:]
                            db.delete_item(items[i],chat)
                            db.add_item(a,chat)
                    message = "Task added to the list successfully.\nIf you want to get reminded select /addtime."
                    options = ['/addtime','/list','/help']
                    keyboard = build_keyboard(options)
                    db.add_item("l4sts3l3ct3d_"+text,chat)
                    send_message(message,chat,keyboard)


def build_keyboard(items):
    keyboard =[[item] for item in items]
    reply_markup = {"keyboard":keyboard,"one_time_keyboard":True}
    return( json.dumps(reply_markup))

def main():
    db.setup()
    last_update_id = None
    while True:
        schedule.run_pending()
        while True:     
            updates = get_updates(last_update_id)
            if len(updates["result"]) > 0:
                last_update_id = get_last_update_id(updates) + 1
                handle_updates(updates)
            break


if __name__ == '__main__':
   
    main()
