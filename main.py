import io, numpy
import datetime
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
(BOOK_ACTIONS, BOOK_CHANGE_TITLE, BOOK_CHANGE_AUTHOR, BOOK_CHANGE_LOCATION,
 BOOK_CHANGE_SHELF, BOOK_CHANGE_STOREY,
 BOOK_DELETE, BOOK_MODIFY, BOOK_CHECKOUT, BOOK_RETURN) = range(10)

(user, code_to_add,
 temp_name, temp_title, temp_author, temp_shelf, temp_storey,
 temp_isbn, temp_search_results, temp_book) = range(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        q = select(User).where(User.id == user_id)
        context.user_data[user] = session.execute(q).scalars().all()[0]
        username = context.user_data[user].username
        await update.message.reply_text(f'Привет, {username}! '
                                        f'Отправь фото ISBN-кода, '
                                        f'пропиши /add '
                                        f'или просто напиши, что хочешь найти!')
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
        user = User(id=user_id, username=username, created_at=datetime.datetime.now())
        context.user_data[user] = user
        try:
            session.add(user)
            session.commit()
            await context.bot.send_message(user_id, 'Замечательно! Записали тебя.')
            await context.bot.send_message(user_id, 'Теперь можешь отправить фото ISBN-кода или название книжки, '
                                                            'которую ищешь')
            await context.bot.send_message(user_id, '''Чтобы добавить книжку вручную, введи ```/add```''',
                                                            parse_mode='MarkdownV2')
            return ConversationHandler.END
        except:
            await context.bot.sendMessage(user_id, 'Пользователь с таким именем уже существует,'
                                                   'выбери другое, пожалуйста')
            return NAME_CALLBACK
    else:
        await context.bot.sendMessage(user_id, 'Придумай что-нибудь получше!')
        return NAME_VERIFY

async def dbsearch(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    fuzzyquery = update.message.text
    print(fuzzyquery)
    print(fuzzysearch.ldist(fuzzyquery, 'gyro'))
    q = session.query(Book).all()
    q = sorted([(i, fuzzysearch.ldist(fuzzyquery, i.title),
                 len(i.title), fuzzysearch.ldist(fuzzyquery, i.title)/len(i.title)) for i in q],
               key=lambda j: j[3])

    print(q)
    message = 'Вот что у нас есть (из самого подходящего):\n'
    if len(q) > MAX_QUERY_NUMBER:
        q = q[:MAX_QUERY_NUMBER]
    for i in range(len(q)):
        message += (f'*{i + 1}.* __{q[i][0].title}__ ({q[i][0].author.full_name})\n'
        f'шкаф {q[i][0].location.shelf}, полка {q[i][0].location.storey}\n')
        if q[i][0].status:
            holder = session.query(User).filter(User.id == q[i][0].status).first()
            message += f'сейчас книга на руках у пользователя {holder.username}\n'
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f'{i + 1}', callback_data=str(i)) for i in range(MAX_QUERY_NUMBER)],
        [InlineKeyboardButton('Ладно, поищу лучше ручками', callback_data='cancel')]
    ])
    message = message.replace('(', '\(').replace(')', '\)').replace('-','\-')
    message = message.replace('.', '\.').replace(',', '\,').replace('!','\!')
    await update.message.reply_text(message,
                                    reply_markup=reply_markup, parse_mode='MarkdownV2')
    context.user_data[temp_search_results] = q
    return BOOK_ACTIONS

async def book_actions(update: Update, context: CallbackContext):
    search_results = context.user_data[temp_search_results]
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel':
        await query.edit_message_text('Ну ладно')
        return ConversationHandler.END

    index = update.callback_query.data
    book = search_results[int(index)][0]
    holder = session.query(User).filter(User.id == book.status).first()
    reply_markup = [

        [InlineKeyboardButton('Изменить название', callback_data=BOOK_CHANGE_TITLE)],
        [InlineKeyboardButton('Изменить автора', callback_data=BOOK_CHANGE_AUTHOR)],
        [InlineKeyboardButton('Изменить шкаф и полку', callback_data=BOOK_CHANGE_LOCATION)],
        [InlineKeyboardButton('Удалить', callback_data=BOOK_DELETE)]
    ]
    if not(book.status):
        reply_markup.append([InlineKeyboardButton('Взять', callback_data=BOOK_CHECKOUT)])
    if holder.id == update.effective_user.id:
        reply_markup.append([InlineKeyboardButton('Вернуть', callback_data=BOOK_RETURN)])
    reply_markup = InlineKeyboardMarkup(reply_markup)

    context.user_data[temp_book] = book
    await query.edit_message_text(f'{book.title}', reply_markup=reply_markup)
    return BOOK_MODIFY

