#!/usr/bin/python3

import graph
import multiprocessing as mp
import numpy as np
import os
import pygame
import queue
import random
import time
import widget


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

def _setup_pygame(size=None):
    pygame.display.init()
    pygame.font.init()
    pygame.init()

    if size is None:
        screen_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        return (pygame.display.set_mode(screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF), screen_size)
    return (pygame.display.set_mode(size, pygame.DOUBLEBUF), size)

def setup_pygame(xSize):
    disp_no = os.getenv('DISPLAY')
    if disp_no and not os.getenv('SSH_CONNECTION'):
        print('Using X11 driver')
        return _setup_pygame(xSize)
    else:
        for fp in ['fbcon', 'directfb', 'svgalib']:
            os.putenv('SDL_VIDEODRIVER', fp)
            print(f"Attempting {fp}")
            try:
                return _setup_pygame()
            except pygame.error:
                pass
    raise Exception('setup_pygame failed')


screen, screen_size = setup_pygame((1024, 600))
scope = graph.Scope(min(1024, screen_size[0]), min(470, screen_size[1]))

mouse_position = lambda event: event.pos
mouse_device = None
try:
    import evdev

    for dev in [evdev.InputDevice(nam) for nam in evdev.list_devices()]:
        if 'ByQDtech' in dev.name:
            # that's what you get from buying a cheap display
            pygame.mouse.set_visible(False)
            mouse_position = lambda e: (dev.absinfo(0).value, dev.absinfo(1).value)
            mouse_device = dev
            break
        dev.close()
except:
    pass

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
    #status_pos = (15, screen_size[1] - 1 - status.get_height())
    status_pos = (15, 600 - 1 - status.get_height())

    btn_x = 155
    btn_y = 30
    btn_size = (btn_x, btn_y)
    btn_offs = scope.rect().bottom
    widgets = []
    widgets.append(widget.Setting('Zoom', lambda s: scope.set_step(s.index + 1), '1', [f"{i+1}" for i in range(100)], (0, 0), btn_offs, btn_size))
    widgets.append(widget.Combobox('NORMAL', ['NORMAL', 'HIRES', 'LOWPO'], lambda s: ctrl.put(('m', s.index)), widget.btn_pos(btn_offs, 0, 3, btn_size), btn_size))
    widgets.append(widget.Setting('Freq', lambda s: ctrl.put(('f', s.index)), '1620Hz', ['1Hz', '10Hz', '25Hz', '50Hz', '100Hz', '200Hz', '400Hz', '1344Hz', '1620Hz'], (0, 4), btn_offs, btn_size))
    widgets.append(widget.Setting('Rnge', lambda s: ctrl.put(('a', s.index)), '16G', ['2G', '4G', '8G', '16G'], (0, 5), btn_offs, btn_size))
    #widgets[1].enable(False)
    zoom = widgets[0]

    pygame.display.update()

    sample_cnt = (scope.xlim[1] - scope.xlim[0])
    samples = [(0,0,0)] * sample_cnt

    update_cnt = 0
    begin = time.perf_counter_ns()
    while run.value:
        focus_widget = None
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == ord('q'):
                    run.value = False
                if event.key == ord('0'):
                    zoom.setting_reset()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                for widget in widgets:
                    if widget.press(mouse_position(event)):
                        focus_widget = widget
                continue

            if event.type == pygame.MOUSEBUTTONUP:
                for widget in widgets:
                    if widget.depress(mouse_position(event)):
                        focus_widget = widget
                continue

            if event.type == pygame.MOUSEMOTION:
                for widget in widgets:
                    if widget.track(mouse_position(event)):
                        focus_widget = widget
                continue

            if event.type == pygame.QUIT:
                run.value = False

        try:
            while True:
                samples.append(data.get_nowait())
        except queue.Empty:
            pass

        screen.fill((0, 0, 0))

        count = len(samples) - sample_cnt
        batch = font.render(f"batch: {count}", True, (157, 157, 157))
        if count > 0:
            samples = samples[-sample_cnt:]
            scope.draw(screen, samples)
            screen.blit(title, title_pos)

        if update_cnt == 10:
            end = time.perf_counter_ns()
            fps = font.render(f"fps: {1e10/(end - begin):5.2f}", True, (250, 250, 0))
            update_cnt = 0
            begin = end
        else:
            update_cnt = update_cnt + 1

        screen.blit(batch, (scope.x0, 0))
        screen.blit(fps, fps_pos)
        screen.blit(status, status_pos)

        for widget in widgets:
            if widget != focus_widget:
                widget.draw(screen)
        if focus_widget:
            focus_widget.draw(screen)

        pygame.display.flip()
        time.sleep(.001)
finally:
    if mouse_device:
        mouse_device.close()
    run.value = False
    pygame.quit()
    proc.join()

if False:
    print('scope:')
    print(f"   screen_size : {screen_size}")
    print(f"          size : {scope.size}")
    print(f"      boundbox : {scope.boundbox}")
    print(f"            x0 : {scope.x0}")
    print(f"          xlim : {scope.xlim}")
    print(f"            y0 : {scope.y0}")
    print(f"          ylim : {scope.ylim}")
