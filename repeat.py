import re
import time
import traceback

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

# --------------------------------------------------настрой_очка-------------------------------------------------- #
token = "токен" # токен VK
dostup = set([]) # ID тех кто должен быть в доступе, ID цифрами без @id, через запятую, внутри квадратных скобок
prefix = "!у" # сообщения, начинающиеся с этого префикса, будут расцениваться как команда
remote_prefix = ".." # префикс для "повторялки"
# ---------------------------------------------------------------------------------------------------------------- #

muted_for_all = set()
muted_for_me = set()


def sync_access():
    with open(__file__, 'r', encoding='utf-8') as script:
        data = script.read()
    data = re.sub(r'dostup = set\(\[.*\]\)',
                  f'dostup = set({list(dostup)})',
                  data)
    with open(__file__, 'w', encoding='utf-8') as script:
        script.write(data)


def main():
    session = vk_api.VkApi(token=token)
    longpoll = VkLongPoll(session)
    vk = session.get_api()
    my_id = vk.users.get()[0]['id']
    dostup.add(my_id)

    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW:
            continue

        def send(text: str):
            vk.messages.send(peer_id=event.peer_id, random_id=0, message=text)

        msg = event.text.lower()

        if event.from_chat:
            from_id = event.user_id
            if msg == "":
                print(f"БЕСЕДА: {from_id}: Отправил(а) стикер, видео или фото.")
            else:
                print(f"БЕСЕДА: {from_id}: {event.text}")
        elif event.from_user:
            from_id = my_id if event.from_me else event.peer_id
            if msg == "":
                print(f"ЛС: {from_id}: Отправил(а) стикер, видео или фото.")
            else:
                print(f"ЛС: {from_id}: {event.text}")

        if from_id in muted_for_all:
            vk.messages.delete(message_ids=event.message_id, delete_for_all=1)
        elif from_id in muted_for_me:
            vk.messages.delete(message_ids=event.message_id, delete_for_all=0)

        if from_id in dostup:
            if msg.startswith(prefix):
                msg = msg.replace(prefix, '', 1).strip()
                user = vk.messages.getById(message_ids=event.message_id)["items"][0]["reply_message"]["from_id"]
                if msg == "+мут":
                    muted_for_all.add(user)
                    send(f"✅Удаление сообщений [id{user}|пользователя] для всех установлено.")
                if msg == "-мут":
                    muted_for_all.remove(user)
                    send(f"✅Удаление сообщений [id{user}|пользователя] для всех отключено.")
                if msg == "+игнор":
                    muted_for_me.add(user)
                    send(f"✅Удаление сообщений [id{user}|пользователя] для себя установлено.")
                if msg == "-игнор":
                    muted_for_me.remove(user)
                    send(f"✅Удаление сообщений [id{user}|пользователя] для себя отключено.")
                if msg == "+доступ":
                    dostup.add(user)
                    sync_access()
                    send(f"[id{user}|Пользователю] выдан доступ.")
                if msg == "-доступ":
                    dostup.remove(user)
                    sync_access()
                    send(f"[id{user}|Пользователю убран доступ.")
            elif msg.startswith(remote_prefix) and from_id != my_id:
                send(event.text[2:])


while True:
    try:
        main()
    except Exception:
        print('Ошибка!\n', traceback.format_exc())
        time.sleep(10)
