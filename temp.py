n = int(input("Enter fibbonaci number: "))
a = 0
b = 1
print(a)
print(b)
for i in range(n-2):
    c = a+b
    print(c)
    a = b
    b = c
nested_var = {
    "x": 10,
    "name": "Alex",
    "numbers": [1, 2, 3],
    "nested": {
        "a": 1,
        "b": [10, 20, {"deep": 99}]
    }
}