async def book_modify(update: Update, context: CallbackContext):
    book = context.user_data[temp_book]
    holder = session.query(User).filter(User.id == book.status).first()
    user = update.effective_user
    query = update.callback_query
    await query.answer()
    callback_data = int(query.data)

    if callback_data == BOOK_RETURN:
        if holder != user:
            await query.edit_message_text(f'Так это и не ты брал! Это брал {holder.username}!')
        try:
            book.status = ''
            session.commit()
            await query.edit_message_text(f'Вернули книгу обратно в библиотеку!')
        except:
            await query.edit_message_text(f'Что-то пошло не так. '
                                          f'Воспользуйся этой возможностью, чтобы изучить'
                                          f'книгу поподробнее, может быть?')

    if callback_data == BOOK_DELETE:
        await query.edit_message_text(f'Ты уверен, что устал от {book.title}?\n'
                                      f'(Шкаф {book.location.shelf}, полка {book.location.storey})',
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton('Да, сжечь её!', callback_data='1'),
                                          InlineKeyboardButton('Нет, я жестоко ошибался...', callback_data='0')]
                                      ]))
        return BOOK_DELETE

    if callback_data == BOOK_CHANGE_TITLE:
        await query.edit_message_text(f'Напиши новое название! (Раньше: {book.title})')
        return BOOK_CHANGE_TITLE

    if callback_data == BOOK_CHANGE_AUTHOR:
        await query.edit_message_text(f'Напиши новое имя автора! (Прежнее: {book.author.full_name})')
        return BOOK_CHANGE_AUTHOR

    if callback_data == BOOK_CHANGE_LOCATION:
        await query.edit_message_text(f'Хорошо! Куда ты хочешь переставить книгу {book.title}? '
                                      f'(Раньше она стояла в шкафу {book.location.shelf} '
                                      f'на полке {book.location.storey})\n'
                                      f'Сначала укажи шкаф')
        return BOOK_CHANGE_SHELF

    if callback_data == BOOK_CHECKOUT:
        if book.status:
            await query.edit_message_text(f'Нам жаль, но книга уже записана на пользователя {holder.username}...')
            return ConversationHandler.END
        try:
            book.status = f'{user.id}'
            session.commit()
            await query.edit_message_text(f'Мы записали книгу ({book.title}) на тебя\n({username})!')
            return ConversationHandler.END
        except Exception as e:
            print(e)
            await query.edit_message_text(f'Что-то пошло не так, ты сегодня без книжки...')

    return ConversationHandler.END

async def book_delete(update: Update, context: CallbackContext):
    book = context.user_data[temp_book]
    query = update.callback_query
    await query.answer()
    if query.data == '0':
        await query.edit_message_text('Чудесно!')
        return ConversationHandler.END
    if query.data == '1':
        try:
            session.delete(book)
            session.commit()
            await query.edit_message_text('This book is no more. It has ceased to be. '
                                          'It has expired. Gone to meet its maker.')
            return ConversationHandler.END
        except:
            await query.edit_message_text('Что-то пошло не так! Книга спасена счастливой случайностью')
            return ConversationHandler.END
    return ConversationHandler.END

async def mybooks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = session.query(Book).filter(Book.status == context.user_data[user].id).all()
        print(q)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=''.join([i.title + '\n' for i in q]))
    except (IndexError, KeyError):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='На тебя ничего '
                                                                              'не записано (свободный '
                                                                              'человек)!')

    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Не знаем, почему, '
                                                                          'но что на тебя записано, '
                                                                          'найти не можем...')


async def addbook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('Book adding')


async def photo(update: Update, context: CallbackContext):
    """Get a code by photo.

    Indirectly returns ISBN code from photo setting context.user_data[code].

    Args:
        update(Update): telegram.Update. Contains the message with the photo.
        context(CallbackContext): telegram.CallbackContext.

    Returns:
        int: either ConversationHandler.END or ADDBOOK_SHELF to propel the state machine.
        dict: As a side effect.
    """

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
            await update.message.reply_text('Мы можем добавить её в базу данных\. '
                                            'Для начала напиши *номер шкафа*, в котором она хранится\.',
                                            parse_mode='MarkdownV2')
            return ADDBOOK_SHELF

    except IndexError:
        await update.message.reply_text('К сожалению, мы не смогли распознать ISBN-код.\n'
                                        'Попробуй отправить другое фото!')
        return ConversationHandler.END

async def addbook_shelf(update: Update, context: CallbackContext):
    context.user_data[temp_shelf] = update.message.text
    await update.message.reply_text('Отлично\! Теперь введи *номер полки*\.\.\.', parse_mode='MarkdownV2')
    return ADDBOOK_STOREY

async def addbook_storey(update: Update, context: CallbackContext):
    context.user_data[temp_storey] = update.message.text
    await update.message.reply_text('Мы готовы добавить в библиотеку книгу '
                                    f'с названием *"{context.user_data[temp_title]}"* '
                                    f'на полку *{context.user_data[temp_storey]}* '
                                    f'в шкаф *{context.user_data[temp_shelf]}*\!',
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
    book = Book(isbn_rel=isbn, title=context.user_data[temp_title], location=location, author=author,
                created_at=datetime.datetime.now())

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
        await context.bot.send_message(user_id, f'Мы нашли книгу *"{title}"*\!', parse_mode='MarkdownV2')
        context.user_data[temp_title] = title
        context.user_data[temp_author] = author
        context.user_data[temp_isbn] = code
        return {'title': title, 'author': author}
    except (IndexError, KeyError) as e:
        print(e)
        await context.bot.send_message(user_id, f'{e}Мы не смогли найти эту книгу \uE401 '
                                                                        'Её нет там, где мы ищем.')
        return 0

async def fallback():
    pass

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler('mybooks', mybooks))

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

app.add_handler(ConversationHandler(entry_points=[MessageHandler(filters=filters.TEXT, callback=dbsearch)],
                                    states={
                                        BOOK_ACTIONS: [CallbackQueryHandler(book_actions)],
                                        BOOK_MODIFY: [CallbackQueryHandler(book_modify)],
                                        BOOK_DELETE: [CallbackQueryHandler(book_delete)]
                                    },
                                    fallbacks=[MessageHandler(filters=filters.TEXT, callback=dbsearch)]))

if __name__ == '__main__':
    app.run_polling()
