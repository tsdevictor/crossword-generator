import sys; args = sys.argv[1:]
import random


global H, W, NUM_BLOCKING, words_by_len, BRD_SIZE
def parse_args():
    global H, W, NUM_BLOCKING, words_by_len, BRD_SIZE, args

    DICTIONARY = {}
    with open(args[0]) as dct:
        for line in dct:
            line = line.strip()
            if len(line) < 3: continue
            if len(line) not in DICTIONARY: DICTIONARY[len(line)] = []
            DICTIONARY[len(line)].append(line)

    args = args[1:]
    H, W, NUM_BLOCKING = int(args[0][:args[0].lower().index('x')]), int(args[0][args[0].lower().index('x') + 1:]), int(args[1])
    BRD_SIZE = H * W

    if NUM_BLOCKING == BRD_SIZE: return '#' * BRD_SIZE

    brd = ['-' for _ in range(BRD_SIZE)]
    for arg in args[2:]:
        lower = arg.lower()
        orientation, word = lower[0], '#'

        end = lower.index('x') + 1
        for char in lower[lower.index('x') + 1:]:
            if char in 'abcdefghijklmnopqrstuvwxyz#': break
            end += 1

        row = int(lower[1:lower.index('x')])
        col = int(lower[lower.index('x')+1: end])
        if lower[end:]: word = arg[end:]

        pos = row * W + col
        for char in word:
            brd[pos] = char
            if char == '#': brd[reflect(pos)] = '#'
            elif brd[reflect(pos)].lower() not in 'abcdefghijklmnopqrstuvwxyz#': brd[reflect(pos)] = '.'
            pos += 1 if orientation in 'Hh' else W

    if NUM_BLOCKING % 2: brd[BRD_SIZE // 2] = '#'

    return ''.join(brd)


global THREE_AWAY_NBRS
def generate_nbrs():
    global THREE_AWAY_NBRS
    NBRS_BY_DIRECTION = [[] for _ in range(BRD_SIZE)]
    row_diffs = {-W: 1, W: 1, -1: 0, 1: 0}
    col_diffs = {-W: 0, W: 0, -1: 1, 1: 1}
    for pos in range(BRD_SIZE):
        for drt in [W, -W, 1, -1]:
            nbrs, rd, cd = [], row_diffs[drt], col_diffs[drt]
            count = 0
            for dist in range(1, W):  # distance
                if count == 3: break
                nbr = pos + dist * drt
                if not 0 <= nbr < W*H \
                    or abs(nbr % W - pos % W) != dist * cd \
                    or abs(nbr // W - pos // W) != dist * rd: break
                nbrs.append(nbr)
                count += 1
            if nbrs: NBRS_BY_DIRECTION[pos].append(nbrs)


def reflect(pos): return BRD_SIZE - 1 - pos


def two_d_print(brd):
    print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]))


def connected(brd):
    seen = set()
    all_hash = {i for i in range(BRD_SIZE) if brd[i] == '#'}
    queue = [brd.find('-')]
    for idx in queue:
        if not 0 <= idx < BRD_SIZE: continue
        if idx in seen: continue
        if brd[idx] == '#': continue
        seen.add(idx)
        if (idx + 1) // W == idx // W: queue.append(idx + 1)
        if (idx - 1) // W == idx // W: queue.append(idx - 1)
        queue.append(idx + W)
        queue.append(idx - W)
    return len(seen | all_hash) == BRD_SIZE


# check that: all white spaces are connected, no words of length < 3
def is_valid(brd):
    brd = ''.join([char if char in '#-' else '-' for char in brd])
    for i, char in enumerate(brd):
        if char != '#': continue
        for drt in THREE_AWAY_NBRS[i]:
            adj_word = ''.join(brd[nbr] for nbr in drt)
            if '-#' in adj_word or adj_word in ('-', '--'): return False

    return True


def place(brd, pos, item):
    brd = [*brd]
    brd[pos] = item
    brd[reflect(pos)] = item if item == '#' else '.'

    if item != '#': return ''.join(brd)

    copy = [char if char in '#-' else '-' for char in brd]
    for i, char in enumerate(copy):
        if char != '#': continue
        for drt in THREE_AWAY_NBRS[i]:
            j = 0
            while '-#' in ''.join(copy[nbr] for nbr in drt) or ''.join(copy[nbr] for nbr in drt) in ('-', '--'):
                if brd[drt[j]] != '-': return ''
                copy[drt[j]], copy[reflect(drt[j])] = '#', '#'
                brd[drt[j]], brd[reflect(drt[j])] = '#', '#'
                j += 1

    return ''.join(brd)


def choices():
    lst = [i for i in range(BRD_SIZE)]
    random.shuffle(lst)
    return lst
    # return range(BRD_SIZE)


def brute_force(brd):
    if not connected(brd): return ''
    count = brd.count('#')
    if count > NUM_BLOCKING: return ''
    if count == NUM_BLOCKING: return brd.replace('.', '-') if is_valid(brd) else ''

    for i in choices():
        if brd[i] != '-': continue
        copy = place(brd, i, '#')
        if not copy: continue
        new_brd = brute_force(copy)
        if new_brd: return new_brd
        brd = place(brd, i, '.')

    return ''


def solve(brd):
    placed_words = set()
    filled = set()
    for i, char in enumerate(brd):
        if char == '#' or i in filled: continue
        word_len = min(brd.find('#', i) if NUM_BLOCKING and '#' in brd[i:] else BRD_SIZE, i // W * W + W) - i

        requirements = {}
        for j in range(i, i + word_len):
            filled.add(j)
            if brd[j] not in '-#': requirements[j - i] = brd[j]
        if len(requirements) == word_len: continue

        for word in words_by_len[word_len]:
            if word in placed_words: continue
            for k in requirements:
                if word[k].lower() != requirements[k].lower(): break
            else:
                placed_words.add(word)
                brd = brd[:i] + word + brd[i + len(word):]
                break
    return brd


def main():
    brd = parse_args().lower()
    generate_nbrs()
    brd = brute_force(brd)
    brd = solve(brd)
    # two_d_print(brd)
    print(brd)


if __name__ == '__main__': main()


# Tristan Devictor, pd. 6, 2024
