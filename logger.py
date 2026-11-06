# import datetime
# from loguru import logger

# today = datetime.datetime.now().strftime("%Y-%m-%d")

# logger.add(
#     f"logs/{today}.json",
#     serialize=True,
#     rotation="10 MB",
#     retention="10 days",
#     level="DEBUG",
# )
# logger.add(f"logs/error_logs/{today}.log", level="ERROR")

import snoop
import sys
snoop.Config(color=True, out=sys.stdout, overwrite=True)

@snoop
def add_int(num: list[int], k: int) -> list[int]:
    arr_value = 0
    for i in range(len(num) -1 , 0, -1):
        arr_value += num[len(num) - 1 - i] * (10 ** i)
    arr_value += k
    return list(map(lambda x: int(x), list(str(arr_value))))
add_int([2,7,4], 181)
