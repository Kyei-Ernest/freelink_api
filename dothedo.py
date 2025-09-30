def persistence(n):
    mult = 1
    count = 0
    while n > 9:
        for i in str(n):
            mult *= int(i)
        n = mult
        mult = 1
        count += 1
    return count






a = persistence(999)
print(a)