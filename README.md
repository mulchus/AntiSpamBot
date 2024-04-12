# AntiSpamBot
https://t.me/mulchbot 
@mulchbot

Это телеграм бот для администрирования мата. криптоманов и рекламщиков в чатах 


## Переменные окружения

Часть настроек проекта берётся из переменных окружения.  
Чтобы их определить, создайте файл `.env` в корне проекта и запишите туда данные в таком формате: `ПЕРЕМЕННАЯ = значение`:  
- `BOT_TOKEN = 'токен Вашего бота от Telegram'`. [Инструкция, как создать бота.](https://core.telegram.org/bots/features#botfather)   


## Установка и запуск
Для запуска у вас уже должен быть установлен Python не ниже 3-й версии.  

- Скачайте код
- Создайте файл с переменными окружения.
- Установите зависимости командой `pip install -r requirements.txt`
- Запустите бота - командой `python antispambot.py`
- Добавьте бота в чат и сделайте его администратором с правами чтения сообщений, удаления юзеров.


## Администрирование
Новый юзер чата- вновь вошедший пользователь, в течении первых суток  

Бот имеет следуюшее меню и команды:

### Команды
 `/start` - запуск/перезапуск бота. Необзодима для апдейта конфига под соответствующий новый чат.  
 `/menu` - вывод меню  
 `/analysis текст` - анализ пересылаемого сообщения для ручного отбора основных слов как криптоматийных  
 `/addword <bad or finance> слово` - добавить слово в соответствующую базу плохих или финансовых слов  
 `/delword <bad or finance> слово` - удалить слово из соответствующей базы плохих или финансовых слов  
 `/show admins` - вывести список админов чата  
 `/pause число` (в секундах) - изменить паузу отображения сообщений  

### Меню  
`Запрещенные сообщения` - типы сообщений, которые запрещены новым юзерам.  
`Плохие слова` - добавить или удалить плохое слово из базы плохих слов.  
`Финансовые слова` - добавить или удалить криптоматийное слово из базы финансовых слов.  
`Анализ текста` - удаление из пересылаемого сообщения знаков препинания, предлогов и т.п. и построение списка оставшихся 
слов для ручного отбора как криптоматийных.  
`Помощь` - вывод описания команд.


## Особенности работы  
Бот спроектирован с едиными словарями, расположенными в корне проекта. Т.о. его обучение происходит всеми 
пользователями бота - администраторами чатов одновременно.  
Ошибки работы бота логгируются в файл logs.txt в корне проекта  


## Цели проекта

Создание надежного обучаемого бота для препятствия мату, криптоматике и рекламе в чатах.


## #TODO
1. Дополнить проверку сообщений на гиперссылки для добавления такого типа нежелательного сообщения.  
2. Есть риск удаления множества полезных слов недобросовестным пользователем бота, что требует соответствующей 
доработки бота.  