import telegram
from telegram.ext import Updater, MessageHandler, filters
import openai
import psycopg2
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

openai.api_key = os.environ.get("OPENAI_API_KEY")

DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL, sslmode='require')


def store_message(message, response):
    """ Define a function to store the message and response in the database"""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO conversation (message, response) VALUES (%s, %s)",
            (message, response)
        )
    conn.commit()


def get_last_message():
    """ Define a function to retrieve the most recent message
     from the database"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT message FROM conversation ORDER BY id DESC LIMIT 1"
        )
        last_message = cur.fetchone()
    if last_message is None:
        return ""
    else:
        return last_message[0]


def message_handler(update, context):
    """ Define a function to handle incoming messages"""
    # Get the message text from the update object
    message = update.message.text

    if message == "/start":
        # Clear the conversation history for the current user
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM conversation WHERE user_id = %s",
                (update.message.from_user.id,)
            )
        conn.commit()
        update.message.reply_text(
            "New conversation started! Say something to get started."
        )
        return

    elif message == "/delete_history":
        # Delete all messages in the database from this user
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM conversation WHERE user_id = %s",
                (update.message.from_user.id,)
            )
        conn.commit()
        update.message.reply_text(
            "Your conversation history has been deleted."
        )
        return

    # Get the previous message from the database
    last_message = get_last_message()

    # Use OpenAI's GPT to generate a response
    prompt = f"{last_message}\nUser: {message}\nBot:"
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Store the message and response in the database
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO conversation (user_id, message, response) VALUES (%s, %s, %s)",
            (update.message.from_user.id, message, response.choices[0].text)
        )
    conn.commit()

    # Log the incoming message and generated response
    logging.info(f"User {update.message.from_user.name} sent: {message}")
    logging.info(f"Bot replied with: {response.choices[0].text}")

    # Send the response back to the user
    update.message.reply_text(response.choices[0].text)


def test_message_handler():
    """ Define a test function for the message handler"""
    class FakeUpdate:
        """ Create a fake Telegram update object with a message"""
        def __init__(self, text, name):
            self.message = telegram.Message(
                message_id=1,
                date=None,
                chat=None,
                text=text,
                from_user=telegram.User(id=1, first_name=name, is_bot=False)
            )
    message = "Hello, how are you?"
    name = "John"
    fake_update = FakeUpdate(message, name)
    message_handler(fake_update, None)

    # Check that a response was generated
    assert len(fake_update.message.reply_text) > 0


bot = telegram.Bot(token='TELEGRAM_BOT_TOKEN')
updater = Updater(token='TELEGRAM_BOT_TOKEN', use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
)


def test_bot():
    """ Define a test function for the bot"""
    message = "Hello, how are you?"
    name = "John"
    response = bot.send_message(
        chat_id='YOUR_TELEGRAM_CHAT_ID',
        text=message,
        from_user=name
    )
    assert len(response.text) > 0


def test_api():
    """ Define a function to test the OpenAI API connection"""
    try:
        response = openai.Completion.create(
            engine="davinci-codex",
            prompt="test",
            max_tokens=1,
            n=1,
            stop=None,
            temperature=0.5,
        )
        assert response.choices[0].text != ""
        logging.info("OpenAI API connection test passed!")
    except Exception as e:
        logging.error(f"OpenAI API connection test failed with error: {e}")


updater.start_polling()
logging.info("Bot started!")

# Run the tests
test_message_handler()
test_bot()
test_api()
