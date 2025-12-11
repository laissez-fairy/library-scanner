import io, numpy
from re import search

import requests

import fuzzysearch
from alchemy import *
from telegram import Update, InlineQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, MessageHandler,
                          ApplicationBuilder, ContextTypes, CallbackContext,
                          filters, ConversationHandler, CallbackQueryHandler)


import cv2
import pyzbar.pyzbar

with open('tokenfile', 'r') as f:
    token = f.read()

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

MAX_QUERY_NUMBER = 5

NAME_VERIFY, NAME_CALLBACK = range(2)
ADDBOOK_BUILDING, ADDBOOK_SHELF, ADDBOOK_STOREY, ADDBOOK_FINAL = range(4)

user, code_to_add, temp_name, temp_title, temp_author, temp_shelf, temp_storey, temp_isbn = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        q = select(User).where(User.id == user_id)
        context.user_data[user] = session.execute(q).scalars().all()[0]
        return ConversationHandler.END
    except IndexError:
        await update.message.reply_text('Похоже, ты ещё не пользовался этим ботом. Как тебя назвать?')
        return NAME_VERIFY

async def name_verify(update: Update, context: CallbackContext):
    name = update.message.text
    user_id = update.effective_user.id
    username = update.message.text

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(u'Да, папочка \U0001F60D', callback_data=name)],
        [InlineKeyboardButton('Не-а', callback_data='0')]
    ])

    await update.message.reply_text(f'Сынок, ты точно хочешь называться {username}?', reply_markup=keyboard)
    return NAME_CALLBACK

async def name_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data != '0':
        username = query.data
        user = User(id=user_id, username=username)
        context.user_data[user] = user
        try:
            session.add(user)
            session.commit()
            await context.bot.send_message(user_id, 'Замечательно! Записали тебя.')
            await context.bot.send_message(user_id, 'Теперь можешь отправить фото ISBN-кода или название книжки, '
                                                            'которую ищешь, в кавычках ("").')
            await context.bot.send_message(user_id, '''Чтобы добавить книжку вручную, введи ```/add```''',
                                                            parse_mode='MarkdownV2')
            return ConversationHandler.END
        except:
            await context.bot.sendMessage(user_id, 'Пользователь с таким именем уже существует, выбери другое, пожалуйста')
            return NAME_CALLBACK
    else:
        await context.bot.sendMessage(user_id, 'Придумай что-нибудь получше!')
        return NAME_VERIFY

async def dbsearch(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    fuzzyquery = update.message.text[1:-1]
    q = session.query(Book).all()
    q = sorted([(i, fuzzysearch.ldist(fuzzyquery, i.title),
                 i.title, fuzzysearch.ldist(fuzzyquery, i.title)/len(i.title)) for i in q],
               key=lambda j: j[3])
    message = 'Вот что у нас есть (из самого подходящего):\n'
    if len(q) > MAX_QUERY_NUMBER:
        q = q[:MAX_QUERY_NUMBER]
    for i in range(len(q)):
        message += f'*{i + 1}\.* __{q[i][0].title}__ \({q[i][0].author.full_name}\)\n'
        'шкаф {q[i][0].location.shelf}, полка {q[i][0].location.storey}\n'
    print([[InlineKeyboardButton(f'{i + 1}', str(i))] for i in range(MAX_QUERY_NUMBER)])
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'{i + 1}', callback_data=str(i)) for i in range(MAX_QUERY_NUMBER)],
        [InlineKeyboardButton('Ладно, поищу лучше ручками', callback_data='cancel')]
    ])
    await update.message.reply_text(message, parse_mode='MarkdownV2', reply_markup=reply_markup)





    print(q)

async def addbook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('Book adding')


