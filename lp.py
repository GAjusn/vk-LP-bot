import vk_api, traceback, random, time, json, sys, re, requests, os
from datetime import datetime
from vk_api.longpoll import VkEventType, VkLongPoll
from threading import Thread
import wikipedia
from wikipedia.wikipedia import page
from bs4 import BeautifulSoup
from simpledemotivators import Demotivator, Quote
from gtts import gTTS
import ctypes
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

id_my = 490745923
wikipedia.set_lang('ru')

print('''\033[92m __  __  _       _              _
|  \/  |(_) ___ | |__    __ _  | |     _ __
| |\/| || |/ __|| '_ \  / _` | | |    | '_ \\ 
| |  | || |\__ \| | | || (_| | | |___ | |_) |
|_|  |_||_||___/|_| |_| \__,_| |_____|| .__/
                                      |_|\033[0m\n\n''')



def save_db(db):
    with open("db.json", "w") as write_file:
        json.dump(db, write_file, indent=4, ensure_ascii=False)

try:
    with open("db.json", "r") as file:
        db = json.load(file)
except:
    db={'auto_exit': False}
    print('База данных не обнаружена в корневой директории:  ')
    db['access_token']=input('Введите "Кейт" токент:  ')
    db['me_token']=input('Введите "Ми" токент:  ')
    db['trigger_word']=input('Введите триггер слово. Оно будет использоваться для удаления своих сообщений:  ')
    db['prefix']=input('Введите префикс:  ')
    save_db(db)
while True:
    try:
        _vk_=vk_api.VkApi(token=db['access_token'])
        _vk_me_=vk_api.VkApi(token=db['me_token'])
        vk=_vk_.get_api()
        upload_vk = vk_api.VkUpload(_vk_)
        vk_me=_vk_me_.get_api
        my_info=vk.account.getProfileInfo()
        my_id=my_info['id']
        break
    except Exception as e:
        if str(e)=='[5] User authorization failed: invalid access_token (4).' or str(e)=='[5] User authorization failed: invalid session.':
            print('Один из токенов инвалид.')
            db['access_token']=input('Введите "Кейт" токент:  ')
            db['me_token']=input('Введите "Ми" токент:  ')
            save_db(db)
        else:
            print('Непредвиденная ошибка!')
            traceback.print_exc()
            sys.exit()

def demotivator(msg,photo):
    _text_=msg.split('\n')
    if len(_text_)==2:
        little_text=''
        big_text=_text_[1]
    else:
        little_text=_text_[2]
        big_text=_text_[1]
    dem = Demotivator(big_text, little_text)
    filename = requests.get(photo)
    with open('raw\\filename.jpg','wb') as file:
        file.write(filename.content)
    
    dem.create('raw\\filename.jpg', result_filename="raw\\demresult.jpg")
    
    photo = upload_vk.photo_messages('raw\\demresult.jpg')
    owner_id = photo[0]['owner_id']
    photo_id = photo[0]['id']
    access_key = photo[0]['access_key']
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    return attachment

def get_id(event):
    text=event.text
    print(text)
    message=vk.messages.getById(message_ids=event.message_id)['items'][0]
   
    if 'mentions' in event.raw[6]:
        ids=event.raw[6]['mentions']
        return ids

    if 'reply_message' in message:
                ids=[message['reply_message']['from_id']]
                
                return ids

    if len(text.split(' '))>1:
        push = re.findall(r'\[id(.+)\||\[club(.+)\|', text)
        ids = []
        if push:
            for i in push:
                
                if i[0] != '': 
                    ids.append(int(i[0]))
                else:
                    ids.append(-int(i[1]))
            return ids

        

        screen_names = re.findall(r'vk\.\w+\/(\w+)', text)
        ids=[]
        for i in screen_names:
            try:
                id, type=list(vk.utils.resolveScreenName(screen_name=i).values())
                if type=='group':
                    id=-id
                ids.append(id)
            except:
                pass
        return ids
    else:
        return []

