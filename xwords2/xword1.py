import sys; args = sys.argv[1:]
import re
args = ['dctEckel.txt', '14x16', '108', 'h3x2', 'v2x4', 'V4x5', 'v7x5', 'v9x7',  'H9x5']


def parse_args():
    global H, W, NUM_BLOCKING, WORDS_BY_LEN, BRD_SIZE, NBRS_BY_DIRECTION
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    WORDS_BY_LEN = {i: [] for i in range(3, 31)}
    value = {char: 0 for char in alphabet}
    for line in open(args[0]):
        if re.search('^[A-Za-z]{3,}$', (word := line.rstrip().lower())):
            WORDS_BY_LEN[len(word)].append(word)
            for char in word:
                value[char] += 1
    WORDS_BY_LEN = {i: sorted(WORDS_BY_LEN[i], key=(lambda w: -sum(w.count(c) * value[c] for c in alphabet))) for i in WORDS_BY_LEN}

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
        if not word: word = '#'
        row, col = map(int, re.findall('\d+', arg))
        pos = row * W + col
        for char in word: brd, pos = [*place_block(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

    return ''.join(brd)


def reflect(pos):
    return BRD_SIZE - 1 - pos


def two_d_print(brd):
    print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]) + '\n')


def disconnected(brd, i=0):
    seen = set()
    queue = [brd.find('-') if not i else i]
    for idx in queue:
        if not 0 <= idx < BRD_SIZE or idx in seen or brd[idx] == '#': continue
        seen.add(idx)
        if (idx + 1) // W == idx // W: queue.append(idx + 1)
        if (idx - 1) // W == idx // W: queue.append(idx - 1)
        queue.append(idx + W)
        queue.append(idx - W)
    return {i for i in range(BRD_SIZE)} - (seen | {i for i in range(BRD_SIZE) if brd[i] == '#'})


def place_block(brd, pos, item):
    brd = [*brd]
    if item != '#':
        brd[pos] = item
        if brd[reflect(pos)] == '-': brd[reflect(pos)] = '.'
        return ''.join(brd)

    num_blocking = brd.count('#')
    queue, copy = [pos], [char if char in '#-' else '-' for char in brd]
    for i in queue:
        if copy[i] == '#': continue
        if brd[i] != '-': return ''
        copy[i] = brd[i] = '#'
        num_blocking += 1
        queue.append(reflect(i))
        for drt in NBRS_BY_DIRECTION[i]:
            end = ''.join(nbrs).find('#') if '#' in (nbrs := [copy[nbr] for nbr in drt]) else 0
            if len(drt) < 3: end = len(drt)
            for j in range(end):
                queue.append(drt[j])

    dc = disconnected(''.join(brd))
    if not dc: return ''.join(brd)
    for k, char in enumerate(brd):
        if len({brd[m] for m in dc}) != 1: return ''
        if char == '#': continue
        if len(dc) <= NUM_BLOCKING - num_blocking: break
        dc = disconnected(''.join(brd), k)
    for dis in dc:
        brd[dis] = '#'

    return ''.join(brd)


def block_structure(brd):
    if disconnected(brd): return ''
    if brd.count('#') > NUM_BLOCKING: return ''
    if brd.count('#') == NUM_BLOCKING: return brd.replace('.', '-')

    for i in range(BRD_SIZE):
        if brd[i] != '-': continue
        copy = place_block(brd, i, '#')
        if not copy: continue
        new_brd = block_structure(copy)
        if new_brd: return new_brd
        brd = place_block(brd, i, '.')

    return ''


def get_word(spec, used_words):
    if '-' not in spec: return spec
    for word in WORDS_BY_LEN[len(spec)]:
        if word in used_words: continue
        for i, char in enumerate(word):
            if spec[i] != '-' and spec[i] != char: break
        else: return word


def solve(brd):
    used_words = set()

    for i, char in enumerate(brd):
        if (i, W) not in POSSIBLE_WORDS: continue
        brd_hole = brd[i: BRD_SIZE - (W - i % W) + 1: W]
        word_len = brd_hole.find('#') if '#' in brd_hole else (BRD_SIZE - (W - i % W)) // W + 1

        spec = get_word(''.join(brd[i: i + word_len * W: W]), used_words)
        for word in POSSIBLE_WORDS[(i, W)]:
            for k in range(len(word)):
                if spec[k] != word[k] and spec[k] != '-': break
            else:
                used_words.add(word)
                brd = [*brd]
                for j in range(len(word)):
                    brd[i + j] = char
                brd = ''.join(brd)
                break

    for i, char in enumerate(brd):
        if (i, 1) not in POSSIBLE_WORDS: continue
        word_len = min(brd.find('#', i) if NUM_BLOCKING and '#' in brd[i:] else BRD_SIZE, i // W * W + W) - i
        spec = brd[i: i + word_len]
        for word in POSSIBLE_WORDS[(i, 1)]:
            for k in range(len(word)):
                if spec[k] != word[k] and spec[k] != '-': break
            else:
                used_words.add(word)
                brd = [*brd]
                for j in range(len(word)):
                    brd[i + j] = char
                brd = ''.join(brd)
                break

    return brd


def main():
    brd = parse_args().lower()
    brd = block_structure(brd)
    brd = solve(brd)
    two_d_print(brd)
    print(brd)


if __name__ == '__main__': main()

# Tristan Devictor, pd. 6, 2024
