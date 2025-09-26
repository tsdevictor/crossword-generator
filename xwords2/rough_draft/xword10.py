import sys; args = sys.argv[1:]
import random
import re
# args = ['dct20k.txt', '5x5', '4', 'v2x2I']
# args = ['dctEckel.txt', '15x15', '37', 'H0x4#', 'v4x0#', 'h9x11a']


def parse_args():
    global H, W, NUM_BLOCKING, WORDS_BY_LEN, BRD_SIZE, NBRS_BY_DIRECTION

    WORDS_BY_LEN = {i: [] for i in range(3, 31)}
    for line in open(args[0]):
        if not re.search('\d|^.?.?$', (word := line.rstrip())): WORDS_BY_LEN[len(word)].append(word)

    H, W = map(int, re.split('x', args[1], re.I))
    NUM_BLOCKING, BRD_SIZE = int(args[2]), H * W
    if NUM_BLOCKING == BRD_SIZE: return '#' * BRD_SIZE

    NBRS_BY_DIRECTION = [[] for _ in range(BRD_SIZE)]
    for i in range(BRD_SIZE):
        for drt in [W, -W, 1, -1]:
            nbrs = [n for d in range(1, 4) if 0 <= (n := i + d * drt) < BRD_SIZE and abs(n // W - i // W) == abs(drt) // W * d]
            if nbrs: NBRS_BY_DIRECTION[i].append(nbrs)

    brd = ['-' for _ in range(BRD_SIZE)]
    if NUM_BLOCKING % 2: brd[BRD_SIZE // 2] = '#'
    for arg in args[3:]:
        orientation, word = re.split('\d*x\d*', arg, re.I)
        row, col = map(int, re.findall('\d+', arg))
        pos = row * W + col
        for char in word: brd, pos = [*place(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

    return ''.join(brd)


def reflect(pos): return BRD_SIZE - 1 - pos


def two_d_print(brd): print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]))


def connected(brd):
    seen = set()
    queue = [brd.find('-')]
    for idx in queue:
        if not 0 <= idx < BRD_SIZE or idx in seen or brd[idx] == '#': continue
        seen.add(idx)
        if (idx + 1) // W == idx // W: queue.append(idx + 1)
        if (idx - 1) // W == idx // W: queue.append(idx - 1)
        queue.append(idx + W)
        queue.append(idx - W)
    return len(seen | {i for i in range(BRD_SIZE) if brd[i] == '#'}) == BRD_SIZE


def place(brd, pos, item):
    brd = [*brd]
    brd[pos] = item
    if brd[reflect(pos)] == '-': brd[reflect(pos)] = item if item == '#' else '.'

    if item != '#': return ''.join(brd)

    copy = [char if char in '#-' else '-' for char in brd]
    for i, char in enumerate(copy):
        if char != '#': continue
        for drt in NBRS_BY_DIRECTION[i]:
            for j in range(3):
                if not ('-#' in ''.join(copy[nbr] for nbr in drt) or ''.join(copy[nbr] for nbr in drt) in (
                        '-', '--')): break
                if brd[drt[j]] != '-': return ''
                copy[drt[j]], copy[reflect(drt[j])] = '#', '#'
                brd[drt[j]], brd[reflect(drt[j])] = '#', '#'
                if brd.count('#') > NUM_BLOCKING: return ''

    return ''.join(brd)


def choices():
    lst = [i for i in range(BRD_SIZE)]
    random.shuffle(lst)
    return lst


def brute_force(brd):
    if not connected(brd): return ''
    if brd.count('#') == NUM_BLOCKING: return brd.replace('.', '-')

    for i in choices():
        if brd[i] != '-': continue
        copy = place(brd, i, '#')
        if not copy: continue
        new_brd = brute_force(copy)
        if new_brd: return new_brd
        brd = place(brd, i, '.')

    return ''


def solve(brd):
    used_words = set()

    filled_pos = set()
    for i, char in enumerate(brd):
        if char == '#' or i in filled_pos: continue
        brd_hole = brd[i: BRD_SIZE - (W - i % W) + 1: W]
        word_len = brd_hole.find('#') if '#' in brd_hole else (BRD_SIZE - (W - i % W)) // W + 1

        requirements = {}
        for j in range(i, i + word_len * W, W):
            filled_pos.add(j)
            if brd[j] not in '-#': requirements[(j - i) // W] = brd[j]
        if len(requirements) == word_len: continue

        for word in WORDS_BY_LEN[word_len]:
            if word in used_words: continue
            for k in requirements:
                if word[k].lower() != requirements[k].lower(): break
            else:
                used_words.add(word)
                pos = i
                for c in word: brd, pos = brd[:pos] + c + brd[pos + 1:], pos + W
                break
        break

    filled_pos = set()
    for i, char in enumerate(brd):
        if char == '#' or i in filled_pos: continue
        word_len = min(brd.find('#', i) if NUM_BLOCKING and '#' in brd[i:] else BRD_SIZE, i // W * W + W) - i

        requirements = {}
        for j in range(i, i + word_len):
            filled_pos.add(j)
            if brd[j] not in '-#': requirements[j - i] = brd[j]
        if len(requirements) == word_len: continue

        for word in WORDS_BY_LEN[word_len]:
            if word in used_words: continue
            for k in requirements:
                if word[k].lower() != requirements[k].lower(): break
            else:
                used_words.add(word)
                brd = brd[:i] + word + brd[i + word_len:]
                break

    return brd


def main():
    brd = parse_args().lower()
    brd = brute_force(brd)
    brd = solve(brd)
    # two_d_print(brd)
    print(brd)


if __name__ == '__main__': main()

# Tristan Devictor, pd. 6, 2024
