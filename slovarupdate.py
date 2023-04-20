import config
#
with open('wordfilter.txt', 'r') as f:
    config.mat = f.read().split(', ')
    for item in config.mat:
        item.lower()
    print(config.mat[100:110])
    print(len(config.mat))
    mat = ', '.join(sorted(list(set(config.mat))))
    print(mat[0:10])
    print(len(mat))
    f.close()
with open('wordfilter.txt', 'w') as f:
    f.write(mat)
    f.close()