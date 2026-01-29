class MyIteration:
    def __init__(self, N):
        self.e = N
    
    def __iter__(self):
        self.s = 1
        return self
    
    def __next__(self):
        if self.s <= self.e:
            x = self.s
            self.s = x + 1
            return x
        else:
            raise StopIteration

# Test code
N = int(input())
it = MyIteration(N)
myiter = iter(it)

for i in myiter:
    print(i, end=' ')
