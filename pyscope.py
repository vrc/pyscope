#!/usr/bin/python3

import multiprocessing as mp
import numpy as np
import os
import pygame
import queue
import random
import time


def data_source(data, run):
    try:
        import board
        import adafruit_lsm303_accel

        i2c = board.I2C()
        acc = adafruit_lsm303_accel.LSM303_Accel(i2c)
        #acc.data_rate = adafruit_lsm303_accel.Rate.RATE_1344_HZ
        acc.data_rate = adafruit_lsm303_accel.Rate.RATE_1620_HZ
        while run.value:
            data.put(acc.acceleration)
            time.sleep(.001)
    except:
        x = 0
        dx = 2 * np.pi / 1920
        rng = np.random.default_rng()
        while run.value:
            x = x + dx
            if x > np.pi:
                x = x - 2 * np.pi
            s0 = 45 * np.sin(x + 0 * np.pi / 3) + (rng.random() - .5) * 5
            s1 = 45 * np.sin(x + 2 * np.pi / 3) + (rng.random() - .5) * 5
            s2 = 45 * np.sin(x - 2 * np.pi / 3) + (rng.random() - .5) * 5
            data.put((s0, s1, s2))
            time.sleep(.001)

def _setup_pygame():
    pygame.display.init()
    pygame.font.init()
    pygame.init()
    return None

def setup_pygame():
    disp_no = os.getenv('DISPLAY')
    if disp_no and not os.getenv('SSH_CONNECTION'):
        print('Using X11 driver')
        return _setup_pygame()
    else:
        for fp in ['fbcon', 'directfb', 'svgalib']:
            os.putenv('SDL_VIDEODRIVER', fp)
            print(f"Attempting {fp}")
            try:
                return _setup_pygame()
            except pygame.error:
                pass
    raise Exception('setup_pygame failed')


class Scope :
    screen = None;
    
    def __init__(self, xmax=1920, ymax=1200):
        setup_pygame()
        print(f"display: {pygame.display.Info()}")
        self.screen_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.size = (min(xmax, self.screen_size[0]), min(ymax, self.screen_size[1]))
        self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN)
        self.bg = pygame.Surface(self.size)
        self.setup_bg(self.bg)
        pygame.display.update()
        self.boundbox = pygame.Rect(0, 0, self.size[0], self.size[1])
        print(f"screen: {self.screen_size}, scope: {self.size}")
        print(f"display: {pygame.display.Info()}")

    def setup_bg(self, bg):
        "Renders an empty graticule"
        xmin = 10
        xmax = self.size[0] - 10
        xsize = xmax - xmin
        x0 = self.size[0] // 2
        xline = xsize // 10
        xtick = xline // 5
        xline = xtick * 5
        xsize = xline * 10
        xmin = x0 - xsize // 2
        xmax = x0 + xsize // 2

        ymin = 30
        ymax = self.size[1] - 30
        ysize = ymax - ymin
        y0 = self.size[1] // 2
        yline = ysize // 8
        ytick = yline // 5
        yline = ytick * 5
        ysize = yline * 8
        ymin = y0 - ysize // 2
        ymax = y0 + ysize // 2

        bg.fill((0, 0, 0))        

        borderColor = (255, 255, 255)
        lineColor = (64, 64, 64)
        subDividerColor = (128, 128, 128)

        pygame.draw.rect(bg, borderColor, (xmin - 2, ymin - 2, xsize + 4, ysize + 4), 2)

        # draw the grid
        for i in range(0, 7):
            y = ymin + (i + 1) * yline
            pygame.draw.line(bg, lineColor, (xmin, y), (xmax, y))
        for i in range(0, 9):
            x = xmin + (i + 1) * xline
            pygame.draw.line(bg, lineColor, (x, ymin), (x, ymax))

        # draw the ticks
        tlen = 4
        for i in range(1, 40):
            y = ymin + i * ytick
            pygame.draw.line(bg, subDividerColor, (x0 - tlen - 1, y), (x0 + tlen, y))
        for i in range(1, 50):
            x = xmin + i * xtick
            pygame.draw.line(bg, subDividerColor, (x, y0 - tlen - 1), (x, y0 + tlen))

        self.xlim = (xmin, xmax)
        self.ylim = (ymin, ymax)
        self.x0 = x0
        self.y0 = y0

    def rect(self):
        return self.boundbox

    def _draw(self, samples):
        #scale = (self.ylim[1] - self.ylim[0]) * 0.45
        scale = (self.ylim[1] - self.ylim[0]) * 0.01
        p0 = [(self.xlim[0] + i, self.y0 - int(scale * v[0])) for i, v in enumerate(samples)]
        p1 = [(self.xlim[0] + i, self.y0 - int(scale * v[1])) for i, v in enumerate(samples)]
        p2 = [(self.xlim[0] + i, self.y0 - int(scale * v[2])) for i, v in enumerate(samples)]
        #p3 = [(self.xlim[0] + i, self.y0) for i, v in enumerate(samples)]
        pygame.draw.lines(self.screen, (200, 200, 0), False, p0)
        pygame.draw.lines(self.screen, (0, 200, 0), False, p1)
        pygame.draw.lines(self.screen, (0, 200, 200), False, p2)
        #pygame.draw.lines(self.screen, (0, 0, 200), False, p3)

    def update(self, samples, bg=None):
        if bg is None:
            bg = self.bg
        self.screen.blit(bg, self.rect())
        self._draw(samples)

scope = Scope(1900, 800)

try:
    run = mp.Value('b', True)
    data = mp.Queue(0)

    proc = mp.Process(target=data_source, args=(data, run))
    proc.start()

    font = pygame.font.Font(None, 30)
    title = font.render('Bibi rocks!', True, (255, 255, 255))
    title_pos = (15, 5)
    fps = font.render('fps:  0.00', True, (100, 100, 100))
    fps_pos = (scope.size[0] - fps.get_width() - 15, 5)
    status = font.render('pos:', True, (200, 200, 200))
    status_pos = (15, scope.screen_size[1] - 5 - status.get_height())

    pygame.display.update()

    sample_cnt = (scope.xlim[1] - scope.xlim[0])
    samples = [(0,0,0)] * sample_cnt

    update_cnt = 0
    begin = time.perf_counter_ns()
    while run.value:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == ord('q')):
                run.value = False
                break
            #if event.type == pygame.MOUSEBUTTONDOWN:
            if event.type == pygame.MOUSEMOTION:
                s = f"pos: {pygame.mouse.get_pos()}"
                status = font.render(s, True, (200, 200, 200), (0, 0, 0))

        try:
            while True:
                samples.append(data.get_nowait())
        except queue.Empty:
            pass

        batch = font.render(f"batch: {len(samples) - sample_cnt}", True, (157, 157, 157))
        samples = samples[-sample_cnt:]

        if True:
            scope.update(samples)
        else:
            scope.setup_bg(scope.screen)
            scope._draw(samples)

        scope.screen.blit(title, title_pos)
        if update_cnt == 10:
            end = time.perf_counter_ns()
            fps = font.render(f"fps: {1e10/(end - begin):5.2f}", True, (0, 157, 0))
            update_cnt = 0
            begin = end
        else:
            update_cnt = update_cnt + 1

        scope.screen.blit(batch, (scope.x0, 5))
        scope.screen.blit(fps, fps_pos)
        #scope.screen.fill(0, 0, 0), 
        scope.screen.blit(status, status_pos)

        pygame.display.update()
        time.sleep(.001)
finally:
    run.value = False
    pygame.quit()
    proc.join()
