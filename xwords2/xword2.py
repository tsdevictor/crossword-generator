import sys; args = sys.argv[1:]
import re
args = ['dct20k.txt', '4x4', '0']  # , 'H1x0early']


def parse_args():
    global WORDS_BY_LEN, H, W, NUM_BLOCKING, BRD_SIZE, BLOCK_NBRS, ALL_WORDS
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    ALL_WORDS = set()                             # set of all words in the dictionary
    WORDS_BY_LEN = {i: [] for i in range(3, 31)}  # dictionary of all words -> key=len, val={words}
    value = {char: 0 for char in alphabet}        # compute value of each char based on how common it is
    for line in open(args[0]):                    # first arg is dictionary
        if re.search('^[A-Za-z]{3,}$', (word := line.rstrip().lower())):  # make sure len(word) > 3 and only word characters
            WORDS_BY_LEN[len(word)].append(word)
            ALL_WORDS.add(word)
            for char in word: value[char] += 1

    # sort words by their value (sum of values of each char in the word)
    WORDS_BY_LEN = {i: sorted(WORDS_BY_LEN[i], key=(lambda w: -sum(w.count(c) * value[c] for c in alphabet))) for i in WORDS_BY_LEN}

    H, W = map(int, re.split('x', args[1], re.I))  # height, width of board
    NUM_BLOCKING, BRD_SIZE = int(args[2]), H * W   # number of blocking squares, board size
    if NUM_BLOCKING == BRD_SIZE: return '#' * BRD_SIZE  # trivial solution to trivial problem

    # neighbor positions (3 squares north, east, south, west) -> used for implied blocking square placement
    BLOCK_NBRS = [[] for _ in range(BRD_SIZE)]
    for i in range(BRD_SIZE):
        for drt in [W, -W, 1, -1]:  # south, north, east, west
            nbrs = [n for d in range(1, 4) if 0 <= (n := i + d * drt) < BRD_SIZE and abs(n // W - i // W) == abs(drt) // W * d]
            if nbrs: BLOCK_NBRS[i].append(nbrs)

    brd = ['-' for _ in range(BRD_SIZE)]
    if NUM_BLOCKING % 2: brd[BRD_SIZE // 2] = '#'  # if odd num_blocking, '#' must be in center because board is symmetric over 180
    for arg in args[3:]:  # words that are passed in: e.g., "early" at position (0, 0) horizontally
        orientation, word = re.split('\d*x\d*', arg, re.I)  # 'H' or 'V', word
        if not word: word = '#'                             # if no word is provided, it is assumed to be a blocking tile
        row, col = map(int, re.findall('\d+', arg))  # position, e.g., 0x0
        pos = row * W + col
        # place each word that is passed in
        for char in word: brd, pos = [*place_block(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

    return ''.join(brd)


def reflect(pos): return BRD_SIZE - 1 - pos  # reflection of positions for 180 degree symmetry


def two_d_print(brd):
    print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]) + '\n')


def disconnected(brd, i=0):  # returns set of non-blocking positions that are disconnected from the rest (floodfill)
    seen = set()
    queue = [brd.find('-') if not i else i]
    for idx in queue:  # loop through queue of white squares and their neighbors
        if not 0 <= idx < BRD_SIZE or idx in seen or brd[idx] == '#': continue
        seen.add(idx)
        if (idx + 1) // W == idx // W: queue.append(idx + 1)
        if (idx - 1) // W == idx // W: queue.append(idx - 1)
        queue.append(idx + W)
        queue.append(idx - W)
    # return set of white squares that were not encountered in floodfill
    return {i for i in range(BRD_SIZE) if i not in seen and brd[i] != '#'}


def place_block(brd, pos, item):
    brd = [*brd]
    if item != '#':  # placement of non-blocking square has no implications except reflected pos (except special cases)
        brd[pos] = item
        if brd[reflect(pos)] == '-': brd[reflect(pos)] = '.'
        return ''.join(brd)

    num_blocking = brd.count('#')
    queue, copy = [pos], [char if char in '#-' else '-' for char in brd]
    for i in queue:  # loop through queue of implied blocking squares to satisfy American xword rules
        if copy[i] == '#': continue
        if brd[i] != '-': return ''
        copy[i] = brd[i] = '#'
        num_blocking += 1
        queue.append(reflect(i))
        for drt in BLOCK_NBRS[i]:
            end = ''.join(nbrs).find('#') if '#' in (nbrs := [copy[nbr] for nbr in drt]) else 0
            if len(drt) < 3: end = len(drt)
            for j in range(end):
                queue.append(drt[j])

    dc = disconnected(''.join(brd))  # if white squares are not connected, fill them...
    if not dc: return ''.join(brd)
    for k, char in enumerate(brd):
        if len({brd[m] for m in dc}) != 1: return ''
        if char == '#': continue
        if len(dc) <= NUM_BLOCKING - num_blocking: break  # ...unless it requires too many '#' to do so -> board is invalid
        dc = disconnected(''.join(brd), k)
    for dis in dc: brd[dis] = '#'

    return ''.join(brd)


def block_structure(brd):  # brute force creation of blocking square structure
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


def set_up(brd):  # pre-compute possible words at each position
    global POSSIBLE_WORDS, WORD_STARTS, INTERSECTIONS
    POSSIBLE_WORDS = {}  # start, orientation: positions included, possible words
    for i, char in enumerate(brd):
        if char == '#': continue
        orientations = []
        if i // W == 0 or (i - W >= 0 and brd[i - W] == '#'):
            hole = brd[i: BRD_SIZE - (W - i % W) + 1: W]
            orientations.append((W, hole.find('#') * W + i % W if '#' in hole else BRD_SIZE - (W - i % W) + 1))
        if i % W == 0 or ((i - 1) // W == i // W and brd[i - 1] == '#'):
            orientations.append((1, min(brd.find('#', i) if NUM_BLOCKING and '#' in brd[i:] else BRD_SIZE, i // W * W + W)))
        for o, end in orientations:
            if '-' not in (spec := brd[i: end: o]): continue
            POSSIBLE_WORDS[(i, o)] = (range(i, end, o), set())
            for w in WORDS_BY_LEN[len(spec)]:
                for k, c in enumerate(w):
                    if spec[k] not in {'-', c}: break
                else: POSSIBLE_WORDS[(i, o)][1].add(w)
    # map each position "p" to the position "f" of the first character of the word that includes "p"
    WORD_STARTS = {(pos, orientation): i for i, orientation in POSSIBLE_WORDS for pos in POSSIBLE_WORDS[i, orientation][0]}
    INTERSECTIONS = {}
    for pos1, orientation1 in POSSIBLE_WORDS:
        for pos2, orientation2 in POSSIBLE_WORDS:
            if orientation1 == orientation2: continue
            for h, i in enumerate(POSSIBLE_WORDS[(pos1, orientation1)][0]):
                for j, k in enumerate(POSSIBLE_WORDS[(pos2, orientation2)][0]):
                    if i == k:
                        INTERSECTIONS[(pos1, orientation1, pos2, orientation2)] = (h, j)


def get_word(pos, orientation, possible_words, spec, used_words):  # return word that can fill given position
    if '-' not in spec: return spec
    for word in possible_words[(pos, orientation)][1]:
        if word in used_words: continue
        for i, char in enumerate(word):
            if spec[i] != '-' and spec[i] != char: break
        else: return word


def place_word(brd, word, start, orientation):  # placement of word in xword board
    brd = [*brd]
    for i, char in enumerate(word): brd[start + i * orientation] = char
    return ''.join(brd)


def is_valid(brd):  # check that each word (i) exists or (ii) is not yet complete
    for start, orientation in POSSIBLE_WORDS:
        positions = POSSIBLE_WORDS[(start, orientation)][0]
        word = ''.join(brd[i] for i in positions)
        if '-' not in word and word not in ALL_WORDS: return False
    return True


def update_possible(word, orientation, positions, possible_words):
    start, perpendicular = positions[0], (1 if orientation == W else W)
    removed = {key: [] for key in possible_words}
    for pos in positions:
        for w in possible_words[(pos, perpendicular)][1]:
            i1, i2 = INTERSECTIONS[(start, orientation, pos, perpendicular)]
            if word[i1] != w[i2] or w == word:
                removed[(pos, perpendicular)].append(w)
    for key in removed:
        for w in removed[key]:
            possible_words[key][1].remove(w)
    removed[(start, orientation)] = possible_words[(start, orientation)]
    possible_words.pop((start, orientation))
    return removed


def fill_words(brd, possible_words, used_words):  # brute force filling of words in xword
    if not is_valid(brd): return ''
    if '-' not in brd: return brd

    for start, orientation in possible_words:
        positions = possible_words[(start, orientation)][0]
        word = get_word(start, orientation, possible_words, ''.join([brd[i] for i in positions]), used_words)
        new_brd = place_word(brd, word, start, orientation)
        two_d_print(new_brd)
        removed = update_possible(word, orientation, positions, possible_words)
        new_brd = fill_words(new_brd, possible_words, used_words | {word})
        if new_brd: return new_brd
        for key in removed:
            if key not in possible_words: possible_words[key] = removed[key]
            else:
                for r in removed[key]:
                    possible_words.append(r)

    return ''


def main():
    brd = parse_args().lower()
    brd = block_structure(brd)
    two_d_print(brd)
    set_up(brd)
    brd = fill_words(brd, POSSIBLE_WORDS, set())
    print(brd)


if __name__ == '__main__': main()

# Tristan Devictor, pd. 6, 2024
