#!/usr/bin/python3

import multiprocessing as mp
import numpy as np
import os
import pygame
import queue
import random
import time


def data_source(data, ctrl, run):
    try:
        import board
        import adafruit_lsm303_accel

        DATA_RATE = [
                adafruit_lsm303_accel.Rate.RATE_1_HZ,
                adafruit_lsm303_accel.Rate.RATE_10_HZ,
                adafruit_lsm303_accel.Rate.RATE_25_HZ,
                adafruit_lsm303_accel.Rate.RATE_50_HZ,
                adafruit_lsm303_accel.Rate.RATE_100_HZ,
                adafruit_lsm303_accel.Rate.RATE_200_HZ,
                adafruit_lsm303_accel.Rate.RATE_400_HZ,
                adafruit_lsm303_accel.Rate.RATE_1344_HZ,
                adafruit_lsm303_accel.Rate.RATE_1620_HZ,
                ]

        RANGE = [
                adafruit_lsm303_accel.Range.RANGE_2G,
                adafruit_lsm303_accel.Range.RANGE_4G,
                adafruit_lsm303_accel.Range.RANGE_8G,
                adafruit_lsm303_accel.Range.RANGE_16G,
                ]

        MODE = [
                adafruit_lsm303_accel.Mode.MODE_NORMAL,
                adafruit_lsm303_accel.Mode.MODE_HIGH_RESOLUTION,
                adafruit_lsm303_accel.Mode.MODE_LOW_POWER,
                ]

        i2c = board.I2C()
        acc = adafruit_lsm303_accel.LSM303_Accel(i2c)
        acc.data_rate = adafruit_lsm303_accel.Rate.RATE_1620_HZ
        while run.value:
            data.put(acc.acceleration)
            if ctrl.empty():
                time.sleep(.001)
            else:
                cmd, val = ctrl.get_nowait()
                if cmd == 'f':
                    acc.data_rate = DATA_RATE[val]
                elif cmd == 'a':
                    acc.range = RANGE[val]
                elif cmd == 'm':
                    acc.mode = MODE[val]
                else:
                    break
    except:
        x = 0
        dx = 2 * np.pi / 1920
        rng = np.random.default_rng()
        scale = 5
        noise = 1
        period = .001
        while run.value:
            x = x + dx
            if x > np.pi:
                x = x - 2 * np.pi
            s0 = 9 * scale * np.sin(x + 0 * np.pi / 3) + (rng.random() - .5) * noise * scale
            s1 = 9 * scale * np.sin(x + 2 * np.pi / 3) + (rng.random() - .5) * noise * scale
            s2 = 9 * scale * np.sin(x - 2 * np.pi / 3) + (rng.random() - .5) * noise * scale
            data.put((s0, s1, s2))
            if ctrl.empty():
                time.sleep(period)
            else:
                cmd, val = ctrl.get_nowait()
                if cmd == 'f':
                    period = [.5, .2, .1, .05, .02, .01, .005, .002, .001][val]
                elif cmd == 'a':
                    scale = [0.625, 1.25, 2.5, 5][val]
                elif cmd == 'm':
                    noise = [1, 2, .5][val]
                else:
                    print(f"This sucks {cmd} : {val}")
                    break


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

def btn_pos(row, col):
    x = 15 + col * (btn_x + 12)
    y = scope.size[1] + 5 + row * (btn_y + 5)
    return (x, y)

class Text (object):
    font = None

    def __init__(self, label):
        if self.font is None:
            # can only do this once pygame.font.init() has been called
            self.__class__.font = pygame.font.SysFont('notomono', 20)
        self.color = (0, 0, 0)
        self.label = label

    def _redraw(self):
        self.text = self.font.render(self.label, True, self.color)

    def set_color(self, color):
        self.color = color
        self._redraw()

    def set_text(self, label):
        self.label = label
        self._redraw()

