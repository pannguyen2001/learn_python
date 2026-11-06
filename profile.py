# from line_profiler import profile

# @profile
def add_int(num: list[int], k: int) -> list[int]:
    arr_value = 0
    for i in range(len(num) - 1, -1, -1):
        arr_value += num[len(num) - i - 1] * (10 ** i)
    arr_value += k
    return list(map(lambda x: int(x), list(str(arr_value))))

for i in range (10000):
    add_int([2,7,4], 181)

# @profile
# def main():
#     print('start calculating')
#     primes = add_int([2,7,4], 181)
#     print(f'done calculating. Found {len(primes)} primes.')

# if __name__ == '__main__':
#     main()

