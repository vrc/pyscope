import pygame

def btn_pos(offs, row, col, size):
    x = 15 + col * (size[0] + 12)
    y = offs + 5 + row * (size[1] + 5)
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
        print(f"set_text({label})")
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
        return surface.blit(self.lbl, self.rect)

    def press(self, pos):
        return False

    def depress(self, pos):
        return False

    def track(self, pos):
        return False

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
        return surface.blit(self.btn, self.rect)

    def press(self, pos):
        if self.state == self.StateEnabled and self.rect.collidepoint(pos):
            self.state = self.StateArmed
            self._redraw()
            return True
        return False

    def depress(self, pos):
        if self.state == self.StateArmed:
            self.state = self.StateEnabled
            self._redraw()
            if self.on_click and self.rect.collidepoint(pos):
                self.on_click(self)
            return True
        return False

    def track(self, pos):
        return False

    def enable(self, ena=True):
        self.state = self.StateEnabled if ena else self.StateDisabled
        self._redraw()

class Combobox (Label):
    StateDefault = 0
    StateArmed = 1
    StateArmedPost = 2

    def __init__(self, current, values, on_update, pos, size):
        self.index = values.index(current)
        self.values = values
        self.armed_state = self.StateDefault
        self.on_update = on_update
        super().__init__(f">{current}<", pos, size)
        self.armed_rect = pygame.Rect(self.rect.topleft,  (self.rect.width, self.font.get_linesize() * len(values)))

    def is_armed(self):
        return self.ena and self.armed_state == self.StateArmed

    def _redraw_armed(self):
        self.sel = pygame.Surface(self.armed_rect.size)
        self.sel.fill((200, 200, 200))

        h = self.font.get_linesize()
        w = self.armed_rect.width

        for i, v in enumerate(self.values):
            rect = pygame.Rect((0, i * h), (w, h))
            if i == self.armed_index:
                print(rect)
                self.sel.fill((100, 100, 100), rect)
                text = self.font.render(f">{v}<", True, (255, 255, 255))
            else:
                text = self.font.render(v, True, (0, 0, 0))
            dx = max(0, (w - text.get_width()) // 2)
            dy = max(0, (h - text.get_height()) // 2)
            self.sel.blit(text, (dx, dy + i * h))

    def draw(self, surface):
        if self.is_armed():
            return surface.blit(self.sel, self.armed_rect)
        surface.blit(self.lbl, self.rect)
        if self.armed_state == self.StateArmedPost:
            print(f"Update armed rect {self.armed_rect}")
            self.armed_state = self.StateDefault
            return self.armed_rect
        return self.rect

    def armed_cancel(self):
        if self.armed_state == self.StateArmed:
            self.armed_state = self.StateArmedPost
            self.set_text(f">{self.values[self.index]}<")

    def press(self, pos):
        if self.ena and self.armed_state == self.StateDefault and self.rect.collidepoint(pos):
            self.armed_state = self.StateArmed
            self.armed_index = self.index
            print(f"armed: {self.armed_index} {self.ena} {self.is_armed()}")
            self._redraw_armed()
            return True
        print(f"not armed: {self.ena}, {self.armed_state}, {self.rect.collidepoint(pos)}")
        return False

    def depress(self, pos):
        if self.is_armed():
            if self.armed_rect.collidepoint(pos):
                print(f"index : {self.index} -> {self.armed_index}")
                self.index = self.armed_index
                if self.on_update:
                    self.on_update(self)
            self.armed_cancel()
            return True
        return False

    def track(self, pos):
        if self.is_armed():
            if self.armed_rect.collidepoint(pos):
                self.armed_index = min(len(self.values) - 1, (pos[1] - self.armed_rect.top) // self.font.get_linesize())
                print(f"armed_index : {self.armed_index}")
                self._redraw_armed()
            else:
                self.armed_cancel()
            return True
        return False

class Setting (object):

    def __init__(self, label, on_update, current, settings, pos, btn_offs, btn_size):
        self.btns = []
        self.btns.append(PushButton(f"{label} +", lambda b: self.setting_next(), btn_pos(btn_offs, pos[0]+0, pos[1], btn_size), btn_size))
        self.btns.append(PushButton(f"{label} -", lambda b: self.setting_prev(), btn_pos(btn_offs, pos[0]+2, pos[1], btn_size), btn_size))
        self.lbl = Label(current, btn_pos(btn_offs, pos[0]+1, pos[1], btn_size), btn_size)
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
        return self.rect()

    def press(self, pos):
        u = False
        for btn in self.btns:
            u |= btn.press(pos)
        return u

    def depress(self, pos):
        u = False
        for btn in self.btns:
            u |= btn.depress(pos)
        return u

    def track(self, pos):
        u = False
        for btn in self.btns:
            u |= btn.track(pos)
        return u

    def enable(self, ena=True):
        for btn in self.btns:
            btn.enable(ena)
        self.lbl.enable(ena)

    def rect(self):
        return self.btns[0].rect.union(self.btns[1].rect)
