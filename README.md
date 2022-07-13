# homework_bot
### Описание проекта

Проект 'homework_bot' представляет собой Telegram-бота, который узнает статус домашней работы: 
взята ли в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

Раз в 10 минут бот опрашивает API сервиса Практикум.Домашка, при обновлении статуса анализирует ответ API
и отправляет соответствующее уведомление в Telegram;
Также бот логирует свою работу и сообщает о важных проблемах сообщением в Telegram.
Принцип создания интерфейса - REST, переход к API осуществлен на основе Django REST Framework.

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Amica24/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

### Примеры запросов к API:

У API Практикум.Домашка есть лишь один эндпоинт:
https://practicum.yandex.ru/api/user_api/homework_statuses/ и доступ к нему
возможен только по токену.
Получить токен можно по адресу: https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a

API Практикум.Домашка возвращает ответы в формате JSON. В ответе
содержатся два ключа:
homeworks : значение этого ключа — список домашних работ;
current_date : значение этого ключа — время отправки ответа.
Ответ API содержит актуальный статус каждой домашней работы. В список
попадают работы, которым был присвоен статус за период от from_date до
настоящего момента. Следовательно, с помощью метки времени можно управлять
содержанием этого списка:
* при from_date = 0 в этот список попадут все ваши домашние работы;
* при from_date , равном «минуту назад», велик шанс получить пустой список
homeworks ;
* при других значениях этого параметра в списке будет ограниченный перечень
домашних работ

Пример запроса:

Cоздайте файл api_praktikum.py и добавьте в него следующий код:
```
# homework_api/api_praktikum.py
import requests
url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': f'OAuth {<ваш токен>}'}
payload = {'from_date': <временная метка в формате Unix time>}.
# Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами params
homework_statuses = requests.get(url, headers=headers, params=payload)
# Печатаем ответ API в формате JSON
print(homework_statuses.text)
# А можно ответ в формате JSON привести к типам данных Python и напечатать и его
# print(homework_statuses.json())
```

Пример ответа при удачном выполнении запроса:

При запросе с параметром from_date = 0 API вернёт список домашек за всё время:
```
{
  "homeworks":[
    {
      "id":124,
      "status":"rejected",
      "homework_name":"username__hw_python_oop.zip",
      "reviewer_comment":"Код не по PEP8, нужно исправить",
      "date_updated":"2020-02-13T16:42:47Z",
      "lesson_name":"Итоговый проект"
    },
  {
    "id":123,
    "status":"approved",
    "homework_name":"username__hw_test.zip",
    "reviewer_comment":"Всё нравится",
    "date_updated":"2020-02-11T14:40:57Z",
    "lesson_name":"Тестовый проект"
  },
  ...
  ],
  "current_date":1581604970
}
```


