import time


start = time.time()

for line in open('../../dctEckel.txt'):
    x = line
    for k in line:
        x = k


print(time.time()-start)




# 1. massage the dictionary -> rate each word by how often it contains the letter that appears the most throughout the dictionary
# 2. create the set of choices for each block that is the start of a word
# 3.