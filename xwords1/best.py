import sys; args = sys.argv[1:]
import re


def parse_args():
    global H, W, NUM_BLOCKING, BRD_SIZE, NBRS_BY_DIRECTION

    H, W, NUM_BLOCKING = int(args[0][:args[0].lower().index('x')]), int(args[0][args[0].lower().index('x') + 1:]), int(
        args[1])
    BRD_SIZE = H * W
    if NUM_BLOCKING == BRD_SIZE: return '#' * BRD_SIZE

    NBRS_BY_DIRECTION = [[] for _ in range(BRD_SIZE)]
    for i in range(BRD_SIZE):
        for drt in [W, -W, 1, -1]:
            nbrs = [n for d in range(1, 4) if
                    0 <= (n := i + d * drt) < BRD_SIZE and abs(n // W - i // W) == abs(drt) // W * d]
            if nbrs: NBRS_BY_DIRECTION[i].append(nbrs)

    brd = ['-' for _ in range(BRD_SIZE)]
    if NUM_BLOCKING % 2: brd[BRD_SIZE // 2] = '#'
    for arg in args[2:]:
        if '.txt' in arg: continue
        orientation, word = re.split('\d*x\d*', arg, re.I)
        if not word: word = '#'
        row, col = map(int, re.findall('\d+', arg))
        pos = row * W + col
        for char in word:
            brd, pos = [*place_block(''.join(brd), pos, char)], pos + [W, 1][orientation in 'Hh']

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


def main():
    brd = parse_args().lower()
    brd = block_structure(brd)
    print(brd)


if __name__ == '__main__': main()

# Tristan Devictor, pd. 6, 2024