async def photo(update: Update, context: CallbackContext):
    file = await update.message.photo[-1].get_file()
    memory = io.BytesIO()
    memory.seek(0)
    await file.download_to_memory(memory)
    image = cv2.imdecode(numpy.array(bytearray(memory.getvalue()), dtype=numpy.uint8), cv2.IMREAD_COLOR)
    memory.close()
    cv2.imwrite('photo.jpg', image)
    codes = pyzbar.pyzbar.decode(image)
    try:
        code = str(codes[0].data)
        code = code[2:-1]
        context.user_data[code_to_add] = code
        await addbook(update, context)
        if await requestfromcode(int(code), update.effective_user.id, context):
            await update.message.reply_text('Мы можем добавить её в базу данных. '
                                            'Для начала напиши *номер шкафа*, в котором она хранится.', parse_mode='MarkdownV2')
            return ADDBOOK_SHELF

    except IndexError:
        await update.message.reply_text('К сожалению, мы не смогли распознать ISBN-код.\n'
                                        'Попробуй отправить другое фото!')
        return ConversationHandler.END

async def addbook_shelf(update: Update, context: CallbackContext):
    context.user_data[temp_shelf] = update.message.text
    await update.message.reply_text('Отлично! Теперь введи *номер полки*...', parse_mode='MarkdownV2')
    return ADDBOOK_STOREY

async def addbook_storey(update: Update, context: CallbackContext):
    context.user_data[temp_storey] = update.message.text
    await update.message.reply_text('Мы готовы добавить в библиотеку книгу '
                                    f'с названием *"{context.user_data[temp_title]}"* '
                                    f'на полку *{context.user_data[temp_storey]}* '
                                    f'в шкаф *{context.user_data[temp_shelf]}*!',
                                    parse_mode='MarkdownV2',
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton('Добавить!', callback_data='1')],
                                        [InlineKeyboardButton('Я стесняюсь...', callback_data='0')]
                                    ]
                                    ))
    return ADDBOOK_FINAL

async def addbook_final(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    print(query.data)
    if query.data == '0':
        await query.edit_message_text('Ну ладно, давай в другой раз!')
        return ConversationHandler.END


    location = Location(shelf=context.user_data[temp_shelf], storey=context.user_data[temp_storey])
    author = Author(full_name=context.user_data[temp_author])
    isbn = ISBN(isbn=context.user_data[temp_isbn])
    book = Book(isbn_rel=isbn, title=context.user_data[temp_title], location=location, author=author)

    try:
        session.add(book)
        session.commit()
        await query.edit_message_text('Добавилась!')
        return ConversationHandler.END
    except:
        await query.edit_message_text('Извини, что-то пошло не так. Попробуй ещё раз.')
        return ConversationHandler.END




async def requestfromcode(code: int, user_id, context: CallbackContext):
    try:
        r = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{code}').json()['items'][0]
        title = r['volumeInfo']['title']
        author = r['volumeInfo']['authors'][0]
        await context.bot.send_message(user_id, f'Мы нашли книгу "{title}"!')
        context.user_data[temp_title] = title
        context.user_data[temp_author] = author
        context.user_data[temp_isbn] = code
        return {'title': title, 'author': author}
    except (IndexError, KeyError) as e:
        print(e)
        await context.bot.send_message(user_id, f'{e}Мы не смогли найти эту книгу \uE401 '
                                                                        'Её нет там, где мы ищем.')
        return 0


app = ApplicationBuilder().token(token).build()

app.add_handler(ConversationHandler(entry_points=[CommandHandler('start', start)],
                                    states={
                                        NAME_CALLBACK: [CallbackQueryHandler(name_callback)],
                                        NAME_VERIFY: [MessageHandler(filters.TEXT, name_verify)]
                                    },
                                    fallbacks=[MessageHandler(filters.TEXT, photo)]))

app.add_handler(ConversationHandler(entry_points=[MessageHandler(filters.PHOTO, photo),
                                                  CommandHandler('add', addbook)],
                                   states={
                                       ADDBOOK_BUILDING: [CallbackQueryHandler(addbook)],
                                       ADDBOOK_SHELF: [MessageHandler(filters.TEXT, addbook_shelf)],
                                       ADDBOOK_STOREY: [MessageHandler(filters.TEXT, addbook_storey)],
                                       ADDBOOK_FINAL: [CallbackQueryHandler(addbook_final)]
                                   },
                                   fallbacks=[MessageHandler(filters.TEXT, photo)]))

app.add_handler(MessageHandler(filters=filters.Regex(r'[.]*'), callback=dbsearch))

app.run_polling()
