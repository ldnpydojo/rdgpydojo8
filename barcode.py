import pygame

from pygame import camera
import pygame.display
from pygame.time import Clock
from pygame.draw import line
from pygame import font

from pygame.surfarray import pixels2d

camera.init()

pygame.init()
screen = pygame.display.set_mode((640, 480))
cam = camera.Camera(camera.list_cameras()[0])
cam.start()

clock = Clock()

font.init()
f = font.SysFont('FreeSans', 14)

MIN_BITS = 80


CODING = {
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

MAP = {}
for (spaces, bars), val in CODING.items():
    s1, s2, s3 = spaces
    b1, b2, b3, b4 = bars
    sym = ''.join((b1, s1, b2, s2, b3, s3, b4))
    v = str(val)
    MAP[sym] = v


def decode(s):
    out = ''
    SIZE = 8
    while s:
        chunk, s = s[:SIZE], s[SIZE:]
        #out += MAP.get(chunk, '#') 
        out += '%02x' % (int(chunk, 2))
        #out += 'a'

    return out


from collections import Counter

def count(str):
    c = Counter()
    for char in str:
        c[char] += 1
    return c


def count(s):
    return len(s.split('#'))

def detect_barcode(samples):
    last = None
    lastedge = 0
    out = []
    med = median(samples)
    for i, s in enumerate(samples):
        v = s >= med
        if v is not last:
            dist = i - lastedge
            out.append(dist)
            last = v
            lastedge = i

    avgw = median(out) * 1.3 # sum(out) / len(out)
    out = [str(int(v > avgw)) for v in out]

    if len(out) < MIN_BITS:
        return ''

    inp = ''.join(out)
    best = ''
    bh = None
    for v in (0, 1):
        if v:
            s = ''.join(reversed(list(inp)))
        else:
            s = inp
        for i in range(10):
            for j in range(0, -10, -1):
                found = decode(s[i:j])
                hashes = count(found)
                if not best or bh is None or hashes > bh:
                    best = found
                    bh = hashes
    return '%s: %s' % (len(out), inp)
    return '%s: %s' % (len(out), best)


def median(samples):
    s = samples[:]
    s.sort()
    return s[len(s) // 2]

while True:
    clock.tick(20)
    image = cam.get_image()
    screen.blit(image, (0, 0))
    line(screen, (255, 255, 0), (100, 240), (540, 240))
    l = []
    for x in xrange(100, 540):
        c = image.get_at((x, 240))
        l.append(c.r * 0.3 + c.g * 0.6 + c.b * 0.1)
    out = detect_barcode(l)

    s = f.render(out[:100], True, (255, 255, 255))
    screen.blit(s, (30, 450))
    pygame.display.flip()
