import sys; args = sys.argv[1:]
import re
import time
args = ['dctEckel.txt', '21x21', '75']


def parse_args():
    global H, W, NUM_BLOCKING, BRD_SIZE, EDGES, THREE_AWAY_NBRS, FLOODFILL_NBRS

    H, W = map(int, re.split('x', args[1], re.I))  # height, width of board: ex. 3x3
    NUM_BLOCKING, BRD_SIZE = int(args[2]), H * W   # number of blocking squares, board size
    if NUM_BLOCKING == BRD_SIZE: return '#' * BRD_SIZE  # trivial solution to trivial problem

    EDGES = {i for i in range(BRD_SIZE) if i % W in (0, W-1) or i // W in (0, H-1)}  # set of positions counting as edges

    # pre-computation of neighbor positions (1 square north, east, south, west) -> used for floodfill
    FLOODFILL_NBRS = [[] for _ in range(BRD_SIZE)]
    # pre-computation of neighbor positions (3 squares north, east, south, west) -> used for implied blocking square placement
    THREE_AWAY_NBRS = [[] for _ in range(BRD_SIZE)]
    for i in range(BRD_SIZE):
        FLOODFILL_NBRS[i] = [n for drt in [W, -W, 1, -1] if 0 <= (n := i + drt) < BRD_SIZE and abs(n // W - i // W) == abs(drt) // W]
        for drt in [W, -W, 1, -1]:  # south, north, east, west
            nbrs = [n for d in range(1, 4) if 0 <= (n := i + d * drt) < BRD_SIZE and abs(n // W - i // W) == abs(drt) // W * d]
            if nbrs: THREE_AWAY_NBRS[i].append(nbrs)

    brd = ['-' for _ in range(BRD_SIZE)]  # initialize empty board
    if NUM_BLOCKING % 2: brd[BRD_SIZE // 2] = '#'  # if odd num '# -> '#' must be in center (board symmetric over 180)
    for arg in args[3:]:  # words that are passed in: e.g., "early" at position (0, 0) horizontally
        orientation, word = re.split('\d*x\d*', arg, re.I)  # 'H' or 'V', word
        if not word: word = '#'  # if no word is provided, it is assumed to be a blocking character
        row, col = map(int, re.findall('\d+', arg))  # position, e.g., 0x0
        pos = row * W + col
        for char in word: brd, pos = [*place_block(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

    return ''.join(brd)


def reflect(pos): return BRD_SIZE - pos - 1  # reflection of position about 180-degree rotation


def two_d_print(brd): print('\n'.join([''.join([brd[r * W + c] for c in range(W)]) for r in range(H)]) + '\n')


CACHE = {}
def disconnected(brd, pos=0):  # returns set of non-blocking positions that are disconnected from the rest (floodfill)
    key = (brd, pos)
    if key in CACHE: return CACHE[key]
    unseen = {i for i in range(BRD_SIZE) if brd[i] != '#'}
    queue = [pos if pos else brd.find('-')]
    for idx in queue:  # loop through queue of white squares (adding each square's neighbors every time)
        if idx not in unseen or brd[idx] == '#': continue
        unseen.remove(idx)
        for nbr in FLOODFILL_NBRS[idx]:
            if nbr in unseen: queue.append(nbr)
    CACHE[key] = unseen
    return unseen  # return set of white squares that were not encountered in floodfill


BRD_CACHE = {}
def place_block(brd, pos, item):
    brd = [*brd]
    if item != '#':  # placement of non-blocking square has no implications except reflected pos (except special cases)
        brd[pos] = item
        if brd[reflect(pos)] == '-': brd[reflect(pos)] = '.'
        return ''.join(brd)

    # making sure that all words are of length >= 3
    queue, copy = [pos], [char if char in '#-' else '-' for char in brd]
    for i in queue:  # loop through queue of implied blocking squares to satisfy American xword rules
        if copy[i] == '#': continue
        if brd[i] != '-': return ''

        copy[i] = brd[i] = '#'
        queue.append(reflect(i))
        for drt in THREE_AWAY_NBRS[i]:
            if len(drt) < 3: end = len(drt)
            else: end = ''.join(nbrs).find('#') if '#' in (nbrs := [copy[nbr] for nbr in drt]) else 0
            for j in range(end): queue.append(drt[j])

    num_blocking = brd.count('#')
    # making sure all white squares are connected to each other
    dc = disconnected(''.join(brd))
    if not dc: return ''.join(brd)
    #two_d_print(brd)
    #print()
    for k, char in enumerate(brd):  # if any white squares are not connected, fill them...
        if char == '#': continue
        if len({brd[m] for m in dc}) != 1: return ''  # can't fill up space that must have letter
        # ...unless it requires too many '#' to do so -> board is invalid
        if len(dc) <= NUM_BLOCKING - num_blocking: break
        dc = disconnected(''.join(brd), k)
    else: return ''
    for dis in dc: brd[dis], brd[reflect(dis)] = '#', '#'

    return ''.join(brd)


def block_choices(brd):  # sort choices for '#' placement to avoid "clumps" and therefore minimize word length
    choices, invalid = {i: 0 for i in range(BRD_SIZE) if brd[i] == '-'}, set()
    for pos in choices:
        new_brd = place_block(brd, pos, '#')
        if not new_brd: invalid.add(pos)
        else: choices[pos] = clump_score(new_brd), new_brd
    choices = {i: choices[i] for i in choices if i not in invalid}
    return sorted(choices.keys(), key=lambda ch: choices[ch][0], reverse=True), {i: choices[i][1] for i in choices}


def clump_score(brd):
    score, seen = 0, set()
    for pos in range(BRD_SIZE):
        if brd[pos] != '#' or pos in seen: continue
        queue = [pos]
        score += 1  # this blocking square was not connected to the rest -> +1 point because it is disconnected
        for idx in queue:  # loop through queue of blocking squares and their neighbors
            if pos in EDGES: score -= 0.2
            if not 0 <= idx < BRD_SIZE or idx in seen or brd[idx] != '#': continue  # base case for floodfill
            seen.add(idx)
            for nbr in FLOODFILL_NBRS[idx]: queue.append(nbr)

    len_weighting = 0
    for i, char in enumerate(brd):
        if char == '#': continue
        row, col, word_starts = i // W, i % W, []
        if row == 0 or (row > 0 and brd[i - W] == '#'):
            hole = brd[i: BRD_SIZE - (W - col) + 1: W]
            length = (((hole.find('#') + row) * W + col if '#' in hole else BRD_SIZE - (W - col) + 1) - i) // W
            len_weighting += length ** 3
        if col == 0 or ((i - 1) // W == row and brd[i - 1] == '#'):
            length = (brd.find('#', i) if '#' in brd[i:(row + 1) * W] else (row + 1) * W) - i
            len_weighting += length ** 3

    return score - len_weighting / 100000


def block_structure(brd):  # "brute-force" creation of blocking square structure
    if brd.count('#') > NUM_BLOCKING: return ''
    if brd.count('#') == NUM_BLOCKING: return brd.replace('.', '-')

    choices, new_brds = block_choices(brd)
    for i in choices:
        new_brd = block_structure(new_brds[i])
        if new_brd: return new_brd
        brd = place_block(brd, i, '.')

    return ''


def word_setup(brd):  # pre-compute possible words at each position
    global ALL_WORDS, MAX_SCORE, POSSIBLE_WORDS, POSSIBLE_POSITIONS, POS_TO_WORD_START

    ALL_WORDS = set()
    min_len, max_len = 3, max(H, W)  # len of smallest and biggest word in the crossword (guess)
    words_by_len = {i: [] for i in range(min_len, max_len + 1)}  # dictionary of all words -> key=len, val={words}
    value = {char: 0 for char in 'abcdefghijklmnopqrstuvwxyz'}  # compute "value" of each char based on how often it appears
    regex = '^[A-Za-z]{' + f'{min_len},{max_len}' + '}$'  # make sure len(word) > 3 and word is composed of only letters
    for line in open(args[0]):  # loop through dictionary
        if re.search(regex, (word := line.rstrip().lower())):
            words_by_len[len(word)].append(word)
            ALL_WORDS.add(word)
            for char in word: value[char] += 1
    # sort words by their value (sum of values of each char in the word)
    words_by_len = {i: sorted(words_by_len[i], key=lambda w: sum(value[c] for c in w), reverse=True) for i in
                    words_by_len}

    MAX_SCORE = 0
    POSSIBLE_WORDS = {}  # start, orientation: possible words
    POSSIBLE_POSITIONS = {}  # start, orientation: included positions
    for i, char in enumerate(brd):
        if char == '#': continue
        row, col, word_starts = i // W, i % W, []
        if row == 0 or (row > 0 and brd[i - W] == '#'):
            hole = brd[i: BRD_SIZE - (W - col) + 1: W]
            word_starts.append(((hole.find('#') + row) * W + col if '#' in hole else BRD_SIZE - (W - col) + 1, W))
        if col == 0 or ((i - 1) // W == row and brd[i - 1] == '#'):
            word_starts.append((brd.find('#', i) if '#' in brd[i:(row + 1) * W] else (row + 1) * W, 1))
        for end, orientation in word_starts:
            if '-' not in (spec := brd[i: end: orientation]): continue
            POSSIBLE_POSITIONS[(i, orientation)] = [k for k in range(i, end, orientation)]
            POSSIBLE_WORDS[(i, orientation)] = []
            for wrd in words_by_len[len(spec)]:
                for k, ch in enumerate(wrd):
                    if spec[k] not in {'-', ch}: break
                else: POSSIBLE_WORDS[(i, orientation)].append(wrd)
    POS_TO_WORD_START = {(pos, orientation): i for (i, orientation) in POSSIBLE_POSITIONS for pos in
                         POSSIBLE_POSITIONS[(i, orientation)]}


def place_word(brd, word, start, orientation):  # placement of word in xword board
    brd = [*brd]
    for i, char in enumerate(word): brd[start + i * orientation] = char
    return is_valid(''.join(brd))


def is_valid(brd):  # check that each word (i) exists or (ii) is not yet complete
    global MAX_SCORE
    score, seen = 0, set()
    for key in POSSIBLE_POSITIONS:
        positions = POSSIBLE_POSITIONS[key]  # range(start, end, increment)
        word = brd[positions[0]: positions[-1] + 1: key[1]]  # brd[start: end + 1: increment]
        if word in ALL_WORDS and word not in seen:
            seen.add(word)
            score += len(word)
            if score > MAX_SCORE:
                print(brd)
                MAX_SCORE = score
        elif '-' not in word or word in seen: return ''
    return brd


def update_word_choices(brd, positions, orientation, possible_positions, possible_words, used_word):
    opposite = 1 if orientation == W else W
    updated_words, updated_positions = possible_words.copy(), possible_positions.copy()
    updated_positions.pop((positions[0], orientation))
    for pos in positions:
        if (pos, opposite) not in POS_TO_WORD_START: continue
        start = POS_TO_WORD_START[(pos, opposite)]
        updated_words[(start, opposite)] = [w for w in possible_words[(start, opposite)]
                                            if w[(pos - start) // opposite] == brd[pos] and w != used_word]
    return updated_positions, updated_words


def fill_words(brd, possible_positions, possible_words):  # brute force filling of words in xword
    if '-' not in brd: return brd

    start, orientation = min(possible_positions.keys(), key=lambda k: len(possible_words[k]))
    positions = possible_positions[(start, orientation)]
    for word in possible_words[(start, orientation)]:
        new_brd = place_word(brd, word, start, orientation)
        if not new_brd: continue
        upd_p, upd_w = update_word_choices(new_brd, positions, orientation, possible_positions, possible_words, word)
        new_brd = fill_words(new_brd, upd_p, upd_w)
        if new_brd: return new_brd
    return ''


def main():
    start = time.time()
    brd = parse_args().lower()
    brd = block_structure(brd)
    two_d_print(brd)
    word_setup(brd)
    brd = fill_words(brd, POSSIBLE_POSITIONS, POSSIBLE_WORDS)
    print(brd)
    print(time.time() - start)


if __name__ == '__main__': main()


# Tristan Devictor, pd. 6, 2024
