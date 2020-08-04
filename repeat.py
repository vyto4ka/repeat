dostup = [365530525] #тут айди тех кто должен быть в доступе, нужен именно айди цифрами без @id 
muted_for_all = []
muted_for_me = []
import time
import random
import vk
import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType

def main():
    session = vk_api.VkApi(token="токен")
    longpoll = VkLongPoll(session)
    vk = session.get_api()
    for event in longpoll.listen():
        if event.type == VkEventType.CHAT_UPDATE: 
            if event.type_id == 1:
                msg='Изменилось название беседы'
            if event.type_id == 2:
                msg='Сменилась обложка беседы'
            if event.type_id == 3:
                msg='Назначен новый администратор'
            if event.type_id == 5:
                msg='Закреплено сообщение'
            if event.type_id == 6:
                msg='Пользователь присоединился к беседе'
            if event.type_id == 7:
                msg='Пользователь покинул беседу'
            if event.type_id == 8:
                message='Пользователя исключили из беседы'
            if event.type_id == 9:
                msg='С пользователя сняты права администратора'
        try:
            msg = event.text.lower()
            if event.from_chat:
            	from_id = event.user_id
            	if msg == "":
            		print(f"""БЕСЕДА: {from_id}: Отправил(а) стикер, видео или фото.""")
            		if from_id in muted_for_all:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=1)
            		if from_id in muted_for_me:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=0)
            	else:
            		print(f"""БЕСЕДА: {from_id}: {event.text}""")
            		if from_id in muted_for_all:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=1)
            		if from_id in muted_for_me:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=0)
            elif event.from_user:
            	x = vk.messages.getById(message_ids=event.message_id)["items"][0]
            	from_id = x["from_id"]
            	if msg == "":
            		print(f"""ЛС: {from_id}: Отправил(а) стикер, видео или фото.""")
            		if from_id in muted_for_all:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=1)
            		if from_id in muted_for_me:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=0)
            	else:
            		print(f"""ЛС: {from_id}: {event.text}""")
            		if from_id in muted_for_all:
            		    vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=1)
            		if from_id in muted_for_me:
            			vk.messages.delete(message_ids=f"""{event.message_id}""",delete_for_all=0)
        except:
        	msg = "gg"
        else:
            	if msg == "!у +мут":
            		if from_id in dostup:
            		    x = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]
            		    muted_for_all.append(x["from_id"])
            		    vk.messages.send(peer_id=event.peer_id, random_id=0, message=f"""✅Удаление сообщений [id{x["from_id"]}|пользователя] для всех установлено.""")
            	if msg == "!у -мут":
            		if from_id in dostup:
            			x = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]
            			muted_for_all.remove(x["from_id"])
            			vk.messages.send(peer_id=event.peer_id, random_id=0, message=f"""✅Удаление сообщений [id{x["from_id"]}|пользователя] для всех удалено.""")
            	if msg == "!у +игнор.":
            		if from_id in dostup:
            			x = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]
            			muted_for_me.append(x["from_id"])
            			vk.messages.send(peer_id=event.peer_id, random_id=0, message=f"""✅Удаление сообщений [id{x["from_id"]}|пользователя] для себя установлено.""")
            	if msg == "!у -игнор":
            		if from_id in dostup:
            			x = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]
            			muted_for_me.remove(x["from_id"])
            			vk.messages.send(peer_id=event.peer_id, random_id=0, message=f"""✅Удаление сообщений [id{x["from_id"]}|пользователя] для себя удалено.""")
            	if msg == "!у +доступ":
            		if from_id in dostup:
            			x = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]
            			dostup.append(x["from_id"])
            			vk.messages.send(peer_id=event.peer_id, random_id=0, message=f"""[id{x["from_id"]}|Пользователю] выдан доступ.""")
            	if msg == "!у -доступ":
            		if from_id in dostup:
            			x = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]
            			dostup.remove(x["from_id"])
            			vk.messages.send(peer_id=f"""[id{x[from_id]}|Пользователю убран доступ.""")
            	elif msg.startswith(".."): #тут текст, на который будет начинаться команда
            		if from_id in dostup:
            		    vk.messages.send(peer_id=event.peer_id, random_id=0, message=event.text[2:])
            	
while True:
	try: 
		main()
	except: 
		pass
