import sys; args = sys.argv[1:]
# args = ['9x9', '12', 'V0x1Shy']

global H, W, NUM_BLOCKING, words_by_len
def parse_args():
    global H, W, NUM_BLOCKING, words_by_len, args

    H, W, NUM_BLOCKING = int(args[0][:args[0].lower().index('x')]), int(args[0][args[0].lower().index('x') + 1:]), int(args[1])

    brd = '-' * H * W
    for arg in args[2:]:
        if '.txt' in arg: continue

        lower = arg.lower()
        orientation, word = lower[0], '#'

        end = lower.index('x') + 1
        for char in lower[lower.index('x') + 1:]:
            if char in 'abcdefghijklmnopqrstuvwxyz#': break
            end += 1

        row = int(lower[1:lower.index('x')])
        col = int(lower[lower.index('x')+1: end])
        if lower[end:]: word = arg[end:]

        brd = [*brd]
        pos = row * W + col
        for char in word:
            brd[pos] = char
            if char == '#': brd[reflect(pos)] = '#'
            elif brd[reflect(pos)].lower() not in 'abcdefghijklmnopqrstuvwxyz#': brd[reflect(pos)] = '.'
            pos += 1 if orientation in 'Hh' else W

        if NUM_BLOCKING % 2: brd[H*W//2] = '#'

    return ''.join(brd)


def reflect(pos): return H*W-1-pos


def two_d_print(brd):
    print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]))


def word_length_3(word):
    return '-' not in word or '---' in word


# check that: all white spaces are connected, no words of length < 3
def is_valid(brd):
    brd = ''.join([char if char in '#-' else '-' for char in brd])

    # no words of length < 3
    for i, char in enumerate(brd):
        if char != '#': continue
        if not word_length_3(brd[i:-1:-W]): return False  # above
        if not word_length_3(brd[i:H * W:W]): return False  # below
        if not word_length_3(brd[i:i // W * W - 1:-1]): return False   # left
        if not word_length_3(brd[i:(i // W + 1) * W:1]): return False  # right

    return True


def place(brd, pos, item):
    brd = brd[:pos] + item + brd[pos + 1:]
    pos = reflect(pos)
    brd = brd[:pos] + (item if item == '#' else '.') + brd[pos + 1:]

    return brd


def brute_force(brd, pos):
    if brd.replace('.', '-').count('#') == NUM_BLOCKING:
        return brd.replace('.', '-') if is_valid(brd) else ''
    # else: print(brd, brd.count('#'), NUM_BLOCKING)

    for i in range(pos, len(brd)):
        if brd[i] != '-' or brd[reflect(i)] != '-': continue
        new_brd = brute_force(place(brd, i, '#'), i + 1)
        if new_brd: return new_brd
        place(brd, i, '.')

    return ''


def prelim_fill(brd):
    brd = [*brd]

    for i, char in enumerate(brd):
        if char == '#':
            if i % W < 3 and not word_length_3(brd[i:i // W * W - 1:-1]):
                for j in range(i, -1, -W): brd[j] = '#'
            if i % W > W - 3 and not word_length_3(brd[i:(i // W + 1) * W:1]):
                for j in range(i, (i//W+1)*W, 1): brd[j] = '#'
            if i // W < 3 and word_length_3(brd[i:-1:-W]):
                for j in range(i, -1, -W): brd[j] = '#'
            if i // W > H - 3 and word_length_3(brd[i:H * W:W]):
                for j in range(i, H*W, W): brd[j] = '#'

    return ''.join(brd)


def main():
    brd = parse_args()
    # two_d_print(brd)
    # brd = prelim_fill(brd)
    brd = brute_force(brd, 0)
    print(brd)


if __name__ == '__main__': main()


# Tristan Devictor, pd. 6, 2024