class Label (Text):

    def __init__(self, label, pos, size=None):
        super().__init__(label)
        self.ena = True
        self.size = size
        self.set_text(label)
        self.rect = pygame.Rect(pos, self.size)

    def _redraw(self):
        text = self.font.render(self.label, True, self.color if self.ena else (100, 100, 100))

        if self.size is None:
            self.size = text.get_size()

        self.lbl = pygame.Surface(self.size)

        self.lbl.fill((200, 200, 200))
        dx = max(0, (self.lbl.get_width() - text.get_width()) // 2)
        dy = max(0, (self.lbl.get_height() - text.get_height()) // 2)
        self.lbl.blit(text, (dx, dy))

    def draw(self, surface):
        surface.blit(self.lbl, self.rect)

    def press(self, pos):
        pass

    def depress(self, pos):
        pass

    def enable(self, ena=True):
        if self.ena != ena:
            self.ena = ena
            self._redraw()

class PushButton (Text):

    StateEnabled = 0
    StateArmed = 1
    StateDisabled = 2

    def __init__(self, label, on_click, pos, size=None):
        super().__init__(label)

        self.on_click = on_click
        self.state = self.StateEnabled
        self.size = size
        self._redraw()
        self.rect = pygame.Rect(pos, self.size)

    def _redraw(self):
        color= [(0, 0, 0), (255, 255, 255), (100, 100, 100)][self.state]
        text = self.font.render(self.label, True, color)

        if self.size is None:
            self.size = text.get_size()
            self.size = (self.size[0] + 4, self.size[1] + 4)
        size = self.size

        self.btn = pygame.Surface(size)
        self.btn.fill((200, 200, 200))

        dx = (self.btn.get_width() - text.get_width()) // 2
        dy = (self.btn.get_height() - text.get_height()) // 2

        if self.state != self.StateDisabled:
            ghost = self.font.render(self.label, True, (255 - color[0], 255 - color[1], 255 - color[2]))
            self.btn.blit(ghost, (dx+1, dy+1))
            self.btn.blit(text, (dx-1, dy-1))
        else:
            self.btn.blit(text, (dx, dy))

        if self.state == self.StateEnabled:
            pygame.draw.lines(self.btn, (50, 50, 50), False, [(size[0]-1, 1), (size[0]-1, size[1]-1), (1, size[1] - 1)], 3)
            pygame.draw.lines(self.btn, (255, 255, 255), False, [(size[0]-1, 1), (1, 1), (1, size[1] - 1)], 3)

        if self.state == self.StateArmed:
            pygame.draw.lines(self.btn, (50, 50, 50), False, [(size[0]-1, 1), (1, 1), (1, size[1] - 1)], 3)
            pygame.draw.lines(self.btn, (255, 255, 255), False, [(size[0]-1, 1), (size[0]-1, size[1]-1), (1, size[1] - 1)], 3)

    def draw(self, surface):
        surface.blit(self.btn, self.rect)

    def press(self, pos):
        if self.state == self.StateEnabled and self.rect.collidepoint(pos):
            self.state = self.StateArmed
            self._redraw()

    def depress(self, pos):
        if self.state == self.StateArmed:
            self.state = self.StateEnabled
            self._redraw()
            if self.on_click and self.rect.collidepoint(pos):
                self.on_click(self)

    def enable(self, ena=True):
        self.state = self.StateEnabled if ena else self.StateDisabled
        self._redraw()

class Setting (object):

    def __init__(self, label, on_update, current, settings, pos, btn_size):
        self.btns = []
        self.btns.append(PushButton(f"{label} +", lambda b: self.setting_next(), btn_pos(pos[0]+0, pos[1]), btn_size))
        self.btns.append(PushButton(f"{label} -", lambda b: self.setting_prev(), btn_pos(pos[0]+2, pos[1]), btn_size))
        self.lbl = Label(current, btn_pos(pos[0]+1, pos[1]), btn_size)
        self.settings = settings
        self.index = self.settings.index(current)
        self.idx = self.index
        self.on_update = on_update
        self.update(False)

    def update(self, notify=True):
        self.btns[0].enable(self.index < (len(self.settings) - 1))
        self.btns[1].enable(self.index > 0)
        self.lbl.set_text(self.settings[self.index])
        if notify and self.on_update:
            self.on_update(self)

    def setting_next(self):
        self.index = min(self.index + 1, len(self.settings) - 1)
        self.update()

    def setting_prev(self):
        self.index = max(self.index - 1, 0)
        self.update()

    def setting_reset(self):
        self.index = self.idx
        self.update()

    def draw(self, surface):
        for btn in self.btns:
            btn.draw(surface)
        self.lbl.draw(surface)

    def press(self, pos):
        for btn in self.btns:
            btn.press(pos)

    def depress(self, pos):
        for btn in self.btns:
            btn.depress(pos)

    def enable(self, ena=True):
        for btn in self.btns:
            btn.enable(ena)
        self.lbl.enable(ena)

    def rect(self):
        return self.btns[0].rect.union(self.btns[1].rect)

class Scope (object):
    def __init__(self, xmax=1920, ymax=1080):
        setup_pygame()
        self.screen_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.size = (min(xmax, self.screen_size[0]), min(ymax, self.screen_size[1]))
        self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN)
        self.bg = pygame.Surface(self.size)
        self.setup_bg(self.bg)
        pygame.display.update()
        self.boundbox = pygame.Rect(0, 0, self.size[0], self.size[1])
        self.step = 1

    def setup_bg(self, bg):
        "Renders an empty graticule"
        xmin = 5
        xmax = self.size[0] - 5
        xsize = xmax - xmin
        x0 = self.size[0] // 2
        xline = xsize // 10
        xtick = xline // 5
        xline = xtick * 5
        xsize = xline * 10
        xmin = x0 - xsize // 2
        xmax = x0 + xsize // 2

        ymin = 30
        ymax = self.size[1]
        ysize = ymax - ymin
        y0 = self.size[1] // 2
        yline = ysize // 8
        ytick = yline // 5
        yline = ytick * 5
        ysize = yline * 8
        ymin = y0 - ysize // 2
        ymax = y0 + ysize // 2

        self.xlim = (xmin, xmax)
        self.ylim = (ymin, ymax)
        self.x0 = x0
        self.y0 = y0

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

    def rect(self):
        return self.boundbox

    def set_step(self, step):
        self.step = step

    def _draw(self, samples, step):
        count = (self.xlim[1] - self.xlim[0] + step - 1) // step
        scale = (self.ylim[1] - self.ylim[0]) * 0.01
        p0 = [(self.xlim[0] + i * step, self.y0 - int(scale * v[0])) for i, v in enumerate(samples[-count:])]
        p1 = [(self.xlim[0] + i * step, self.y0 - int(scale * v[1])) for i, v in enumerate(samples[-count:])]
        p2 = [(self.xlim[0] + i * step, self.y0 - int(scale * v[2])) for i, v in enumerate(samples[-count:])]
        #p3 = [(self.xlim[0] + i, self.y0) for i, v in enumerate(samples)]
        pygame.draw.lines(self.screen, (200, 200, 0), False, p0)
        pygame.draw.lines(self.screen, (0, 200, 0), False, p1)
        pygame.draw.lines(self.screen, (0, 200, 200), False, p2)
        #pygame.draw.lines(self.screen, (0, 0, 200), False, p3)

    def update(self, samples):
        self.screen.blit(self.bg, self.rect())
        self._draw(samples, self.step)

scope = Scope(1024, 470)

try:
    run = mp.Value('b', True)
    data = mp.Queue(0)
    ctrl = mp.Queue(0)

    proc = mp.Process(target=data_source, args=(data, ctrl, run))
    proc.start()

    font = pygame.font.Font(None, 30)
    title = font.render('Bibi rocks!', True, (255, 255, 255))
    title_pos = (15, 0)
    fps = font.render('fps:  0.00', True, (100, 100, 100))
    fps_pos = (scope.size[0] - fps.get_width() - 15, 0)
    status = font.render('pos:', True, (200, 200, 200))
    #status_pos = (15, scope.screen_size[1] - 1 - status.get_height())
    status_pos = (15, 600 - 1 - status.get_height())

    btn_x = 155
    btn_y = 30
    btn_size = (btn_x, btn_y)
    widgets = []
    widgets.append(Setting('Zoom', lambda s: scope.set_step(s.index + 1), '1', [f"{i+1}" for i in range(100)], (0, 0), btn_size))
    widgets.append(Setting('Mode', lambda s: ctrl.put(('m', s.index)), 'NORMAL', ['NORMAL', 'HIRES', 'LOWPO'], (0, 3), btn_size))
    widgets.append(Setting('Freq', lambda s: ctrl.put(('f', s.index)), '1620Hz', ['1Hz', '10Hz', '25Hz', '50Hz', '100Hz', '200Hz', '400Hz', '1344Hz', '1620Hz'], (0, 4), btn_size))
    widgets.append(Setting('Rnge', lambda s: ctrl.put(('a', s.index)), '16G', ['2G', '4G', '8G', '16G'], (0, 5), btn_size))
    #widgets[1].enable(False)
    zoom = widgets[0]


    pygame.display.update()

    sample_cnt = (scope.xlim[1] - scope.xlim[0])
    samples = [(0,0,0)] * sample_cnt

    update_cnt = 0
    begin = time.perf_counter_ns()
    update_ctrl = True
    while run.value:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == ord('q'):
                    run.value = False
                if event.key == ord('0'):
                    zoom.setting_reset()
                    update_ctrl = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                for widget in widgets:
                    widget.press(event.pos)
                update_ctrl = True
            if event.type == pygame.MOUSEBUTTONUP:
                for widget in widgets:
                    widget.depress(event.pos)
                update_ctrl = True

            if event.type == pygame.MOUSEMOTION:
                r0 = widgets[0].rect()
                r1 = widgets[-1].rect()
                s = f"pos: {widgets[0].rect().topleft} - {widgets[-1].rect().bottomright} + {status.get_height()}"
                status = font.render(s, True, (200, 200, 200), (0, 0, 0))

            if event.type == pygame.QUIT:
                run.value = False

        try:
            while True:
                samples.append(data.get_nowait())
        except queue.Empty:
            pass

        count = len(samples) - sample_cnt
        batch = font.render(f"batch: {count}", True, (157, 157, 157))
        if count > 0:
            samples = samples[-sample_cnt:]
            scope.update(samples)
            scope.screen.blit(title, title_pos)

        if update_cnt == 10:
            end = time.perf_counter_ns()
            fps = font.render(f"fps: {1e10/(end - begin):5.2f}", True, (0, 157, 0))
            update_cnt = 0
            begin = end
        else:
            update_cnt = update_cnt + 1

        scope.screen.blit(batch, (scope.x0, 0))
        scope.screen.blit(fps, fps_pos)
        scope.screen.blit(status, status_pos)

        if update_ctrl:
            for widget in widgets:
                widget.draw(scope.screen)
            update_ctrl = False

        pygame.display.update()
        time.sleep(.001)
finally:
    run.value = False
    pygame.quit()
    proc.join()
