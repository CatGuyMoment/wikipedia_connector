def exp(base,exponent):
    if exponent == 0:
        return 1
    
    return exp(base,exponent-1) * base if base%2 else exp(base,exponent/2) **2

print(exp(5,3))