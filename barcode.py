import pygame

from pygame import camera
import pygame.display
from pygame.time import Clock
from pygame.draw import line
from pygame import font
from pygame import transform

from pygame.surfarray import pixels2d

MIN_BITS = 10


CODABAR_RAW = {
    ('001', '0001'): 0,
    ('010', '0001'): 2,
    ('100', '0001'): 6,
    ('001', '0010'): 1,
    ('010', '0010'): '-',
    ('100', '0010'): 7,
    ('001', '0100'): 4,
    ('010', '0100'): '$',
    ('100', '0100'): 8,
    ('001', '1000'): 5,
    ('010', '1000'): 9,
    ('100', '1000'): 3,
    ('000', '1110'): '.',
    ('000', '1101'): '/',
    ('000', '1011'): ':',
    ('000', '0111'): '+',
}

CODABAR = {}
for (spaces, bars), val in CODABAR_RAW.items():
    s1, s2, s3 = spaces
    b1, b2, b3, b4 = bars
    sym = ''.join((b1, s1, b2, s2, b3, s3, b4, '0'))
    v = str(val)
    CODABAR_RAW[sym] = v

UPC_LEFT = {
    '0001101': 0,
    '0011001': 1,
    '0010011': 2,
    '0111101': 3,
    '0100011': 4,
    '0110001': 5,
    '0101111': 6,
    '0111011': 7,
    '0110111': 8,
    '0001011': 9,
}

def invert(s):
    return ''.join('0' if c == '1' else '1' for c in k)

UPC_RIGHT = {}
for k, v in UPC_LEFT.items():
    UPC_RIGHT[invert(k)] = v


def decode_codabar(s):
    out = ''
    SIZE = 8
    while s:
        chunk, s = s[:SIZE], s[SIZE:]
        out += CODABAR.get(chunk, '#') 
        #out += '%02x' % (int(chunk, 2))
        #out += 'a'

    return out


def count(s):
    return sum(int(c == '#') for c in s)


def interpolate(samples, length):
    """Use a catmull-rom spline to interpolate samples to length length"""
    l = float(len(samples))

    maxk = len(samples) - 1

    def p(k):
        return samples[max(0, min(maxk, k))]

    def m(k):
        return (samples[min(maxk, k + 1)] - samples[max(0, k - 1)]) * 0.5

    out = []
    for i in xrange(length):
        src = i * l / length
        k, t = divmod(src, 1.0)
        k = int(k)

        p0 = p(k)
        p1 = p(k + 1)
        
        m0 = m(k)
        m1 = m(k + 1)

        t2 = t * t
        t3 = t2 * t

        out.append(
            (2 * t3 - 3 * t2 + 1) * p0 +
            (t3 - 2 * t2 + t) * m0 +
            (-2 * t3 + 3 * t2) * p1 +
            (t3 - t2) * m1
        )
    return out


def decode_upc(bits):
    if not bits.startswith('101') or bits[42:45] != '101' and not bits.endswith('101'):
        return ''
    bits = bits[3:42] + bits[45:-3]
    out = []
    lookup = UPC_LEFT
    for i in xrange(12):
        c, bits = bits[:7], bits[7:]
        if i == 6:
            lookup = UPC_RIGHT
        out.append(str(lookup.get(c, '#')))
    return ''.join(out)

BEST = '#' * 12

def merge_code(code):
    global BEST
    out = []
    for a, b in zip(BEST, code):
        if b != '#':
            c = b
        else:
            c = a
        out.append(c)
    BEST = ''.join(out)
    return BEST


def detect_barcode(samples):
    bars = transitions_to_bars(
        read_transitions(samples),
        len(samples)
    )
    widths = []
    bs = []
    for dir, start, end in bars:
        w = end - start
        widths.append(w)
        bs.append((('1' if dir < 0 else '0'), w))

    #avgw = median(widths)
    widths = list(set(float(w) for w in widths))
    widths.sort()
    for avgw in widths:
        out = []
        for s, w in bs:
            w = int(w / avgw + 0.5)
            if w > 4:
                if len(out) > 20:
                    break
                else:
                    out = []
                    continue
            out.append(s * w)
        inp = ''.join(out)
        dec = decode_upc(inp)
        if dec:
            return merge_code(dec)
    
    return BEST


THRESHOLD = 10

