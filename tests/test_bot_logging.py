from src.bot.core import MyBot


def test_bot_uses_default_log_interval():
    bot = MyBot()

    assert bot.log_interval == 22


def test_bot_accepts_custom_log_interval():
    bot = MyBot(log_interval=44)

    assert bot.log_interval == 44
