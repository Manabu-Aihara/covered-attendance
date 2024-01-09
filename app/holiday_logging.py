import logging
from datetime import datetime


def get_logger(name: str, level: str):
    # getLoggerにモジュール名を与える
    logger = logging.getLogger(name)

    # これを設定しておかないと後のsetLevelでDEBUG以下を指定しても効かないっぽい
    level: int = getattr(logging, level)
    logger.setLevel(level)

    # 出力先を指定している
    date_now = datetime.now()
    logfile = f"holiday{date_now.strftime('%Y%m%d')}.log"
    handler = logging.FileHandler(logfile)

    # そのハンドラの対象のレベルを設定する
    handler.setLevel(level)

    # どんなフォーマットにするかを指定する。公式に使える変数は書いてますね。
    formatter = logging.Formatter("%(levelname)s  %(asctime)s  %(message)s")
    handler.setFormatter(formatter)

    # 設定したハンドラをloggerに適用している
    logger.addHandler(handler)

    return logger
