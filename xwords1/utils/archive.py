def connected(brd):
    seen = set()
    queue = [brd.find('-')]
    for idx in queue:
        if not 0 <= idx < H * W: continue
        if idx in seen: continue
        seen.add(idx)
        if brd[idx] == '#': continue
        queue.append(idx + W)
        queue.append(idx - W)
        queue.append(idx + 1)
        queue.append(idx - 1)
    return len(seen) == H * W - brd.count('#')