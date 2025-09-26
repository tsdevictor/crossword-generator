import sys; args = sys.argv[1:]
import random
import re
args = ['dct20k.txt', '3x3', '0']  #, 'v2x2I']
# args = ['dctEckel.txt', '15x15', '37', 'H0x4#', 'v4x0#', 'h9x11a']


def parse_args():
    global H, W, NUM_BLOCKING, WORDS_BY_LEN, BRD_SIZE, NBRS_BY_DIRECTION, EXISTING_COMBINATIONS, ALL_WORDS
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    ALL_WORDS = set()
    WORDS_BY_LEN = {i: [] for i in range(3, 31)}
    dict_string = ''
    value = {char: 0 for char in alphabet}
    for line in open(args[0]):
        if not re.search('\d|^.?.?$', (word := line.rstrip())):
            WORDS_BY_LEN[len(word)].append(word)
            for char in word: value[char] += 1
            dict_string += word + ' '
            ALL_WORDS.add(word)
    WORDS_BY_LEN = {i: sorted(WORDS_BY_LEN[i], key=(lambda w: -sum(w.count(c) * value[c] for c in alphabet))) for i in WORDS_BY_LEN}
    EXISTING_COMBINATIONS = {c1 + c2 for c1 in alphabet for c2 in alphabet if c1 + c2 in dict_string}
    # print(EXISTING_COMBINATIONS, '\n', len(EXISTING_COMBINATIONS))
    # print(WORDS_BY_LEN)
    # sys.exit()

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
        for char in word: brd, pos = [*place_block(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

    return ''.join(brd)


def reflect(pos): return BRD_SIZE - 1 - pos


def two_d_print(brd): print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]) + '\n')


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


def place_block(brd, pos, item):
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


def block_choices():
    lst = [i for i in range(BRD_SIZE)]
    # random.shuffle(lst)
    return lst


def xword1(brd):
    if not connected(brd): return ''
    if brd.count('#') == NUM_BLOCKING: return brd.replace('.', '-')

    for i in block_choices():
        if brd[i] != '-': continue
        copy = place_block(brd, i, '#')
        if not copy: continue
        new_brd = xword1(copy)
        if new_brd: return new_brd
        brd = place_block(brd, i, '.')

    return ''


def xword2(brd):
    word_start = []
    for i, char in enumerate(brd):
        if char == '#': continue
        if i % W == 0 or (0 <= i - 1 and (i - 1) // W == i // W and brd[i - 1] == '#'):
            word_start.append((i, min(brd.find('#', i) if '#' in brd[i:] else BRD_SIZE, (i // W) * W + W), 1))
        if i // W == 0 or (0 <= i - W and brd[i - W] == '#'):
            brd_hole = brd[i: BRD_SIZE + 1: W]
            if '#' not in brd_hole: word_start.append((i, BRD_SIZE - (W - i % W) + 1, W))
            else: word_start.append((i, (brd_hole.find('#')-1) * W + i % W + 1, W))
    word_start = sorted(word_start, key=lambda w: len(word := brd[w[0]: w[1]: w[2]]) + word.count('-'))
    # print(word_start)
    # sys.exit()
    used_words = set()
    return fill_words(brd, word_start, used_words)


def place_word(brd, word, pos, orientation):
    for char in word:
        brd, pos = brd[:pos] + char + brd[pos + 1:], pos + orientation
    return brd


def is_valid(brd, word_start):
    for start, end, orientation in word_start:
        if brd[start: end: orientation] not in ALL_WORDS: return False
    return True


def get_word(spec, used_words):
    if '-' not in spec: return ''
    for word in WORDS_BY_LEN[len(spec)]:
        if word in used_words: continue
        if all([c == '-' or word[i] == c for i, c in enumerate(spec)]):
            return word


def fill_words(brd, word_start, used_words):
    if '-' not in brd:
        return brd if is_valid(brd, word_start) else ''

    for start, end, orientation in word_start:
        spec = brd[start: end: orientation]
        word = get_word(spec, used_words)
        if not word: continue
        copy = place_word(brd, word, start, orientation)
        two_d_print(copy)
        # two_d_print(copy)
        # for i in range(start, end, orientation):
        #     if orientation == W and i % W > 0 and brd[i-1] not in EXISTING_COMBINATIONS: return ''
        #     if orientation == W and i % W < W - 1 and brd[i + 1] not in EXISTING_COMBINATIONS: return ''
        #     if orientation == 1 and i // W < H - 1 and brd[i + W] not in EXISTING_COMBINATIONS: return ''
        #     if orientation == 1 and i // W > 1 and brd[i - W] not in EXISTING_COMBINATIONS: return ''
        copy = fill_words(copy, sorted([*({*word_start} - {(start, end, orientation)})], key=lambda w: len(wd := copy[w[0]: w[1]: w[2]]) + wd.count('-')), used_words | {word})
        if copy: brd = copy

    return ''


def main():
    brd = parse_args().lower()
    brd = xword1(brd)
    # two_d_print(brd)
    brd = xword2(brd)
    print(brd)


if __name__ == '__main__': main()

# Tristan Devictor, pd. 6, 2024