class Graph(object):
    def __init__(self, w, h):
        self.surf = pygame.Surface((w, h))
        self.w = w
        self.h = h

    def plot_graph(self, samples):
        self.surf.fill((0, 0, 0))
        for i, v in enumerate(samples):
            if i > self.w:
                break
            
            col = (255, 255, 0)
            last = samples[max(0, i - 5)]
            if v - last > THRESHOLD:
                col = (255, 0, 0)
            elif last - v > THRESHOLD:
                col = (0, 128, 0)

            pygame.draw.line(self.surf, col, (i, self.h), (i, self.h - int(v)))
        

def read_transitions(samples):
    lastm = None
    start = None
    off = int(len(samples) * (5.0 / 1024) + 0.5)
    for i, v in enumerate(samples):
        last = samples[max(0, i - off)]
        if v - last > THRESHOLD:
            m = 1
        elif last - v > THRESHOLD:
            m = -1
        else:
            m = 0

        if lastm is None:
            lastm = m
            continue

        if m != lastm:
            if start is not None and lastm:
                yield lastm, start, i - 1
            start = i
        lastm = m


def transitions_to_bars(trans, w):
    last_end = 0
    last = 0, 0, 0
    for dir, start, end in trans:
        if last is not None:
            ld, ls, le = last 
            if ld != dir:
                if ld == 0:
                    ld = -dir
                e = (start + end) * 0.5
                yield ld, last_end, e
                last_end = e
            else:
                last = dir, ls, end
            
        last = dir, start, end

    yield last[0], last_end, w


class DrawCode(object):
    def __init__(self, w, h):
        self.surf = pygame.Surface((w, h))
        self.w = w
        self.h = h

    def plot_graph(self, samples):
        scale = float(self.w) / len(samples)
        self.surf.fill((255, 0, 0))

        transitions = list(read_transitions(samples))
        bars = transitions_to_bars(
            transitions,
            len(samples)
        )
        for dir, start, end in bars:
            s = int(start * scale + 0.5)
            e = int(end * scale + 0.5)
            c = (255, 255, 255) if dir > 0 else (0, 0, 0)
            self.surf.fill(c, pygame.Rect(s, 0, e-s, self.h))

        for dir, start, end in transitions:
            s = int(start * scale + 0.5)
            e = int(end * scale + 0.5)
            c = (0, 128, 0) if dir > 0 else (255, 0, 0)
            self.surf.fill(c, pygame.Rect(s, 0, e-s, self.h // 4))


def median(samples):
    s = samples[:]
    s.sort()
    if not s:
        return 0
    return s[len(s) // 2 - 1]


camera.init()

pygame.init()
cam = camera.Camera(camera.list_cameras()[0], (1280, 1024))
screen = pygame.display.set_mode((1024, 768))
cam.start()

clock = Clock()

font.init()
f = font.SysFont('FreeSans', 14)


g = Graph(1024, 256)
dc = DrawCode(1024, 20)


LEFT = 350
RIGHT = 1024 - LEFT

dc2 = DrawCode(RIGHT - LEFT, 5)

def read_line(image):
    l = []
    for x in xrange(LEFT, RIGHT):
        c = image.get_at((x, 240))
        l.append(c.r * 0.3 + c.g * 0.6 + c.b * 0.1)
    return l

lastl = []

ACCUMULATE = 3
ACCUMULATE_FRAC = 1.0 / ACCUMULATE

while True:
    clock.tick(30)
    source = cam.get_image()
    image = source.subsurface(pygame.Rect((1280 - 1024) // 2, 0, 1024, 480))
    screen.blit(image, (0, 0))
    line(screen, (255, 255, 0), (LEFT, 240), (RIGHT, 240))

    l = read_line(image)
    lastl = [l] + lastl[:ACCUMULATE]

    acc = [0] * len(l)
    for l in lastl:
        for i, s in enumerate(l):
            acc[i] += s * ACCUMULATE_FRAC

    interpolated = interpolate(acc, 2048)
    g.plot_graph(interpolate(acc, 1024))
    dc.plot_graph(interpolated)
    dc2.plot_graph(interpolated)
    out = detect_barcode(interpolated)

    s = f.render(out[:100], True, (0, 0, 0))
    screen.blit(s, (31, 451))
    s = f.render(out[:100], True, (255, 255, 255))
    screen.blit(s, (30, 450))
    screen.blit(g.surf, (0, 500))
    screen.blit(dc.surf, (0, 480))
    screen.blit(dc2.surf, (LEFT, 241))
    pygame.display.flip()
