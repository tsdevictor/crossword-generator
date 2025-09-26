import sys; args = sys.argv[1:]
import re
import cProfile
args = ['dct20k.txt', '5x5', '0']


def parse_args():
    global WORDS_BY_LEN, H, W, NUM_BLOCKING, BRD_SIZE, BLOCK_NBRS, ALL_WORDS, PREFIXES
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    H, W = map(int, re.split('x', args[1], re.I))  # height, width of board
    NUM_BLOCKING, BRD_SIZE = int(args[2]), H * W  # number of blocking squares, board size
    if NUM_BLOCKING == BRD_SIZE: return '#' * BRD_SIZE  # trivial solution to trivial problem

    PREFIXES, ALL_WORDS = set(), set()  # all prefixes, all words
    min_len, max_len = 3, max(H, W)
    WORDS_BY_LEN = {i: [] for i in range(min_len, max_len + 1)}  # dictionary of all words -> key=len, val={words}
    value = {char: 0 for char in alphabet}  # compute value of each char based on how common it is
    regex = '^[A-Za-z]{' + f'{min_len},{max_len}' + '}$'
    for line in open(args[0]):  # first arg is dictionary
        if re.search(regex, (word := line.rstrip().lower())):  # make sure len(word) > 3 and only word characters
            WORDS_BY_LEN[len(word)].append(word)
            ALL_WORDS.add(word)
            PREFIXES.add(word[:2])
            PREFIXES.add(word[:3])
            if len(word) > 3: PREFIXES.add(word[:4])
            for char in word: value[char] += 1

    # sort words by their value (sum of values of each char in the word)
    WORDS_BY_LEN = {i: sorted(WORDS_BY_LEN[i], key=(lambda w: -sum(value[c] for c in w))) for i in WORDS_BY_LEN}

    # neighbor positions (3 squares north, east, south, west) -> used for implied blocking square placement
    BLOCK_NBRS = [[] for _ in range(BRD_SIZE)]
    for i in range(BRD_SIZE):
        for drt in [W, -W, 1, -1]:  # south, north, east, west
            nbrs = [n for d in range(1, 4) if
                    0 <= (n := i + d * drt) < BRD_SIZE and abs(n // W - i // W) == abs(drt) // W * d]
            if nbrs: BLOCK_NBRS[i].append(nbrs)

    brd = ['-' for _ in range(BRD_SIZE)]
    if NUM_BLOCKING % 2: brd[BRD_SIZE // 2] = '#'  # if odd num '# -> '#' must be in center (board symmetric over 180)
    for arg in args[3:]:  # words that are passed in: e.g., "early" at position (0, 0) horizontally
        orientation, word = re.split('\d*x\d*', arg, re.I)  # 'H' or 'V', word
        if not word: word = '#'  # if no word is provided, it is assumed to be a blocking tile
        row, col = map(int, re.findall('\d+', arg))  # position, e.g., 0x0
        pos = row * W + col
        for char in word: brd, pos = [*place_block(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

    return ''.join(brd)


def reflect(pos): return BRD_SIZE - 1 - pos  # reflection of positions for 180 degree symmetry


def two_d_print(brd): print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]) + '\n')


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
        if len(
            dc) <= NUM_BLOCKING - num_blocking: break  # ...unless it requires too many '#' to do so -> board is invalid
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
    global POSSIBLE_WORDS, POSSIBLE_POSITIONS, POS_TO_WORD_START
    POSSIBLE_WORDS = {}  # start, orientation: possible words
    POSSIBLE_POSITIONS = {}  # start, orientation: included positions
    for i, char in enumerate(brd):
        if char == '#': continue
        orientations = []
        if i // W == 0 or (i - W >= 0 and brd[i - W] == '#'):
            hole = brd[i: BRD_SIZE - (W - i % W) + 1: W]
            orientations.append(
                ((hole.find('#') + i // W) * W + i % W if '#' in hole else BRD_SIZE - (W - i % W) + 1, W))
        if i % W == 0 or ((i - 1) // W == i // W and brd[i - 1] == '#'):
            orientations.append(
                (min(brd.find('#', i) if NUM_BLOCKING and '#' in brd[i:] else BRD_SIZE, i // W * W + W), 1))
        for end, orientation in orientations:
            if '-' not in (spec := brd[i: end: orientation]): continue
            POSSIBLE_POSITIONS[(i, orientation)] = [k for k in range(i, end, orientation)]
            POSSIBLE_WORDS[(i, orientation)] = []
            for w in WORDS_BY_LEN[len(spec)]:
                for k, c in enumerate(w):
                    if spec[k] not in {'-', c}: break
                else:
                    POSSIBLE_WORDS[(i, orientation)].append(w)
    POS_TO_WORD_START = {(pos, orientation): i for (i, orientation) in POSSIBLE_POSITIONS for pos in
                         POSSIBLE_POSITIONS[(i, orientation)]}


def place_word(brd, word, start, orientation):  # placement of word in xword board
    brd = [*brd]
    for i, char in enumerate(word): brd[start + i * orientation] = char
    return is_valid(''.join(brd))


def is_valid(brd):  # check that each word (i) exists or (ii) is not yet complete
    global MAX_SCORE
    seen_words = set()
    score = 0
    for key in POSSIBLE_POSITIONS:
        word = ''
        for i in POSSIBLE_POSITIONS[key]:
            if brd[i] == '-':
                if 2 <= len(word) <= 4 and word not in PREFIXES: return ''
                break
            word += brd[i]
        else:
            if word not in ALL_WORDS: return ''
            if word in seen_words: return ''
            score += len(word)
            seen_words.add(word)
            if score > MAX_SCORE:
                print(brd)
                MAX_SCORE = score
    return brd


def update_words(brd, positions, orientation, possible_words, used_words):
    opposite = 1 if orientation == W else W
    updated = possible_words.copy()
    for pos in positions:
        if (pos, opposite) not in POS_TO_WORD_START: continue
        start = POS_TO_WORD_START[(pos, opposite)]
        # update based on whether word satisfies prefix above it
        possible = []
        for w in possible_words[(start, opposite)]:
            if w[pos // opposite - start // opposite] == brd[pos] and w not in used_words:
                possible.append(w)
        updated[(start, opposite)] = possible
    return updated


def fill_words(brd, possible_positions, possible_words, used_words):  # brute force filling of words in xword
    if '-' not in brd: return brd

    for start, orientation in sorted(possible_positions.keys(), key=lambda k: len(possible_words[k])):
        positions = possible_positions[(start, orientation)]
        spec = ''.join([brd[i] for i in positions])
        if '-' not in spec: continue
        for word in possible_words[(start, orientation)]:
            if word in used_words: continue
            new_brd = place_word(brd, word, start, orientation)
            if not new_brd: continue
            updated = update_words(new_brd, positions, orientation, possible_words, used_words | {word})
            new_brd = fill_words(new_brd, possible_positions, updated, used_words | {word})
            if new_brd: return new_brd

    return ''


def rough_draft(brd):
    used_words = set()

    for i, char in enumerate(brd):
        if (i, W) not in POSSIBLE_WORDS: continue
        brd_hole = brd[i: BRD_SIZE - (W - i % W) + 1: W]
        word_len = brd_hole.find('#') if '#' in brd_hole else (BRD_SIZE - (W - i % W)) // W + 1

        spec = brd[i: i + word_len * W: W]
        for word in POSSIBLE_WORDS[(i, W)]:
            if word in used_words: continue
            for k in range(len(word)):
                if spec[k] != word[k] and spec[k] != '-': break
            else:
                used_words.add(word)
                brd = [*brd]
                for j in range(len(word)): brd[i + j * W] = word[j]
                brd = ''.join(brd)
                break
        break

    for i, char in enumerate(brd):
        if (i, 1) not in POSSIBLE_WORDS: continue
        word_len = min(brd.find('#', i) if NUM_BLOCKING and '#' in brd[i:] else BRD_SIZE, i // W * W + W) - i
        spec = brd[i: i + word_len]
        for word in POSSIBLE_WORDS[(i, 1)]:
            if word in used_words: continue
            for k in range(len(word)):
                if spec[k] != word[k] and spec[k] != '-':
                    break
            else:
                used_words.add(word)
                brd = [*brd]
                for j in range(len(word)): brd[i + j] = word[j]
                brd = ''.join(brd)
                break

    global MAX_SCORE
    MAX_SCORE = 0
    for start, orientation in POSSIBLE_WORDS:
        word = ''
        for i in POSSIBLE_POSITIONS[(start, orientation)]: word += brd[i]
        if word not in ALL_WORDS: continue
        MAX_SCORE += len(word)

    return brd


def main():
    brd = parse_args().lower()
    brd = block_structure(brd)
    set_up(brd)
    print(rough_draft(brd))
    brd = fill_words(brd, POSSIBLE_POSITIONS, POSSIBLE_WORDS, set())
    print(brd)


if __name__ == '__main__': cProfile.run('main()', sort='tottime')  # main()


# Tristan Devictor, pd. 6, 2024