def get_push(id=int, name_case=None):
    if id<0:
        id = abs(id)
        name=vk.groups.getById(group_id=id)[0]['name']
        push=f'[club{id}|{name}]'
    else:
        info=vk.users.get(user_ids=[id], name_case=name_case)[0]
        push=f"[id{id}|{info['first_name']} {info['last_name']}]"
    return push

def spam(peer_id=int, text=str, count=int, delay=int):
    if text==None:
        text='Spam {}/{}'
    for i in range(1, count+1):
        vk.messages.send(peer_id=peer_id, message=text.format(i, count), random_id=random.randint(1, 10**9))
        time.sleep(delay)
simulation=False
def set_activity(type=str, peer_id=int):
    while simulation:
        try:
            vk.messages.setActivity(peer_id=peer_id, type=type)
            time.sleep(5)
        except:
            pass


longpoll = VkLongPoll(_vk_)  
upload = vk_api.VkUpload(_vk_)

push_status=False
push_id=0

prefix=db['prefix']
trigger_word=db['trigger_word']
auto_exit=db['auto_exit']

while True:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                text = event.text.lower()
                text_original = event.text
                peer_id = event.peer_id
                chat_id = peer_id - 2000000000
                time_=event.raw[4]
                message_id=event.message_id
         
                if push_status and event.from_me: 
                    if text==f'{prefix}stop':
                        push_status=False
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message='Stoped')
                    else:
                        attachments=list(event.attachments.values())
                        attach = []
                        for i in range(0,len(attachments),2):
                            attach.append(attachments[i]+attachments[i+1])
                        attachments=','.join(attach)
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'[id{push_id}|{event.text}]', attachment=attachments)

                if event.from_me and not push_status:
                    if text==f'{prefix}пинг' or text==f'{prefix}ping':
                        pong=f'Понг лп: {abs(round(datetime.now().timestamp()-time_, 3))} сек.'
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message=pong)
                    if text.startswith(f'{prefix}push'):
                        id_=get_id(event=event)
                        if id_!=[]:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f"Пуш на {get_push(id_[0], 'gen')} начат.")
                            push_status=True
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message='Упоминание человека не найдено!')
                    if text.startswith(f'{prefix}id'):
                        id_=get_id(event=event)
                        if id_!=[]:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f"ID {get_push(id_[0], 'gen')} равен: {id_[0]}")
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message='Упоминание человека не найдено!')
                    if text.startswith(f'{prefix}{trigger_word}'):
                        count=re.findall(r'\d+', text)
                        if not count:
                            count = 2
                        else:
                            count = int(count[0]) + 1
                        for_deletiona=[]
                        offset=0
                        while len(for_deletiona)<count:
                            history=vk.messages.getHistory(
                                count=200,
                                offset=offset,
                                peer_id=peer_id
                                )['items']
                            offset+=200
                            for i in history:
                                if len(for_deletiona)>=count:
                                    break
                                if my_id==i['from_id']:
                                    for_deletiona.append(i['id'])
                        if text.startswith(f'{prefix}{trigger_word}-'):
                            for i in for_deletiona:
                                try:
                                    vk.messages.edit(peer_id=peer_id, message_id=i, message='Скрыто ФСБ')
                                except:
                                    pass
                        vk.messages.delete(message_ids=','.join(map(str,for_deletiona)), delete_for_all=1)
                    if text==f'{prefix}лп':
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'''Имя: {my_info['first_name']}\nФамилия: {my_info['last_name']}\nID: {my_id}\nУдалялка: {trigger_word}\nПрефикс: {prefix}\nАвтовыход: {'✅' if auto_exit else '🚫'}''')  
                    if text.startswith(f'{prefix}спам'):
                        args=re.findall(r'\d+', text)
                        text_to_spam=text_original.split('\n')
                        if len(text_to_spam)>1:
                            text_to_spam='\n'.join(text_to_spam[1:])
                        else:
                            text_to_spam=None
                        if len(args)==0:
                            count=2
                            delay=1
                        elif len(args)==1:
                            count=int(args[0])
                            delay=1
                        elif len(args)==2:
                            count=int(args[0])
                            delay=int(args[1])
                        Thread(target=spam, args=(peer_id, text_to_spam, count, delay)).start()
                    if text.startswith(f'{prefix}реши'):
                        arg=text[len(f'{prefix}реши '):]  
                        if len(arg)>0:
                            try:    
                                msg=f'Ответ: {eval(arg)}'
                            except Exception as e:
                                msg=f'Ошибка: {e}'
                        else:
                            msg='А что решить-то?'
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message=msg)
        
                    if text.startswith(f'{prefix}wiki'):
                        arg=text[len(f'{prefix}wiki '):]
                        if len(arg)>0:
                            try:
                                page=wikipedia.page(arg)
                                link=vk.utils.getShortLink(url= f"https://ru.wikipedia.org/wiki/{page.title.replace(' ', '%20')}")['short_url']
                                vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'''=Кратко=\n\n{page.summary}\nСсылка на статью: {link}.''')
                            except Exception as e:
                                if 'Try another id!' in str(e):
                                    vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'Не удалось найти статью по запросу.')

                        else:
                            msg='А какая статья-то?'   
                        pass
                    if text.startswith(f'{prefix}инфо'):
                        id_=get_id(event=event)
                        if id_!=[]:
                            id_=id_[0]
                            response = requests.get(f'https://vk.com/foaf.php?id={id_}')
                            xml = response.text
                            soup = BeautifulSoup(xml, 'lxml')
                            created = soup.find('ya:created').get('dc:date')
                            datereg=f'{created[8:10]}.{created[5:7]}.{created[0:4]}'
                            info=vk.users.get(user_ids=str(id_), fields=
                            ["sex",
                            "first_name", 
                            "last_name", 
                            "is_closed", 
                            "blacklisted", 
                            "blacklisted_by_me", 
                            "status", 
                            "photo_max_orig", 
                            "counters", 
                            "friend_status", 
                            "city", 
                            "first_name_abl", 
                            "last_name_abl", 
                            "last_seen", 
                            "online", 
                            "screen_name",
                            "bdate"])[0] 
                            friend_status = str(info['friend_status']).replace('0', '🚫').replace('1', 'Заявка на расмотрении.').replace('2', '🔖Имеется входящая заявка.').replace('3', '✅')
                            sex = str(info['sex']).replace('1', '👩').replace('2', '👨').replace('3', 'Не указан')
                            is_closed = str(info['is_closed']).replace('True', '✅').replace('False', '🚫')
                            blacklisted = str(info['blacklisted']).replace('1', '✅').replace('0', '🚫')
                            blacklisted_by_me = str(info['blacklisted_by_me']).replace('1', '✅').replace('0', '🚫')
                            if 'last_seen' in info: 
                                last_seen = str(info['last_seen']['platform']).replace('1', 'Мобильная версия 📱').replace('2', 'Приложение для iPhone 📱').replace('3', 'Приложение для iPad 📱').replace('4', 'Приложение для Android 📱').replace('5', 'Приложение для Windows Phone 📱').replace('6', 'Приложение для Windows 10 📱').replace('7', 'Полная версия сайта 🖥️')
                            else:
                                last_seen = 'Онлайн скрыт 🔒.'
                            
                            try:
                                count_friends=info['counters']['friends']
                            except:
                                count_friends='Скрыто 🔒.'
                            try:
                                count_followers=info['counters']['followers']
                            except:
                                count_followers='Скрыто 🔒.'


                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'''Информация о {info['first_name_abl']} {info['last_name_abl']}, {'Online' if info['online']==1 else 'Offline'}, {last_seen}

⚙ ID: {info['id']}
⚙ Короткая ссылка: {info['screen_name']}
⚙ Имя: {info['first_name']}
⚙ Фамилия: {info['last_name']}
👥 Кол-во друзей: {count_friends}
🎉 Дата регистрации: {datereg}
🎉 Дата рождение: {info['bdate'] if 'bdate' in info else 'Скрыто 🔒.'}
🌆 Город: {info['city']['title'] if 'city' in info else 'Не указан.'}
👻 Друзья: {friend_status}
✍🏻 Подписчики: {count_followers}
👨 Пол: {sex}
🔒 Закрытый прoфиль: {is_closed}
💬 Статус: {info['status']}
⛔ Я в чс: {blacklisted}
⛔ Он в чс: {blacklisted_by_me}
📷 Фото: {vk.utils.getShortLink(url=info['photo_max_orig'])['short_url']} ''')

                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'Упоминание пользователя не найдено.')
                    if text==f'{prefix}+автовыход':
                        if auto_exit:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'Автовыход и так включён.')
                        else:
                            auto_exit=True
                            db['auto_exit']=True
                            save_db(db)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'✅ Автовыход включён.')
                    if text==f'{prefix}-автовыход':
                        if not auto_exit:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'Автовыход и так выключен.')
                        else:
                            auto_exit=False
                            db['auto_exit']=False
                            save_db(db)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'🚫 Автовыход выключен.')
                    if text.startswith(f'{prefix}прочитать'):
                        arg=re.findall(r'(все|всё|беседы|группы|личные)', text)
                        if len(arg)>0:
                            arg=arg[0]
                            if arg=='все' or arg=='всё':
                                arg=['user', 'chat', 'group']
                            elif arg=='беседы':
                                arg=['chat']
                            elif arg=='группы':
                                arg=['group']
                            elif arg=='личные':
                                arg=['user']
                            convers = vk.messages.getConversations(count=200, filter='unread')['items']
                            chats = private = groups = 0
                            to_read = []
                            code = 'API.messages.markAsRead({"peer_id": %s});'
                            to_execute = ''
                            for chat in convers:
                                type=chat['conversation']['peer']['type']
                                if type in arg:
                                    to_read.append(chat['conversation']['peer']['id'])
                                    if type == 'chat': chats += 1
                                    elif type == 'user': private += 1
                                    elif type == 'group': groups += 1       
                            while len(to_read) > 0:
                                for _ in range(25 if len(to_read) > 25 else len(to_read)):
                                    to_execute += code % to_read.pop()
                                vk.execute(code=to_execute)
                                time.sleep(0.1)

                                to_execute = ''
                            message = '✅ Диалоги прочитаны:'
                            if chats: message += f'\nБеседы: {chats}'
                            if private: message += f'\nЛичные: {private}'
                            if groups: message += f'\nГруппы: {groups}'
                            if message == '✅ Диалоги прочитаны:':
                                message = '🤔 Ты зачем моё время попросту тратишь? Делать нечего что ли? И так всё прочитанно.'
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=message)
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message=f'🤔 А что прочитать-то?')
                    if text.startswith(f'{prefix}выбери'):
                        choice=re.findall(r'выбери (.*)', text)
                        if len(choice)>0:
                            choice=choice[0]
                            resultat=random.choices(choice.split(' или '))
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = f'Я выбираю: {resultat[0]}')
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'Удивительно! Из ничего, я выбрал ничего.')
                    if text.startswith(f'{prefix}удалялка'):
                        _trigger_word_=re.findall(r'удалялка (.*)', text)
                        if len(_trigger_word_)>0:
                            trigger_word=_trigger_word_[0]
                            db['trigger_word']=trigger_word
                            save_db(db)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = f'Триггер слово изменено на: {trigger_word}')
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'А на что изменить-то?')
                    if text.startswith(f'{prefix}префикс'):
                        _prefix_=re.findall(r'префикс (.*)\.', text) 
                        if len(_prefix_)>0:
                            prefix=_prefix_[0]
                            db['prefix']=prefix
                            save_db(db)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = f'Префикс изменён на: {prefix}')
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'А на что изменить-то?')
                    if text.startswith(f'{prefix}дем'):
                        
                        message=vk.messages.getById(message_ids=message_id)['items'][0]
                        if 'reply_message' in message:
                            if 'attachments' in message['reply_message']:
                                if len(message['reply_message']['attachments'])==1 and message['reply_message']['attachments'][0]['type']=='photo':
                                        photo = message['reply_message']['attachments'][0]['photo']['sizes'][-1]['url']
                                        vk.messages.edit(message_id=message_id, peer_id=peer_id, attachment=demotivator(text, photo))
                                else:
                                    vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'В сообщении должно быть одно вложение типа "фотография".')
                            else:
                                vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'В сообщении должно быть одно вложение.')
                        else:
                            photo = vk.photos.getById(photos=event.raw[7]['attach1'])[0]['sizes'][-1]['url']
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, attachment=demotivator(text, photo))
                    if text.endswith('//'):
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message = '\n'.join(list(event.text)[:-2]))
                    if text.startswith(f'{prefix}ссылка'):
                        link=re.findall(r'ссылка (.*)', text)
                        vk.messages.edit(message_id=message_id, peer_id=peer_id, message = f'Вот ваша ссылка:\n{vk.utils.getShortLink(url=link)["short_url"]}')
                    if text.startswith(f'{prefix}транскрипция'):
                        message=vk.messages.getById(message_ids=message_id)['items'][0]
                        if 'reply_message' in message:
                            if len(message['reply_message']['attachments'])!=0:
                                if message['reply_message']['attachments'][0]['type']=='audio_message':
                                    transcript=message['reply_message']['attachments'][0]['audio_message']['transcript']
                                    owner_id=message['reply_message']['attachments'][0]['audio_message']['owner_id']
                                    info=vk.users.get(user_ids=str(owner_id), name_case='gen')[0]
                                    vk.messages.edit(message_id=message_id, peer_id=peer_id, message = f'✉Голосовое сообщение от {info["first_name"]} {info["last_name"]}\n💬Перевод от ВКонтакте:\n{transcript}')
                                else:
                                    vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'Это не голосовое сообщение.')
                            else:
                                vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'А где голосовое сообщение?')
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'Мне нужен ответ на голосове сообщение.')
                    if text.startswith(f'{prefix}симулировать'):
                        type=re.findall(r'симулировать (.)', text)
                        if len(type)>0:
                            if type[0]=='1':
                                type='typing'
                                simulation=True
                                Thread(target=set_activity, args=(type, peer_id)).start()
                            elif type[0]=='2':
                                type='audiomessage'
                                simulation=True
                                Thread(target=set_activity, args=(type, peer_id)).start()
                            elif type[0]=='3':
                                simulation=False
                            else:
                                type='typing'
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'Success')
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'А что сделать-то?')
                    if text.startswith(f'{prefix}гс'):
                        text_to_speech=re.findall(r'гс (.+)', text)
                        if len(text_to_speech)>0:
                            text_to_speech=text_to_speech[0]
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = '...Озвучиваю...')
                            tts = gTTS(text=text_to_speech, lang='ru', slow=False)
                            audion = 'raw\\audio.mp3'
                            tts.save(audion)
                            audio = upload.audio_message(audion)['audio_message']
                            attachment=f'audio_message{audio["owner_id"]}_{audio["id"]}'
                            vk.messages.delete(message_ids=str(message_id), delete_for_all=1)
                            vk.messages.send(peer_id=peer_id, attachment=attachment, random_id=random.randint(1, 10**9))
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = 'А что сказать-то?')
                    if text.startswith(f'{prefix}сооб'):
                        message=vk.messages.getById(message_ids=message_id)['items'][0]
                        if 'reply_message' in message:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = str(message['reply_message']))
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message = str(message))
                    if text.startswith(f"{prefix}+чс"):
                        id_ = get_id(event)[0]
                        
                        banned_list = vk.account.getBanned(count=200)["items"]
                        
                        if id_ not in banned_list:
                            vk.account.ban(owner_id=id_)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} добавлен в черный список".format(get_push(id_)))
                        
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} уже находится в черном списке".format(get_push(id_)))
                    
                    if text.startswith(f"{prefix}-чс"):
                        id_ = get_id(event)[0]
                        
                        banned_list = vk.account.getBanned(count=200)["items"]
                        
                        if id_ in banned_list:
                            vk.account.unban(owner_id=id_)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} удален из черного списка".format(get_push(id_)))
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} не находится в черном списке".format(get_push(id_)))
                    if text.startswith(f"{prefix}+др"):
                        id_ = get_id(event)[0]
                        friends_list = vk.friends.get(count=5000)["items"]
                        if id_ not in friends_list:
                            vk.friends.add(user_id=id_)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} добавлен в друзья".format(get_push(id_)))
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} и так находится в друзьях".format(get_push(id_)))
                    
                    if text.startswith(f"{prefix}-др"):
                        id_ = get_id(event)[0]
                        friends_list = vk.friends.get(count=5000)["items"]
                        if id_ in friends_list:
                            vk.friends.delete(user_id=id_)
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} удален из списка друзей".format(get_push(id_)))
                        else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="{} отсутствует в списке друзей".format(get_push(id_)))
                   
                    if text.startswith(f"{prefix}влс"):
                       id_ = get_id(event)[0]
                       if id_:
                            args = re.findall("влс (.+)", text_original)[0]
                            print(id_)
                            vk.messages.send(peer_id=id_, message=args, random_id=random.randint(1, 10**9))
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="Сообщение отправлено")
                       else:
                            vk.messages.edit(message_id=message_id, peer_id=peer_id, message="Ошибка!")

                    if text.startswith(f"{prefix}цит"):
                         
                         message=vk.messages.getById(message_ids=message_id)['items'][0]
                         
                         if 'reply_message' in message:

                            if 'attachments' in message['reply_message']:
                               
                              
                                    
                                    info=vk.users.get(user_ids=get_id(event=event), fields=
                                    [
                                        "first_name", 
                                        "last_name",  
                                        "photo_max_orig"
                                    ])[0]
                                    print(info)
                                    name = "{} {}".format(info["first_name"], info["last_name"])
                                    if len(text.split()) > 1:
                                        args = re.findall("цит (.+)", event.text)[0]
                                    else:
                                        message=vk.messages.getById(message_ids=message_id)['items'][0]
                                        print(message)
                                        args = message["reply_message"]["text"]
                                        print(args)
                                    print(args)
                                    quote = Quote(args, name)
                                    print(info['photo_max_orig'])
                                    filename = requests.get(info['photo_max_orig'])
                                    with open('raw\\ava.jpg','wb') as file:
                                        file.write(filename.content)
                                    quote.create('raw\\ava.jpg', result_filename="raw\\qresult.png")

                                    photo = upload_vk.photo_messages('raw\\qresult.png')
                                    owner_id = photo[0]['owner_id']
                                    photo_id = photo[0]['id']
                                    access_key = photo[0]['access_key']
                                    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
                                    vk.messages.edit(message_id=message_id, peer_id=peer_id, attachment=attachment)

            if event.type==VkEventType.CHAT_UPDATE and auto_exit:
                peer_id=event.peer_id
                if event.raw[3]==my_id and event.raw[1]==6:
                    time.sleep(1)
                    vk.messages.send(peer_id=peer_id, message='🚫|Автовыход из бесед включен, ливаю....', random_id=random.randint(1, 10**9))
                    time.sleep(1)
                    vk.messages.removeChatUser(chat_id=chat_id, user_id=my_id) 
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        os.execv(sys.executable, [sys.executable] + sys.argv)
        exit(0)
    except Exception as e:
        if str(e)=='[5] User authorization failed: invalid session.':
            print('\033[0;31mТокен инвалид\033[0m')
            break
        else:
            print('\033[0;31mОшибка:\033[0m')
            traceback.print_exc()
            time.sleep(5)


